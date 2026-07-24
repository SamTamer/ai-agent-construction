from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import sys
import os
import time
from collections import defaultdict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent.rag_pipeline import RAGPipeline

app = FastAPI(title="Construction Safety AI Agent")
pipeline = RAGPipeline()

# Simple in-memory rate limiter
request_counts = defaultdict(list)
RATE_LIMIT = 10  # max requests
WINDOW_SECS = 60  # per minute


def is_rate_limited(ip: str) -> bool:
    now = time.time()
    # Keep only requests within the last 60 seconds
    request_counts[ip] = [t for t in request_counts[ip] if now - t < WINDOW_SECS]
    if len(request_counts[ip]) >= RATE_LIMIT:
        return True
    request_counts[ip].append(now)
    return False


import re

# Prompt injection patterns — phrases that attempt to override the system prompt
INJECTION_PATTERNS = [
    r"ignore\s+(previous|prior|above|all)\s+(instructions?|rules?|prompts?|context)",
    r"forget\s+(previous|prior|above|all|your)\s*(instructions?|rules?|prompts?|context)?",
    r"you\s+are\s+now\s+(a\s+)?(?!a\s+construction)",  # "you are now a [different persona]"
    r"disregard\s+(all|previous|prior|your)\s*(instructions?|rules?|prompts?)?",
    r"do\s+not\s+follow\s+(your\s+)?(instructions?|rules?|guidelines?)",
    r"override\s+(your\s+)?(instructions?|rules?|system|prompt)",
    r"new\s+instructions?:",
    r"system\s*:\s*you",       # injected system role
    r"assistant\s*:\s*sure",   # pre-filling assistant response
    r"<\s*/?system\s*>",       # XML-style role injection
    r"###\s*(system|instruction|prompt)",  # markdown role injection
]

INJECTION_REGEX = re.compile("|".join(INJECTION_PATTERNS), re.IGNORECASE)


def detect_injection(text: str) -> bool:
    """Return True if the text contains a suspected prompt injection attempt."""
    return bool(INJECTION_REGEX.search(text))


class HistoryTurn(BaseModel):
    role: str    # "user" or "assistant"
    content: str


class QuestionRequest(BaseModel):
    question: str
    history: list[HistoryTurn] = []


class AnswerResponse(BaseModel):
    question: str
    response: str
    sources: list
    answered: bool


@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Construction Safety Agent is running"}


@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest, req: Request):
    # Rate limiting
    client_ip = req.client.host
    if is_rate_limited(client_ip):
        raise HTTPException(
            status_code=429, detail="Too many requests. Please wait a moment."
        )

    # Input validation
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    if len(request.question) > 500:
        raise HTTPException(
            status_code=400, detail="Question must be under 500 characters"
        )

    # Prompt injection detection
    if detect_injection(request.question):
        raise HTTPException(
            status_code=400,
            detail="Invalid input. Please ask a construction safety question.",
        )

    history = [{"role": t.role, "content": t.content} for t in request.history]
    result = pipeline.ask(request.question, history=history)
    return result
