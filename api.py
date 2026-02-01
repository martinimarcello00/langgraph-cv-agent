from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv

import uvicorn
from agent import graph

# Load env vars
load_dotenv()

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
        "http://127.0.0.1:8002"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default"

@app.post("/chat")
@limiter.limit("5/minute")
async def chat(request: Request, chat_request: ChatRequest):
    try:
        inputs = {"messages": [("user", chat_request.message)]}
        config = {"configurable": {"thread_id": chat_request.thread_id}}
        
        # Run graph with persistence
        result = await graph.ainvoke(inputs, config=config)
        
        # Extract last message
        last_msg = result["messages"][-1]
        return {"response": last_msg.content}
        
    except Exception as e:
        error_str = str(e)
        if "RESOURCE_EXHAUSTED" in error_str:
            raise HTTPException(status_code=429, detail="ops., too many people are asking infos about me! Try later")
        raise HTTPException(status_code=500, detail=error_str)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
