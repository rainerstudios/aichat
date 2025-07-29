from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from dotenv import load_dotenv
import os

load_dotenv()

from app.langgraph.agent import assistant_ui_graph
from app.add_langgraph_route import add_langgraph_route

app = FastAPI()
# cors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

add_langgraph_route(app, assistant_ui_graph, "/api/chat")

if __name__ == "__main__":
    import uvicorn
    import logging

    logging.basicConfig(filename='backend.log', level=logging.INFO)
    uvicorn.run(app, host="0.0.0.0", port=8000)
