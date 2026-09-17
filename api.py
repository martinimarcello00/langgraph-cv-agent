import os
import json
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv
from usage_utils import budget
import uvicorn
import gradio as gr
from agent import graph
from suggestions import suggestions_for
import asyncio

# Load env vars
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RECONCILE_INTERVAL_SECONDS = float(os.getenv("USAGE_RECONCILE_INTERVAL", "300"))
BUDGET_MESSAGE = (
    "I'm currently overwhelmed with fame (and API token limits). "
    "I'm too busy right now, try again tomorrow!"
)
GENERIC_ERROR_MESSAGE = "Something went wrong on my side. Please try again."

_reconcile_task: asyncio.Task | None = None


def _ensure_reconcile_task() -> None:
    """Start the background usage reconciler, and restart it if it ever dies.

    Not a FastAPI lifespan hook because mounting Gradio replaces the app lifespan.
    """
    global _reconcile_task
    if _reconcile_task is None or _reconcile_task.done():
        _reconcile_task = asyncio.create_task(budget.run_periodic(RECONCILE_INTERVAL_SECONDS))


def _sse(payload: dict) -> str:
    """JSON-encode every event: raw markdown contains newlines, which break SSE framing."""
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _text_of(content) -> str:
    """Flatten the content blocks the reasoning models may return instead of a plain string."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    return ""


# Setup Limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Marcello's Personal Bot")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:8001",
        "http://127.0.0.1:8001",
        "http://localhost:8002",
        "http://127.0.0.1:8002",
        "https://marcellomartini.tech",
        "https://www.marcellomartini.tech"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "tokens_used_today": budget.total_tokens,
        "daily_token_limit": budget.daily_limit,
    }

class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default"

@app.post("/chat")
@limiter.limit("5/minute")
async def chat(request: Request, chat_request: ChatRequest):
    _ensure_reconcile_task()

    # In-memory comparison, so no network call sits on the request path.
    if budget.exceeded():
        logger.warning("Daily token limit exceeded!")
        return {"response": BUDGET_MESSAGE}

    try:
        inputs = {"messages": [("user", chat_request.message)]}
        config = {"configurable": {"thread_id": chat_request.thread_id}, "run_name": "CV Agent"}
        
        # Run graph with persistence
        result = await graph.ainvoke(inputs, config=config)
        
        # Extract last message
        last_msg = result["messages"][-1]
        answer = _text_of(last_msg.content)
        return {"response": answer, "suggestions": suggestions_for(answer)}
        
    except Exception as e:
        logger.error(f"Error processing chat request: {e}", exc_info=True)
        if "RESOURCE_EXHAUSTED" in str(e):
            raise HTTPException(status_code=429, detail="ops., too many people are asking infos about me! Try later")
        raise HTTPException(status_code=500, detail=GENERIC_ERROR_MESSAGE)


@app.post("/chat/stream")
@limiter.limit("10/minute")
async def chat_stream(request: Request, chat_request: ChatRequest):
    """
    Streaming chat endpoint for faster perceived response times.
    Emits JSON-encoded SSE events: token, tool, error, done.
    """
    _ensure_reconcile_task()

    async def generate():
        if budget.exceeded():
            logger.warning("Daily token limit exceeded!")
            yield _sse({"type": "token", "v": BUDGET_MESSAGE})
            yield _sse({"type": "done"})
            return

        try:
            inputs = {"messages": [("user", chat_request.message)]}
            config = {
                "configurable": {"thread_id": chat_request.thread_id},
                "run_name": "CV Agent Streaming"
            }

            # "messages" yields LLM tokens, "updates" yields node results.
            answer = ""
            async for mode, payload in graph.astream(
                inputs, config=config, stream_mode=["messages", "updates"]
            ):
                if mode == "messages":
                    chunk, metadata = payload
                    # Skip the tools node, whose chunks are tool-call arguments.
                    if metadata.get("langgraph_node") != "agent":
                        continue
                    text = _text_of(chunk.content)
                    if text:
                        answer += text
                        yield _sse({"type": "token", "v": text})
                elif mode == "updates" and "tools" in payload:
                    for message in payload["tools"].get("messages", []):
                        name = getattr(message, "name", None)
                        if name:
                            yield _sse({"type": "tool", "v": name})

            cards = suggestions_for(answer)
            if cards:
                yield _sse({"type": "suggestions", "v": cards})
            yield _sse({"type": "done"})

        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            yield _sse({"type": "error", "v": GENERIC_ERROR_MESSAGE})
            yield _sse({"type": "done"})

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# --- Gradio Chat Interface ---
from ui import demo

app = gr.mount_gradio_app(app, demo, path="/")

if __name__ == "__main__":
    # Local development default
    uvicorn.run(app, host="0.0.0.0", port=8000)
