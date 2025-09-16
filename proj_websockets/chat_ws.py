from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
from sqlalchemy.orm import Session
from datetime import datetime
import crud
import schemas
import uuid

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, conversation_id: str):
        await websocket.accept()
        if conversation_id not in self.active_connections:
            self.active_connections[conversation_id] = []
        self.active_connections[conversation_id].append(websocket)

    def disconnect(self, websocket: WebSocket, conversation_id: str):
        if conversation_id in self.active_connections:
            if websocket in self.active_connections[conversation_id]:
                self.active_connections[conversation_id].remove(websocket)
                if not self.active_connections[conversation_id]:
                    del self.active_connections[conversation_id]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str, conversation_id: str):
        if conversation_id in self.active_connections:
            for connection in self.active_connections[conversation_id]:
                await connection.send_text(message)

manager = ConnectionManager()

async def handle_chat_websocket(
    websocket: WebSocket,
    conversation_id: str,
    db: Session,
    # === REMOVE THIS PARAMETER: current_user: models.User
):
    try:
        await manager.connect(websocket, conversation_id)

        # Check conversation exists (removed current_user check)
        conversation = crud.get_conversation(db=db, conversation_id=conversation_id)
        if not conversation:
            await websocket.close(code=1008, reason="Conversation not found or accessible.")
            return

        # await manager.send_personal_message(f"You joined conversation: {conversation.id}", websocket) # Removed user email

        while True:
            try:
                data = await websocket.receive_text()
                message_data = json.loads(data)

                message_content = message_data.get("content", "").strip()
                sender_id = message_data.get("sender_id") # Now sender_id comes directly from frontend, less secure!
                timestamp = datetime.utcnow()

                if not message_content or not sender_id:
                    await manager.send_personal_message("Missing 'content' or 'sender_id'", websocket)
                    continue

                # === IMPORTANT SECURITY NOTE:
                # If you're not authenticating, the sender_id provided by the client
                # cannot be trusted. Anyone can claim to be any sender_id.
                # If sender_id is meant to represent the current user,
                # you will have to find another way to establish their identity.
                # For basic functionality, you can proceed, but be aware of the implications.
                # If sender_id is still a UUID, ensure it's converted correctly.

                # Step 1: Create message schema
                message_obj = schemas.OneToOneMessageCreate(
                    content=message_content,
                    sender_id=uuid.UUID(sender_id), # Ensure it's a valid UUID
                    conversation_id=uuid.UUID(conversation_id),
                )

                # Step 2: Store in DB
                saved_msg = crud.create_message(db=db, message=message_obj)

                # Step 3: Broadcast to all participants
                response = {
                    "conversation_id": conversation_id,
                    "content": message_content,
                    "sender_id": str(sender_id), # Still send back as string
                    "created_at": timestamp.isoformat(),
                    "type": "message"
                }
                await manager.broadcast(json.dumps(response), conversation_id)

                # Step 4: Optionally update conversation metadata
                crud.update_conversation_last_message(
                    db=db,
                    conversation_id=conversation_id,
                    message_content=message_content,
                    timestamp=timestamp
                )

            except json.JSONDecodeError:
                await manager.send_personal_message("Invalid JSON format.", websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket, conversation_id)
        await manager.broadcast(f"Client left the conversation {conversation_id}", conversation_id) # Removed current_user.email
    except Exception as e:
        print(f"An error occurred in chat_websocket: {e}")
        await websocket.close(code=1011, reason=f"Server error: {e}")