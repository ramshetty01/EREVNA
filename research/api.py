"""Local-first API. Explicit token required unless local-only mode is enabled."""

import hmac
import os
import threading
from typing import Annotated, Literal

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from research.llm_io import BudgetExceeded
from research.models import Document, ResearchResult
from research.pipeline import ResearchError, run_research

app = FastAPI(title="EREVNA Research API", version="0.4.0")
slots = threading.BoundedSemaphore(2)


class ResearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1500)
    documents: list[Document] | None = Field(default=None, max_length=12)
    retrieval: Literal["bm25", "dense", "hybrid"] = "bm25"
    k: int = Field(default=8, ge=1, le=12)
    verify_support: bool = True
    max_llm_calls: int | None = Field(default=None, ge=1, le=10, strict=True)


@app.middleware("http")
async def limit_body(request: Request, call_next):
    if request.method == "POST":
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > 400_000:
                return JSONResponse(
                    status_code=413, content={"detail": "Request body is too large."}
                )
        request._body = bytes(body)
    return await call_next(request)


@app.get("/health")
def health():
    return {"status": "ok", "version": "0.4.0"}


@app.post("/research", response_model=ResearchResult)
def research(request: ResearchRequest, authorization: Annotated[str | None, Header()] = None):
    token = os.getenv("EREVNA_API_TOKEN", "")
    local = os.getenv("EREVNA_API_LOCAL") == "1"
    if token:
        if not hmac.compare_digest(authorization or "", "Bearer " + token):
            raise HTTPException(401, "Valid bearer token required.")
    elif not local:
        raise HTTPException(503, "Configure EREVNA_API_TOKEN or enable localhost-only mode.")
    if not slots.acquire(blocking=False):
        raise HTTPException(
            429, "Two runs are already active. Retry shortly.", headers={"Retry-After": "5"}
        )
    try:
        return run_research(
            request.query,
            documents=request.documents,
            retrieval=request.retrieval,
            k=request.k,
            verify_support=request.verify_support,
            max_llm_calls=request.max_llm_calls,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from None
    except BudgetExceeded as exc:
        raise HTTPException(422, str(exc)) from None
    except ResearchError as exc:
        raise HTTPException(502, str(exc)) from None
    finally:
        slots.release()
