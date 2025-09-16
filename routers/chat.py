from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict
from datetime import datetime
import schemas, models, crud, auth
from database import get_db
import secrets

router = APIRouter(
    prefix="",
    tags=["Chat"],
)

secret_key = secrets.token_hex(32)

@router.post("/conversations/", response_model=schemas.ConversationOut, status_code=status.HTTP_201_CREATED)
def create_conversation_route(
    conversation: schemas.ConversationCreate,
    db: Session = Depends(get_db),
    # current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    Create a new conversation between two users.
    """
    return crud.create_conversation(db=db, conversation=conversation)


@router.get("/conversations/{conversation_id}", response_model=schemas.ConversationOut)
def read_conversation_route(conversation_id: str, db: Session = Depends(get_db)):
    """
    Get a specific conversation by ID.
    """
    conversation = crud.get_conversation(db=db, conversation_id=conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.get("/conversations/user/{user_id}", response_model=List[schemas.ConversationOut])
def read_conversations_by_user_route(user_id: str, db: Session = Depends(get_db)):
    """
    Get all conversations for a specific user.
    """
    return crud.get_conversations_by_user(db=db, user_id=user_id)


@router.put("/conversations/{conversation_id}/update-last-message", response_model=schemas.ConversationOut)
def update_conversation_last_message_route(
    conversation_id: str,
    message_content: str,
    db: Session = Depends(get_db)
):
    """
    Update the last message and timestamp of a conversation.
    """
    updated_conv = crud.update_conversation_last_message(
        db=db,
        conversation_id=conversation_id,
        message_content=message_content,
        timestamp=datetime.utcnow()
    )
    if not updated_conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return updated_conv


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_201_CREATED)
def delete_conversation_route(conversation_id: str, db: Session = Depends(get_db)):
    """
    Delete a conversation by ID.
    """
    success = crud.delete_conversation(db=db, conversation_id=conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"detail": "Conversation deleted successfully"}


@router.post("/messages/", response_model=schemas.OneToOneMessageOut, status_code=status.HTTP_201_CREATED)
def create_message_route(
    message: schemas.OneToOneMessageCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    Send a new one-to-one message in a conversation.
    """
    
    if str(current_user.id) != str(message.sender_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to send message as this user")

    return crud.create_message(db=db, message=message)


@router.get("/messages/{message_id}", response_model=schemas.OneToOneMessageOut)
def read_message_route(message_id: str, db: Session = Depends(get_db)):
    """
    Get a specific message by ID.
    """
    message = crud.get_message(db=db, message_id=message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return message


@router.get("/messages/conversation/{conversation_id}", response_model=List[schemas.OneToOneMessageOut])
def read_messages_by_conversation_route(conversation_id: str, db: Session = Depends(get_db)):
    """
    Get all messages for a specific conversation.
    """
    return crud.get_messages_by_conversation(db=db, conversation_id=conversation_id)


@router.delete("/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message_route(message_id: str, db: Session = Depends(get_db)):
    """
    Delete a message by ID.
    """
    success = crud.delete_message(db=db, message_id=message_id)
    if not success:
        raise HTTPException(status_code=404, detail="Message not found")
    return {"detail": "Message deleted successfully"}

@router.post("/requests/", response_model=schemas.ConversationRequestOut)
def create_conversation_request_route(
    request: schemas.ConversationRequestCreate,
    db: Session = Depends(get_db),
    # current_user: schemas.UserOut = Depends(get_current_active_user)
):
    # # Ensure the sender_id from the request matches the current authenticated user's ID
    # if str(request.sender_id) != str(current_user.id):
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="You can only create conversation requests for yourself."
    #     )
    # print("mail recieved1: "+request.expert_email)

    return crud.create_conversation_request(
        db=db,
        sender_id=request.sender_id,
        expert_email=request.expert_email,
        request_message=request.request_message
    )

@router.get("/requests/{request_id}", response_model=schemas.ConversationRequestOut)
def read_conversation_request_route(request_id: str, db: Session = Depends(get_db)):
    """
    Get a specific conversation request by ID.
    """
    request = crud.get_conversation_request(db=db, request_id=request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Conversation request not found")
    return request


@router.get("/requests/sender/{sender_id}", response_model=List[schemas.ConversationRequestOut])
def read_requests_by_sender_route(sender_id: str, db: Session = Depends(get_db)):
    """
    Get all conversation requests sent by a specific user.
    """
    return crud.get_requests_by_sender(db=db, sender_id=sender_id)


@router.get("/requests/expert/{expert_id}", response_model=List[schemas.ConversationRequestOut])
def read_requests_by_expert_route(expert_id: str, db: Session = Depends(get_db)):
    """
    Get all conversation requests received by a specific expert.
    """
    return crud.get_requests_by_expert(db=db, expert_id=expert_id)


@router.put("/requests/{request_id}/accept", response_model=Dict[str, str])
def accept_conversation_request_route(request_id: str, db: Session = Depends(get_db)):
    """
    Accept a conversation request.
    """
    result = crud.accept_conversation_request(db=db, request_id=request_id)
    if result["message"] == "Conversation request not found":
        raise HTTPException(status_code=404, detail="Conversation request not found")
    return result

@router.delete("/requests/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation_request_route(request_id: str, db: Session = Depends(get_db)):
    """
    Delete a conversation request by ID.
    """
    success = crud.delete_conversation_request(db=db, request_id=request_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation request not found")
    return {"detail": "Conversation request deleted successfully"}


