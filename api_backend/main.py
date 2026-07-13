import os
import json
from typing import List, Optional, Literal

# importing all the model providers.
import google.generativeai as genai
from groq import Groq

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent.tools.lakehouse_query import (
    LAKEHOUSE_QUERY_TOOL,
    SYSTEM_PROMPT,
    execute_query,
)
from agent.tools.time_travel import TIME_TRAVEL_TOOL, execute_time_travel_query
from agent.tools.explain_query import EXPLAIN_TOOL, explain_plan
from agent.tools.commit_conflict import CONFLICT_TOOL, get_conflicts
from api_backend.logger import log_event

# Model configuration
MODELS = {
    "gemini-2.5-flash": {"provider": "gemini", "name": "gemini-2.5-flash"},
    "gemini-1.5-pro": {"provider": "gemini", "name": "gemini-1.5-pro"},
    "meta-llama/llama-4-scout-17b-16e-instruct": {"provider": "groq", "name": "meta-llama/llama-4-scout-17b-16e-instruct"},
    "qwen/qwen3-32b": {"provider": "groq", "name": "qwen/qwen3-32b"},
    "openai/gpt-oss-20b": {"provider": "groq", "name": "openai/gpt-oss-20b"},
    "qwen/qwen3.6-27b": {"provider": "groq", "name": "qwen/qwen3.6-27b"},
    "groq/gpt-oss-120b": {"provider": "groq", "name": "openai/gpt-oss-120b"}
}

# Groq tool definitions (OpenAI-compatible format)
GROQ_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_lakehouse_query",
            "description": "Execute SQL queries against the retail lakehouse",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {"type": "string", "description": "SQL query to execute"}
                },
                "required": ["sql"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_time_travel_query",
            "description": "Execute time travel queries to see historical data",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {"type": "string", "description": "SQL query to execute"},
                    "as_of_date": {"type": "string", "description": "Date for time travel (YYYY-MM-DD format)"},
                    "snapshot_id": {"type": "string", "description": "Snapshot ID for time travel"}
                },
                "required": ["sql"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "explain_query_plan",
            "description": "Get a plain-English explanation of how a query will execute",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {"type": "string", "description": "The SQL query to explain"}
                },
                "required": ["sql"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_commit_conflicts",
            "description": "Retrieve recent Iceberg commit conflicts. Use this when the user asks why a write job failed or mentions commit errors.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]

app = FastAPI(title="Retail Lakehouse Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize clients
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


class Message(BaseModel):
    """A single chat turn, either from the user or the assistant."""

    role: str  # 'user' or 'assistant'
    content: str


class ChatRequest(BaseModel):
    """Payload sent by the frontend when the user submits a chat message."""

    messages: List[Message]
    as_of_date: Optional[str] = None  # optional time-travel pin
    model: str = "gemini-2.5-flash"  # default model

def get_gemini_model(model_name: str):
    """Get a configured Gemini model."""
    return genai.GenerativeModel(
        model_name=model_name,
        system_instruction=SYSTEM_PROMPT,
        tools=[LAKEHOUSE_QUERY_TOOL, TIME_TRAVEL_TOOL, EXPLAIN_TOOL,CONFLICT_TOOL],
    )


@app.get("/health")
def health() -> dict[str, str]:
    """Basic liveness check for the backend."""
    return {"status": "ok"}


def to_gemini_history(messages: List[Message]) -> List[dict]:
    """Convert our Message list into Gemini's chat history format.

    Gemini uses 'model' instead of 'assistant' for the AI role, and wraps
    text in a parts list rather than a plain string.
    """
    role_map = {"user": "user", "assistant": "model"}
    return [
        {"role": role_map.get(m.role, "user"), "parts": [m.content]}
        for m in messages
    ]


def to_groq_history(messages: List[Message]) -> List[dict]:
    """Convert our Message list into Groq/OpenAI chat history format."""
    return [
        {"role": m.role, "content": m.content}
        for m in messages
    ]


def run_tool(name: str, args: dict) -> dict:
    """Dispatch a Gemini function call to the matching tool executor.

    Adding a new tool later just means adding another branch here plus
    including its declaration in the model's tools list above.
    """
    log_event("tool_call", {"tool": name, "arguments": args})

    if name == "run_lakehouse_query":
        result = execute_query(args["sql"])
    elif name == "run_time_travel_query":
        result = execute_time_travel_query(
            sql=args["sql"],
            as_of_date=args.get("as_of_date"),
            snapshot_id=args.get("snapshot_id"),
        )
    elif name == "explain_query_plan":
        result = explain_plan(args["sql"])
    
    elif name == "get_commit_conflicts":
        result = get_conflicts()
    else:
        result = {"error": f"Unknown tool: {name}"}

    log_event("tool_result", {"tool": name, "result": result})
    return result


async def chat_gemini(req: ChatRequest, model_name: str) -> dict[str, str]:
    """Handle chat using Gemini."""
    model = get_gemini_model(model_name)
    history = to_gemini_history(req.messages[:-1])
    chat_session = model.start_chat(history=history)

    latest_message = req.messages[-1].content
    response = chat_session.send_message(latest_message)

    while True:
        function_call = None
        for part in response.candidates[0].content.parts:
            if part.function_call:
                function_call = part.function_call
                break

        if function_call is None:
            break

        result = run_tool(function_call.name, dict(function_call.args))

        response = chat_session.send_message(
            genai.protos.Content(
                parts=[
                    genai.protos.Part(
                        function_response=genai.protos.FunctionResponse(
                            name=function_call.name,
                            response={"result": result},
                        )
                    )
                ]
            )
        )

    return {"role": "assistant", "content": response.text}


async def chat_groq(req: ChatRequest, model_name: str) -> dict[str, str]:
    """Handle chat using Groq."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + to_groq_history(req.messages)
    
    response = groq_client.chat.completions.create(
        model=model_name,
        messages=messages,
        tools=GROQ_TOOLS,
        temperature=0.7,
    )

    # Handle function calling loop
    while True:
        message = response.choices[0].message
        
        # If no tool call, return the response
        if not message.tool_calls:
            return {"role": "assistant", "content": message.content or ""}
        
        # Execute tool calls
        tool_call = message.tool_calls[0]
        result = run_tool(tool_call.function.name, json.loads(tool_call.function.arguments))
        
        # Add assistant message and tool response to history
        messages.append({"role": "assistant", "content": message.content or "", "tool_calls": [tool_call]})
        messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": str(result)})
        
        # Get next response
        response = groq_client.chat.completions.create(
            model=model_name,
            messages=messages,
            tools=GROQ_TOOLS,
            temperature=0.7,
        )


@app.post("/chat")
async def chat(req: ChatRequest) -> dict[str, str]:
    """Route chat request to appropriate provider based on model selection."""
    log_event("chat_request", {
        "model": req.model,
        "messages": [m.model_dump() for m in req.messages],
    })
    
    config = MODELS.get(req.model, MODELS["gemini-2.5-flash"])
    
    if config["provider"] == "gemini":
        return await chat_gemini(req, config["name"])
    elif config["provider"] == "groq":
        return await chat_groq(req, config["name"])
    else:
        raise ValueError(f"Unknown provider: {config['provider']}")