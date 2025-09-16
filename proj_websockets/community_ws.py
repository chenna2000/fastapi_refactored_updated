from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
from sqlalchemy.orm import Session
from datetime import datetime
import crud
import schemas
import uuid

class ConnectionManager:
    """
    Manages active WebSocket connections for different communities.
    Each community_id can have multiple active WebSocket connections.
    """
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, community_id: str):
        """
        Accepts a new WebSocket connection and adds it to the active connections
        for the specified community.
        """
        await websocket.accept()
        if community_id not in self.active_connections:
            self.active_connections[community_id] = []
        self.active_connections[community_id].append(websocket)

    def disconnect(self, websocket: WebSocket, community_id: str):
        """
        Removes a WebSocket connection from the active connections for its community.
        If no connections remain for a community, its entry is removed from the dictionary.
        """
        if community_id in self.active_connections:
            if websocket in self.active_connections[community_id]:
                self.active_connections[community_id].remove(websocket)
                if not self.active_connections[community_id]:
                    del self.active_connections[community_id]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """
        Sends a message to a single WebSocket connection.
        """
        await websocket.send_text(message)

    async def broadcast(self, message: str, community_id: str):
        """
        Sends a message to all active WebSocket connections within a specific community.
        """
        if community_id in self.active_connections:
            for connection in list(self.active_connections[community_id]):
                try:
                    await connection.send_text(message)
                except RuntimeError as e:
                    print(f"Error sending to a connection in community {community_id}: {e}")
                    self.disconnect(connection, community_id)


manager = ConnectionManager()

async def handle_community_websocket(
    websocket: WebSocket,
    community_id: str,
    db: Session
):
    """
    Handles WebSocket communication for a specific community.
    It receives messages, stores them in the database, and broadcasts them.
    Expected incoming message format (JSON):
    For new community messages:
    {
        "type": "message",
        "sender_id": "uuid_of_sender",
        "content": "Your message content"
    }
    For replies to a message:
    {
        "type": "reply",
        "message_id": "uuid_of_parent_message",
        "sender_id": "uuid_of_sender",
        "content": "Your reply content"
    }
    """
    try:
        await manager.connect(websocket, community_id)

        community = crud.get_community(db=db, community_id=community_id)
        if not community:
            await manager.send_personal_message("Community not found.", websocket)
            await websocket.close(code=1008)
            return

        # await manager.send_personal_message(f"You joined community: {community.name}", websocket)

        while True:
            try:
                data = await websocket.receive_text()
                message_data = json.loads(data)

                msg_type = message_data.get("type")
                sender_id = message_data.get("sender_id")
                content = message_data.get("content", "").strip()
                timestamp = datetime.utcnow()

                if not sender_id or not content or not msg_type:
                    await manager.send_personal_message("Missing 'type', 'sender_id', or 'content'.", websocket)
                    continue

                try:
                    sender_uuid = uuid.UUID(sender_id)
                except ValueError:
                    await manager.send_personal_message("Invalid 'sender_id' format (must be UUID).", websocket)
                    continue

                user = crud.get_user(db, str(sender_uuid))
                if not user:
                    await manager.send_personal_message("Sender user not found.", websocket)
                    continue
                
                if not crud.is_user_community_member(db, str(sender_uuid), community_id):
                    await manager.send_personal_message("You are not a member of this community.", websocket)
                    continue


                response_payload = {
                    "type": msg_type,
                    "sender_id": str(sender_uuid),
                    "content": content,
                    "created_at": timestamp.isoformat(),
                }

                if msg_type == "message":
                    message_obj = schemas.CommunityMessageCreate(
                        community_id=uuid.UUID(community_id),
                        sender_id=sender_uuid,
                        content=content,
                    )
                    saved_msg = crud.create_community_message(db=db, message=message_obj)
                    response_payload["id"] = str(saved_msg.id)
                    response_payload["community_id"] = community_id
                    if saved_msg.sender_obj:
                        response_payload["sender_name"] = saved_msg.sender_obj.name
                    
                elif msg_type == "reply":
                    message_id = message_data.get("message_id")
                    if not message_id:
                        await manager.send_personal_message("Missing 'message_id' for reply.", websocket)
                        continue
                    
                    parent_message = crud.get_community_message(db, message_id)
                    if not parent_message:
                        await manager.send_personal_message("Parent message not found for reply.", websocket)
                        continue

                    reply_obj = schemas.ReplyCreate(
                        message_id=uuid.UUID(message_id),
                        sender_id=sender_uuid,
                        content=content,
                    )
                    saved_reply = crud.create_reply(db=db, reply=reply_obj)
                    response_payload["id"] = str(saved_reply.id)
                    response_payload["message_id"] = message_id
                    
                else:
                    await manager.send_personal_message("Unknown message type. Expected 'message' or 'reply'.", websocket)
                    continue

                await manager.broadcast(json.dumps(response_payload), community_id)

            except json.JSONDecodeError:
                await manager.send_personal_message("Invalid JSON format.", websocket)
            except WebSocketDisconnect:
                raise
            except Exception as e:
                print(f"WebSocket error in community {community_id}: {e}")
                await manager.send_personal_message(f"An error occurred: {e}", websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket, community_id)
        if community is not None:
            await manager.broadcast(f"Client left community {community_id}", community_id)
    except Exception as e:
        print(f"Error establishing community WebSocket connection: {e}")

