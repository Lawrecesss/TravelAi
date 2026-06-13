import os
import uuid
import uvicorn
import traceback
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# Load environment secrets at the very top of application startup
load_dotenv(".env.secret")
# Import the prebuilt graph instance from your agent script
from core.agent import travel_agent_graph


app = FastAPI(title="TravelAi Agent REST API")

# Define request validation schema
class ChatRequest(BaseModel):
    message: str = Field(..., description="The textual message sent to the travel agent.")
    thread_id: Optional[str] = Field(
        None, 
        description="Unique identifier for tracking a single conversation session. If empty, a new session is initialized."
    )

# Define response validation schema
class ChatResponse(BaseModel):
    thread_id: str
    response: str
    history_snapshot: List[Dict[str, Any]]

# FIX: Add a Root URL Route to prevent {"detail": "Not Found"}
@app.get("/")
async def root_landing_page():
    return {
        "status": "online",
        "message": "Welcome to the TravelAi Agent API! Use /api/chat to interact with the agent or visit /docs for interactive API documentation."
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_agent(payload: ChatRequest):
    try:
        # Ensure a valid thread identifier exists (generate a UUID if it's the very first request)
        active_thread_id = payload.thread_id or str(uuid.uuid4())
        
        # Structure the required LangGraph configuration context
        config = {"configurable": {"thread_id": active_thread_id}}
        
        # Prepare inputs representing the human message update 
        inputs = {"messages": [{"role": "user", "content": payload.message}]}
        
        # Run execution blocks through the compiled StateGraph
        output_state = await travel_agent_graph.ainvoke(inputs, config=config)
        
        # Extract the final response in a minimal way for testing
        final_response_text = ""
        messages_history = output_state.get("messages", []) if isinstance(output_state, dict) else []

        if messages_history:
            for msg in reversed(messages_history):
                if hasattr(msg, "type") and msg.type == "ai" and msg.content:
                    final_response_text = msg.content
                    break
                elif isinstance(msg, dict) and msg.get("role") == "assistant" and msg.get("content"):
                    final_response_text = msg.get("content")
                    break

        # Fallback to generic output fields if messages are not present
        if not final_response_text:
            final_response_text = output_state.get("output") if isinstance(output_state, dict) else ""

        if not final_response_text:
            final_response_text = "I have processed your request but haven't generated a text answer."

        return ChatResponse(
            thread_id=active_thread_id,
            response=final_response_text,
            history_snapshot=[]
        )
        
    except Exception as e:
        # Print detailed error to server logs for debugging
        print(f"Error in agent execution: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Agent Loop Error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)