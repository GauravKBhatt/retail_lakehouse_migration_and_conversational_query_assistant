from typing import List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Retail Lakehouse Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
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


@app.post("/chat")
async def chat(req: ChatRequest) -> dict[str, str]:
    """Placeholder chat endpoint.

    Real agent logic (query planning, Gemini calls, Iceberg querying)
    is not wired up yet — this just proves the request/response shape
    the frontend will rely on.
    """
    return {"role": "assistant", "content": "Placeholder — agent coming in Task 9"}