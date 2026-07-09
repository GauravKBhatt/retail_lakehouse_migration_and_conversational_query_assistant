import os
from typing import List, Optional

import google.generativeai as genai
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

app = FastAPI(title="Retail Lakehouse Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=SYSTEM_PROMPT,
    tools=[LAKEHOUSE_QUERY_TOOL, TIME_TRAVEL_TOOL, EXPLAIN_TOOL],
)


class Message(BaseModel):
    """A single chat turn, either from the user or the assistant."""

    role: str  # 'user' or 'assistant'
    content: str


class ChatRequest(BaseModel):
    """Payload sent by the frontend when the user submits a chat message."""

    messages: List[Message]
    as_of_date: Optional[str] = None  # optional time-travel pin


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


def run_tool(name: str, args: dict) -> dict:
    """Dispatch a Gemini function call to the matching tool executor.

    Adding a new tool later just means adding another branch here plus
    including its declaration in the model's tools list above.
    """
    if name == "run_lakehouse_query":
        return execute_query(args["sql"])

    if name == "run_time_travel_query":
        return execute_time_travel_query(
            sql=args["sql"],
            as_of_date=args.get("as_of_date"),
            snapshot_id=args.get("snapshot_id"),
        )

    if name == "explain_query_plan":
        return explain_plan(args["sql"])

    return {"error": f"Unknown tool: {name}"}


@app.post("/chat")
async def chat(req: ChatRequest) -> dict[str, str]:
    """Run the user's message through Gemini, executing whichever tool
    the model calls (lakehouse query or time travel query) until it
    returns a final plain text answer.
    """
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