import logging
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from . import db, llm
from .config import settings

log = logging.getLogger("chatbot")

@asynccontextmanager
async def lifespan(_: FastAPI):
    db.init_db()
    llm.setup_cache()
    yield

app = FastAPI(title="Lyftr Relay", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.origins, allow_methods=["*"], allow_headers=["*"])

class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=128)
    message: str = Field(min_length=1, max_length=4000)
    system_prompt: str | None = Field(default=None, max_length=8000)

    @field_validator("message", mode="before")
    @classmethod
    def _strip(cls, v):
        return v.strip() if isinstance(v, str) else v

    @field_validator("system_prompt", mode="after")
    @classmethod
    def _blank_to_none(cls, v):
        return (v.strip() or None) if v else None

@app.get("/health")
async def health():
    ok = await run_in_threadpool(db.ping)
    if not ok:
        raise HTTPException(503, "database unavailable")
    if not settings.keys:
        raise HTTPException(503, "LLM_API_KEYS is not configured")
    return {"status": "ok", "keys_configured": len(settings.keys), "cache_enabled": llm.litellm.cache is not None}

@app.post("/chat")
async def chat(req: ChatRequest, request: Request):
    t0 = time.perf_counter()
    simulate = llm.parse_simulation(request.headers.get("x-simulate-failure")) if settings.simulate else {}
    past = await run_in_threadpool(db.history, req.session_id)
    stored = await run_in_threadpool(db.get_system_prompt, req.session_id)
    system = req.system_prompt or stored or settings.default_system
    messages = [{"role": "system", "content": system}]
    messages += [{"role": m["role"], "content": m["content"]} for m in past]
    messages.append({"role": "user", "content": req.message})

    r = await llm.complete(messages, simulate)  # AllProvidersFailed -> 503 handler below
    meta = {
        "resolution_source": "LLM_CACHE" if r["cache_hit"] else "LIVE_INFERENCE",
        "model": r["model"], "latency_ms": max(0, int((time.perf_counter() - t0) * 1000)),
        "input_tokens": r["input_tokens"], "output_tokens": r["output_tokens"],
        "key_id": r["key_id"], "fallback_attempts": r["fallback_attempts"], "attempts": r["attempts"],
    }
    await run_in_threadpool(db.save_turn, req.session_id, req.system_prompt, req.message, r["reply"], meta)
    return {"session_id": req.session_id, "reply": r["reply"], "metadata": meta}

@app.get("/sessions/{session_id}/messages")
async def session_messages(session_id: str):
    msgs = await run_in_threadpool(db.history, session_id)
    if not msgs:
        raise HTTPException(404, "session not found")
    return {"session_id": session_id, "messages": msgs}

@app.exception_handler(llm.AllProvidersFailed)
async def _all_failed(_: Request, exc: llm.AllProvidersFailed):
    return JSONResponse({"detail": "all providers unavailable"}, status_code=503)

@app.exception_handler(Exception)
async def _unhandled(_: Request, exc: Exception):
    log.exception("unhandled error")
    return JSONResponse({"detail": "internal server error"}, status_code=500)
