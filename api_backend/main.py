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
    tools=[LAKEHOUSE_QUERY_TOOL],
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


@app.post("/chat")
async def chat(req: ChatRequest) -> dict[str, str]:
    """Run the user's message through Gemini, executing the lakehouse
    query tool if the model asks for it, and returning the final answer.
    """
    history = to_gemini_history(req.messages[:-1])
    chat_session = model.start_chat(history=history)

    latest_message = req.messages[-1].content
    response = chat_session.send_message(latest_message)

    # Handle tool use loop: keep executing tool calls until Gemini
    # returns a plain text answer instead of another function_call.
    while True:
        function_call = None
        for part in response.candidates[0].content.parts:
            if part.function_call:
                function_call = part.function_call
                break

        if function_call is None:
            break

        sql = function_call.args["sql"]
        result = execute_query(sql)

        response = chat_session.send_message(
            genai.protos.Content(
                parts=[
                    genai.protos.Part(
                        function_response=genai.protos.FunctionResponse(
                            name="run_lakehouse_query",
                            response={"result": result},
                        )
                    )
                ]
            )
        )

    return {"role": "assistant", "content": response.text}