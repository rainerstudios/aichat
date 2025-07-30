from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from dotenv import load_dotenv
import os
import asyncio

load_dotenv()

from app.langgraph.agent import assistant_ui_graph
from app.add_langgraph_route import add_langgraph_route
from app.api.chat_persistence import router as chat_persistence_router
from app.services.chat_persistence import init_chat_database

app = FastAPI(
    title="XGaming Server AI Assistant",
    description="AI-powered support assistant for game servers with local chat persistence",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database and services on startup"""
    try:
        await init_chat_database()
        print("✅ Chat persistence database initialized")
    except Exception as e:
        print(f"❌ Failed to initialize chat database: {e}")

# Include routers
add_langgraph_route(app, assistant_ui_graph, "/api/chat")
app.include_router(chat_persistence_router)

if __name__ == "__main__":
    import uvicorn
    import logging

    logging.basicConfig(filename='backend.log', level=logging.INFO)
    uvicorn.run(app, host="0.0.0.0", port=8000)
