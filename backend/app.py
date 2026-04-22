import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from agent import graph

app = FastAPI(title="AutoStream Social-to-Lead API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    message: str
    thread_id: Optional[str] = "default_session"

class ChatResponse(BaseModel):
    response: str
    thread_id: str
    state: dict

@app.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatMessage):
    try:
        config = {"configurable": {"thread_id": payload.thread_id}}
        result = graph.invoke(
            {"messages": [("user", payload.message)]},
            config
        )
        messages = result.get("messages", [])
        if not messages:
            raise HTTPException(status_code=500, detail="No messages returned from agent")
            
        last_msg = messages[-1]
        if hasattr(last_msg, "content"):
            response_text = last_msg.content
        elif isinstance(last_msg, tuple) and len(last_msg) > 1:
            response_text = last_msg[1]
        else:
            response_text = str(last_msg)
        
        state_summary = {
            "name": result.get("collected_name"),
            "email": result.get("collected_email"),
            "platform": result.get("collected_platform"),
            "lead_captured": result.get("lead_captured", False)
        }
        
        return ChatResponse(
            response=response_text,
            thread_id=payload.thread_id,
            state=state_summary
        )
        
    except Exception as e:
        print(f"[SYSTEM] ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
