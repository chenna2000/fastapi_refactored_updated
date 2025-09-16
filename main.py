from fastapi import FastAPI, WebSocket, Depends
from fastapi.middleware.cors import CORSMiddleware
from proj_websockets.chat_ws import handle_chat_websocket
from proj_websockets.community_ws import handle_community_websocket
from database import get_db
from routers import users, chat, community
from database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FastAPI Chat Backend",
    description="Backend API for a real-time chat application with user authentication and conversation management.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(community.router, prefix="/community", tags=["Community"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI Chat Backend!"}

@app.websocket("/ws/chat/{conversation_id}/")
async def chat_websocket_endpoint(websocket: WebSocket, conversation_id: str, db=Depends(get_db)):
    print(f"--- Attempting WebSocket connection for chat: {conversation_id} ---")
    try:
        await handle_chat_websocket(websocket, conversation_id, db)
    except Exception as e:
        print(f"!!! Error in chat_websocket_endpoint: {e} !!!")
        await websocket.close(code=1011, reason=f"Internal Server Error: {e}")

@app.websocket("/ws/community/{community_id}/")
async def community_websocket_endpoint(websocket: WebSocket, community_id: str, db=Depends(get_db)):
    await handle_community_websocket(websocket, community_id, db)