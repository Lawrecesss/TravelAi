import os
import uuid
import uvicorn
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv


load_dotenv(".env.secret")

from core.agent import travel_agent_graph
from pinecone import Pinecone

app = FastAPI(title="TravelAi Agent REST API with Personalization", docs_url="/docs", redoc_url="/redoc", version="1.0.0", description="API for interacting with the TravelAi Planner agent, including endpoints for user preference ingestion and multi-turn chat interactions with personalized context retrieval.")

# Initialize Pinecone client connection
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name = os.getenv("PINECONE_INDEX_NAME")
pinecone_index = pc.Index(index_name)

# --- Request & Response Schemas ---
class UserPreferenceRequest(BaseModel):
    user_id: str = Field(..., description="Unique identifier for the user or traveler.")
    preference: str = Field(..., description="The textual travel preference to ingest (e.g., 'I prefer luxury resorts and avoid rainy seasons').")

class ChatRequest(BaseModel):
    message: str = Field(..., description="The textual message sent to the travel agent.")
    user_id: str = Field(..., description="The unique identifier for the user to look up long-term preferences.")
    thread_id: Optional[str] = Field(
        None, 
        description="Unique identifier for tracking short-term conversation context. If empty, a new session is initialized."
    )

class ChatResponse(BaseModel):
    thread_id: str
    response: str
    history_snapshot: List[Dict[str, Any]]

# --- API Endpoint ---
@app.get("/")
async def root_landing_page():
    return {
        "status": "online",
        "message": "Welcome to the TravelAi Agent API! Use /api/chat to interact with the agent or visit /docs for interactive API documentation."
    }

@app.post("/api/preferences/ingest", status_code=status.HTTP_201_CREATED)
async def ingest_user_preference(payload: UserPreferenceRequest):
    try:
        if not index_name:
            raise HTTPException(status_code=500, detail="PINECONE_INDEX_NAME environment variable is not set.")
        
        record_id = f"pref_{payload.user_id}_{uuid.uuid4().hex[:8]}"
        pinecone_index.upsert(
            vectors=[
                {
                    "id": record_id,
                    "values": pc.inference.embed(
                        model="multilingual-e5-large",  # Ensure this matches your existing index dimension (1024)
                        inputs=[payload.preference],
                        parameters={"input_type": "passage", "truncate": "END"}
                    )[0]["values"],
                    "metadata": {
                        "user_id": payload.user_id,
                        "text": payload.preference,     # Crucial for your LangGraph retrieval tool to read back context
                        "category": "user_preference"   # Standardizes metadata fields to avoid null/KeyErrors
                    }
                }
            ],
            namespace="preferences"  # Isolates user files from global travel blogs/Wikipedia dumps
        )
        
        return {
            "status": "success",
            "message": "User preference successfully vectorized and ingested.",
            "record_id": record_id,
            "namespace": "preferences"
        }
        
    except Exception as e:
        # Avoid validation masking by surfacing the raw exception error back for local development debugging
        raise HTTPException(status_code=500, detail=f"Pinecone Ingestion Error: {str(e)}")
    
@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_agent(payload: ChatRequest):
    try:
        # 1. Resolve or initialize short-term conversation thread memory tag
        active_thread_id = payload.thread_id or str(uuid.uuid4())
        
        # 2. Extract user metadata 
        target_user = payload.user_id
        user_preference_context = ""

        # 3. Look up user preference inside Pinecone under the "preferences" namespace
        try:
            # We construct a query vector of zeros since we are performing a metadata-only filter lookup
            # matching the explicit user_id string to pull their long-term preference profile.
            query_res = pinecone_index.query(
                vector=[0.0] * 1024,  # Adjust dimensions (e.g., 1024 for multilingual-e5-large / llama-text-embed-v2)
                filter={"user_id": {"$eq": target_user}},
                top_k=1,
                include_metadata=True,
                namespace="preferences"  # Target the dedicated preferences namespace
            )
            
            # If a preference record exists, extract the text from the matching metadata
            if query_res and query_res.get("matches"):
                match = query_res["matches"][0]
                user_preference_context = match.get("metadata", {}).get("text", "")
                
        except Exception as pinecone_err:
            # Log the error but do not crash the endpoint—allow fallback execution without custom preferences
            print(f"[Pinecone Preference Lookup Warning]: {pinecone_err}")

        # 4. Inject the preference into the message stream context
        # We append the preference string dynamically to guide the LLM's behavioral footprint.
        input_messages = []
        if user_preference_context:
            preference_instruction = (
                f"[USER PROFILE INTERCEPT]: The following long-term preferences are registered for "
                f"user '{target_user}': {user_preference_context}. You must prioritize these constraints "
                f"when formulating trip suggestions."
            )
            input_messages.append({"role": "system", "content": preference_instruction})
        
        # Append the current incoming user message text
        input_messages.append({"role": "user", "content": payload.message})

        # 5. Build execution configuration dictionary with short-term checkpointer context
        config = {"configurable": {"thread_id": active_thread_id}}

        # 6. Fire the Multi-Hop reasoning loop
        output_state = await travel_agent_graph.ainvoke(
            {"messages": input_messages}, 
            config=config
        )

        # 7. Robust backward-scanning to capture the final assistant AIMessage answer safely
        final_answer = "I apologize, but I couldn't formulate a response. Please try again."
        sanitized_history = []

        if "messages" in output_state and output_state["messages"]:
            # Traverse backwards to skip intermediate ToolMessages or structural dict logs
            for msg in reversed(output_state["messages"]):
                # Handle both object attributes (.content) and dictionary forms safely
                content = getattr(msg, "content", msg.get("content") if isinstance(msg, dict) else "")
                msg_type = getattr(msg, "type", msg.get("type") if isinstance(msg, dict) else "")
                
                if msg_type == "ai" and content:
                    final_answer = str(content)
                    break

            # Sanitize full message stream array for the frontend tracking payload
            for msg in output_state["messages"]:
                content = getattr(msg, "content", msg.get("content") if isinstance(msg, dict) else "")
                msg_role = getattr(msg, "type", msg.get("type") if isinstance(msg, dict) else "user")
                sanitized_history.append({"role": str(msg_role), "content": str(content)})

        return ChatResponse(
            thread_id=active_thread_id,
            response=final_answer,
            history_snapshot=sanitized_history
        )

    except Exception as e:
        print("=== CRITICAL BACKEND ERROR TRACE ===")
        import traceback
        traceback.print_exc()
        print("=====================================")
        raise HTTPException(status_code=500, detail=f"Internal Agent Loop Error: {str(e)}")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)