import os
import json
import time
from pathlib import Path
from typing import List, Optional, Literal

import google.generativeai as genai
from groq import Groq

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from agent.tools.lakehouse_query import (
    LAKEHOUSE_QUERY_TOOL,
    SYSTEM_PROMPT,
    execute_query,
)
from agent.tools.time_travel import TIME_TRAVEL_TOOL, execute_time_travel_query
from agent.tools.explain_query import EXPLAIN_TOOL, explain_plan
from agent.tools.commit_conflict import CONFLICT_TOOL, get_conflicts
from agent.tools.audit_query import AUDIT_TOOL, execute_audit_query
from agent.audit import log_interaction
from agent.memory import get_history, save_history
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
    },
    {
    "type": "function",
    "function": {
        "name": "run_audit_query",
        "description": "Query the audit_log table to see past user interactions, questions asked, SQL generated, and answers given.",
        "parameters": {
            "type": "object",
            "properties": {
                "sql": {"type": "string", "description": "SQL query against nessie.retail.audit_log"}
            },
            "required": ["sql"]
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
    session_id: str = "default"
    as_of_date: Optional[str] = None  # optional time-travel pin
    user_role: str = "analyst"  # for column-level masking via OPA
    model: str = "gemini-2.5-flash"  # default model

def get_gemini_model(model_name: str):
    """Get a configured Gemini model."""
    return genai.GenerativeModel(
        model_name=model_name,
        system_instruction=SYSTEM_PROMPT,
        tools=[LAKEHOUSE_QUERY_TOOL, TIME_TRAVEL_TOOL, EXPLAIN_TOOL, CONFLICT_TOOL, AUDIT_TOOL],
    )


@app.get("/health")
def health() -> dict[str, str]:
    """Basic liveness check for the backend."""
    return {"status": "ok"}


@app.get("/logs")
def get_logs(lines: int = 500) -> PlainTextResponse:
    """Return the last N lines of server.log."""
    log_path = Path(__file__).resolve().parent.parent / "logs" / "server.log"
    if not log_path.exists():
        return PlainTextResponse("No log file found.", status_code=404)
    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
        all_lines = f.readlines()
    tail = all_lines[-lines:]
    return PlainTextResponse("".join(tail))


def _role(m) -> str:
    return m.role if isinstance(m, Message) else m["role"]

def _content(m) -> str:
    return m.content if isinstance(m, Message) else m["content"]

def to_gemini_history(messages) -> list[dict]:
    """Convert Message list or dicts into Gemini's chat history format."""
    role_map = {"user": "user", "assistant": "model"}
    return [
        {"role": role_map.get(_role(m), "user"), "parts": [_content(m)]}
        for m in messages
    ]


def to_groq_history(messages) -> list[dict]:
    """Convert Message list or dicts into Groq/OpenAI chat history format."""
    return [
        {"role": _role(m), "content": _content(m)}
        for m in messages
    ]


def run_tool(name: str, args: dict, user_role: str = "analyst") -> dict:
    """Dispatch a Gemini function call to the matching tool executor.

    Adding a new tool later just means adding another branch here plus
    including its declaration in the model's tools list above.
    """
    log_event("tool_call", {"tool": name, "arguments": args})

    if name == "run_lakehouse_query":
        result = execute_query(args["sql"], user_role=user_role)
    elif name == "run_time_travel_query":
        result = execute_time_travel_query(
            sql=args["sql"],
            as_of_date=args.get("as_of_date"),
            snapshot_id=args.get("snapshot_id"),
        )
    elif name == "explain_query_plan":
        result = explain_plan(args["sql"])

    elif name == "run_audit_query":
        result = execute_audit_query(args["sql"])
    
    elif name == "get_commit_conflicts":
        result = get_conflicts()
    else:
        result = {"error": f"Unknown tool: {name}"}

    log_event("tool_result", {"tool": name, "result": result})
    return result


async def chat_gemini(req: ChatRequest, model_name: str) -> dict[str, str]:
    """Handle chat using Gemini."""
    model = get_gemini_model(model_name)

    # Merge stored history with incoming messages
    stored = get_history(req.session_id)
    incoming = [{"role": m.role, "content": m.content} for m in req.messages]
    full_messages = stored + incoming

    history = to_gemini_history(full_messages[:-1])
    chat_session = model.start_chat(history=history)

    latest_message = full_messages[-1]["content"]
    response = chat_session.send_message(latest_message)

    last_sql = None
    last_snapshot_id = None

    while True:
        function_call = None
        for part in response.candidates[0].content.parts:
            if part.function_call:
                function_call = part.function_call
                break

        if function_call is None:
            break

        args = dict(function_call.args)
        result = run_tool(function_call.name, args, user_role=req.user_role)

        if function_call.name == "run_lakehouse_query":
            last_sql = args.get("sql")
        elif function_call.name == "run_time_travel_query":
            last_sql = args.get("sql")
            last_snapshot_id = args.get("snapshot_id")

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

    save_history(req.session_id, full_messages + [{"role": "assistant", "content": response.text}])

    log_interaction(
        user_role=req.user_role,
        model=req.model,
        question=req.messages[-1].content,
        sql=last_sql,
        snapshot_id=last_snapshot_id,
        execution_time_ms=None,
        answer=response.text,
    )
    return {"role": "assistant", "content": response.text}


async def chat_groq(req: ChatRequest, model_name: str) -> dict[str, str]:
    """Handle chat using Groq."""
    # Merge stored history with incoming messages
    stored = get_history(req.session_id)
    incoming = [{"role": m.role, "content": m.content} for m in req.messages]
    full_messages = stored + incoming

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + [
        {"role": m["role"], "content": m["content"]} for m in full_messages
    ]
    
    response = groq_client.chat.completions.create(
        model=model_name,
        messages=messages,
        tools=GROQ_TOOLS,
        temperature=0.7,
    )

    last_sql = None
    last_snapshot_id = None

    # Handle function calling loop
    while True:
        message = response.choices[0].message
        
        # If no tool call, return the response
        if not message.tool_calls:
            save_history(req.session_id, full_messages + [{"role": "assistant", "content": message.content or ""}])
            log_interaction(
                user_role=req.user_role,
                model=req.model,
                question=req.messages[-1].content,
                sql=last_sql,
                snapshot_id=last_snapshot_id,
                execution_time_ms=None,
                answer=message.content or "",
            )
            return {"role": "assistant", "content": message.content or ""}
        
        # Execute tool calls
        tool_call = message.tool_calls[0]
        args = json.loads(tool_call.function.arguments)
        result = run_tool(tool_call.function.name, args, user_role=req.user_role)

        if tool_call.function.name == "run_lakehouse_query":
            last_sql = args.get("sql")
        elif tool_call.function.name == "run_time_travel_query":
            last_sql = args.get("sql")
            last_snapshot_id = args.get("snapshot_id")
        
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
