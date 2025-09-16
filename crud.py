import uuid
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import Optional, List, Dict
import models, schemas
from fastapi import HTTPException, status
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_user(db: Session, user_id: str) -> Optional[models.User]:
    """
    Retrieves a single user by their ID.
    """
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """
    Retrieves a single user by their email address.
    """
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
    """
    Retrieves a list of users with pagination.
    """
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    """
    Creates a new user with a hashed password.
    """
    password = pwd_context.hash(user.password)
    db_user = models.User(
        id=str(uuid.uuid4()),
        email=user.email,
        name=user.name,
        profile_picture=user.profile_picture,
        is_staff=user.is_staff,
        is_active=user.is_active,
        # is_superuser=user.is_superuser,
        password=password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: str, user_update: schemas.UserBase) -> Optional[models.User]:
    """
    Updates an existing user's information.
    """
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    for key, value in user_update.model_dump(exclude_unset=True).items():
        setattr(db_user, key, value)
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: str) -> bool:
    """
    Deletes a user by their ID.
    Returns True if the user was deleted, False otherwise.
    """
    db_user = get_user(db, user_id)
    if not db_user:
        return False
    db.delete(db_user)
    db.commit()
    return True

def get_conversation(db: Session, conversation_id: str) -> Optional[models.Conversation]:
    """
    Retrieves a single conversation by its ID.
    """
    return db.query(models.Conversation).filter(models.Conversation.id == conversation_id).first()


def get_conversations_by_user(db: Session, user_id: str) -> List[models.Conversation]:
    """
    Retrieves all conversations involving a specific user.
    """
    return db.query(models.Conversation).filter(
        (models.Conversation.user1_id == user_id) | (models.Conversation.user2_id == user_id)
    ).all()


def create_conversation(
    db: Session, conversation: schemas.ConversationCreate
) -> models.Conversation:
    """
    Creates a new conversation.
    """
    db_conversation = models.Conversation(
        id=str(uuid.uuid4()),
        user1_id=str(conversation.user1_id),
        user2_id=str(conversation.user2_id),
        last_message=conversation.last_message,
        last_message_time=conversation.last_message_time
    )
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)
    return db_conversation


def update_conversation_last_message(
    db: Session, conversation_id: str, message_content: str, timestamp: datetime
) -> Optional[models.Conversation]:
    """
    Updates the last message and timestamp for a given conversation.
    """
    db_conversation = get_conversation(db, conversation_id)
    if not db_conversation:
        return None
    db_conversation.last_message = message_content # type: ignore
    db_conversation.last_message_time = timestamp # type: ignore
    db.commit()
    db.refresh(db_conversation)
    return db_conversation


def delete_conversation(db: Session, conversation_id: str) -> bool:
    """
    Deletes a conversation by its ID.
    Returns True if the conversation was deleted, False otherwise.
    """
    db_conversation = get_conversation(db, conversation_id)
    if not db_conversation:
        return False
    db.delete(db_conversation)
    db.commit()
    return True

def get_message(db: Session, message_id: str) -> Optional[models.OneToOneMessage]:
    """
    Retrieves a single one-to-one message by its ID.
    """
    return db.query(models.OneToOneMessage).filter(models.OneToOneMessage.id == message_id).first()


def get_messages_by_conversation(db: Session, conversation_id: str) -> List[models.OneToOneMessage]:
    """
    Retrieves all one-to-one messages within a specific conversation.
    """
    return db.query(models.OneToOneMessage).filter(models.OneToOneMessage.conversation_id == conversation_id).all()


def create_message(
    db: Session, message: schemas.OneToOneMessageCreate
) -> models.OneToOneMessage:
    """
    Creates a new one-to-one message and updates the parent conversation's last message.
    """
    db_message = models.OneToOneMessage(
        id=str(uuid.uuid4()),
        conversation_id=str(message.conversation_id),
        sender_id=str(message.sender_id),
        content=message.content
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)

    update_conversation_last_message(
        db=db,
        conversation_id=str(message.conversation_id),
        message_content=message.content,
        timestamp=datetime.utcnow()
    )

    return db_message


def delete_message(db: Session, message_id: str) -> bool:
    """
    Deletes a one-to-one message by its ID.
    Returns True if the message was deleted, False otherwise.
    """
    db_message = get_message(db, message_id)
    if not db_message:
        return False
    db.delete(db_message)
    db.commit()
    return True

def get_conversation_request(db: Session, request_id: str) -> Optional[models.ConversationRequest]:
    """
    Retrieves a single conversation request by its ID.
    Eager loads sender and expert objects to populate related fields.
    """
    request = db.query(models.ConversationRequest)\
        .options(joinedload(models.ConversationRequest.sender_obj),
                 joinedload(models.ConversationRequest.expert_obj))\
        .filter(models.ConversationRequest.id == request_id).first()
    
    if request and request.expert_obj:
        request.expert_email = request.expert_obj.email # type: ignore
    if request and request.sender_obj:
        request.sender_email = request.sender_obj.email # type: ignore
    return request


def get_requests_by_sender(db: Session, sender_id: str) -> List[models.ConversationRequest]:
    """
    Retrieves all conversation requests sent by a specific user.
    Eager loads sender and expert objects to populate related fields.
    """
    requests = db.query(models.ConversationRequest)\
        .options(joinedload(models.ConversationRequest.sender_obj),
                 joinedload(models.ConversationRequest.expert_obj))\
        .filter(models.ConversationRequest.sender_id == sender_id).all()
    
    for request in requests:
        if request.expert_obj:
            request.expert_email = request.expert_obj.email # type: ignore
        if request.sender_obj:
            request.sender_email = request.sender_obj.email # type: ignore
    return requests


def get_requests_by_expert(db: Session, expert_id: str) -> List[models.ConversationRequest]:
    """
    Retrieves all conversation requests received by a specific expert user.
    Eager loads sender and expert objects to populate related fields.
    """
    requests = db.query(models.ConversationRequest)\
        .options(joinedload(models.ConversationRequest.sender_obj),
                 joinedload(models.ConversationRequest.expert_obj))\
        .filter(models.ConversationRequest.expert_id == expert_id).all()
    
    for request in requests:
        if request.expert_obj:
            request.expert_email = request.expert_obj.email # type: ignore
        if request.sender_obj:
            request.sender_email = request.sender_obj.email # type: ignore
    return requests


def create_conversation_request(
    db: Session, sender_id: uuid.UUID, expert_email: str, request_message: Optional[str] = None
) -> models.ConversationRequest:
    """
    Creates a new conversation request if no conversation exists between the sender and expert.
    The expert is identified by their email.
    """
    # print("mail recieved: "+expert_email)
    expert_user = get_user_by_email(db, expert_email)
    if not expert_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expert user not found with the provided email"
        )
    
    expert_id = expert_user.id

    existing_conversation = db.query(models.Conversation).filter(
        (
            (models.Conversation.user1_id == str(sender_id)) &
            (models.Conversation.user2_id == str(expert_id))
        ) | (
            (models.Conversation.user1_id == str(expert_id)) &
            (models.Conversation.user2_id == str(sender_id))
        )
    ).first()

    if existing_conversation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A conversation already exists between these users"
        )

    db_request = models.ConversationRequest(
        id=str(uuid.uuid4()),
        sender_id=str(sender_id),
        expert_id=str(expert_id),
        request_message=request_message
    )
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    db_request.expert_email = expert_email # type: ignore
    sender_user = get_user(db, str(sender_id))
    if sender_user:
        db_request.sender_email = sender_user.email # type: ignore
    
    db_request.expert_obj = expert_user # type: ignore
    db_request.sender_obj = sender_user # type: ignore

    return db_request

def accept_conversation_request(db: Session, request_id: str) -> Dict[str, str]:
    """
    Marks a conversation request as accepted.
    """
    db_request = get_conversation_request(db, request_id)
    if not db_request:
        return {"message": "Conversation request not found", "conversation_id": "None"}
    db_request.is_accepted = True # type: ignore

    db_conversation = models.Conversation(
        id=str(uuid.uuid4()),
        user1_id=str(db_request.sender_id),
        user2_id=str(db_request.expert_id),
        last_message=db_request.request_message,
        last_message_time=db_request.created_at
    )
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)

    db_message = models.OneToOneMessage(
        id=str(uuid.uuid4()),
        conversation_id=str(db_conversation.id),
        sender_id=str(db_request.sender_id),
        content=db_request.request_message
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)

    update_conversation_last_message(
        db=db,
        conversation_id=str(db_conversation.id),
        message_content=str(db_request.request_message),
        timestamp=datetime.utcnow()
    )

    db.commit()
    db.refresh(db_request)

    delete_conversation_request(db, request_id)
    return {"message": "Accepted", "conversation_id": str(db_conversation.id)}

def delete_conversation_request(db: Session, request_id: str) -> bool:
    """
    Deletes a conversation request by its ID.
    Returns True if the request was deleted, False otherwise.
    """
    db_request = get_conversation_request(db, request_id)
    if not db_request:
        return False
    db.delete(db_request)
    db.commit()
    return True

def get_community(db: Session, community_id: str) -> Optional[models.Community]:
    """
    Retrieves a single community by its ID.
    """
    return db.query(models.Community).filter(models.Community.id == community_id).first()


def get_communities(db: Session, skip: int = 0, limit: int = 100) -> List[models.Community]:
    """
    Retrieves a list of communities with pagination.
    """
    return db.query(models.Community).offset(skip).limit(limit).all()


def create_community(db: Session, community: schemas.CommunityCreate) -> models.Community:
    """
    Creates a new community.
    """
    db_community = models.Community(
        id=str(uuid.uuid4()),
        name=community.name,
        description=community.description
    )
    db.add(db_community)
    db.commit()
    db.refresh(db_community)
    return db_community


def update_community(db: Session, community_id: str, community_update: schemas.CommunityBase) -> Optional[models.Community]:
    """
    Updates an existing community's information.
    """
    db_community = get_community(db, community_id)
    if not db_community:
        return None
    for key, value in community_update.model_dump(exclude_unset=True).items():
        setattr(db_community, key, value)
    db.commit()
    db.refresh(db_community)
    return db_community


def delete_community(db: Session, community_id: str) -> bool:
    """
    Deletes a community by its ID.
    Returns True if the community was deleted, False otherwise.
    """
    db_community = get_community(db, community_id)
    if not db_community:
        return False
    db.delete(db_community)
    db.commit()
    return True


def get_user_communities(db: Session, user_id: str) -> List[models.Community]:
    """
    Retrieves all communities a user is a member of.
    """
    return db.query(models.Community).join(models.Membership).filter(
        models.Membership.user_id == user_id
    ).all()


def get_popular_communities(db: Session, limit: int = 10) -> List[models.Community]:
    """
    Retrieves a list of communities ordered by their member count (most popular first).
    """
    return db.query(
        models.Community,
        func.count(models.Membership.id).label('total_members')
    ).outerjoin(models.Membership).group_by(models.Community.id).order_by(
        func.count(models.Membership.id).desc()
    ).limit(limit).all() # type: ignore


def get_community_member_count(db: Session, community_id: str) -> int:
    """
    Returns the number of members in a given community.
    """
    return db.query(models.Membership).filter(models.Membership.community_id == community_id).count()

def get_membership(db: Session, membership_id: str) -> Optional[models.Membership]:
    """
    Retrieves a single membership by its ID.
    """
    return db.query(models.Membership).filter(models.Membership.id == membership_id).first()


def get_memberships_by_community(db: Session, community_id: str, skip: int = 0, limit: int = 100) -> List[models.Membership]:
    """
    Retrieves all memberships for a specific community with pagination.
    """
    return db.query(models.Membership).filter(models.Membership.community_id == community_id).offset(skip).limit(limit).all()


def get_memberships_by_user(db: Session, user_id: str, skip: int = 0, limit: int = 100) -> List[models.Membership]:
    """
    Retrieves all memberships for a specific user with pagination.
    """
    return db.query(models.Membership).filter(models.Membership.user_id == user_id).offset(skip).limit(limit).all()


def get_membership_by_community_and_user(db: Session, community_id: str, user_id: str) -> Optional[models.Membership]:
    """
    Retrieves a specific membership by community ID and user ID.
    """
    return db.query(models.Membership).filter(
        models.Membership.community_id == community_id,
        models.Membership.user_id == user_id
    ).first()


def create_membership(db: Session, membership: schemas.MembershipCreate) -> models.Membership:
    """
    Creates a new community membership.
    """
    db_membership = models.Membership(
        id=str(uuid.uuid4()),
        community_id=str(membership.community_id),
        user_id=str(membership.user_id),
        is_admin=membership.is_admin
    )
    db.add(db_membership)
    db.commit()
    db.refresh(db_membership)
    return db_membership


def update_membership(db: Session, membership_id: str, is_admin: bool) -> Optional[models.Membership]:
    """
    Updates the admin status of a membership.
    """
    db_membership = get_membership(db, membership_id)
    if not db_membership:
        return None
    db_membership.is_admin = is_admin # type: ignore
    db.commit()
    db.refresh(db_membership)
    return db_membership


def delete_membership(db: Session, membership_id: str) -> bool:
    """
    Deletes a membership by its ID.
    Returns True if the membership was deleted, False otherwise.
    """
    db_membership = get_membership(db, membership_id)
    if not db_membership:
        return False
    db.delete(db_membership)
    db.commit()
    return True


def is_user_community_member(db: Session, user_id: str, community_id: str) -> bool:
    """
    Checks if a user is a member of a specific community.
    """
    return db.query(models.Membership).filter(
        models.Membership.user_id == str(user_id),
        models.Membership.community_id == str(community_id)
    ).first() is not None

def get_community_message(db: Session, message_id: str) -> Optional[models.CommunityMessage]:
    """
    Retrieves a single community message by its ID.
    """
    return db.query(models.CommunityMessage).filter(models.CommunityMessage.id == message_id).first()


def get_community_messages_by_community(db: Session, community_id: str, skip: int = 0, limit: int = 20) -> List[models.CommunityMessage]:
    """
    Retrieves community messages for a specific community with pagination.
    Orders messages by creation time in descending order.
    """
    return db.query(models.CommunityMessage).filter(
        models.CommunityMessage.community_id == community_id
    ).order_by(models.CommunityMessage.created_at.desc()).offset(skip).limit(limit).all()


def create_community_message(db: Session, message: schemas.CommunityMessageCreate) -> models.CommunityMessage:
    """
    Creates a new community message.
    """
    db_message = models.CommunityMessage(
        id=str(uuid.uuid4()),
        community_id=str(message.community_id),
        sender_id=str(message.sender_id),
        content=message.content
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


def update_community_message(db: Session, message_id: str, content: str) -> Optional[models.CommunityMessage]:
    """
    Updates the content of an existing community message.
    """
    db_message = get_community_message(db, message_id)
    if not db_message:
        return None
    db_message.content = content # type: ignore
    db.commit()
    db.refresh(db_message)
    return db_message


def delete_community_message(db: Session, message_id: str) -> bool:
    """
    Deletes a community message by its ID.
    Returns True if the message was deleted, False otherwise.
    """
    db_message = get_community_message(db, message_id)
    if not db_message:
        return False
    db.delete(db_message)
    db.commit()
    return True

def get_reply(db: Session, reply_id: str) -> Optional[models.Reply]:
    """
    Retrieves a single reply by its ID.
    """
    return db.query(models.Reply).filter(models.Reply.id == reply_id).first()


def get_replies_by_message(db: Session, message_id: str, skip: int = 0, limit: int = 100) -> List[models.Reply]:
    """
    Retrieves all replies for a specific community message with pagination.
    """
    return db.query(models.Reply).filter(
        models.Reply.message_id == message_id
    ).order_by(models.Reply.created_at).offset(skip).limit(limit).all()


def create_reply(db: Session, reply: schemas.ReplyCreate) -> models.Reply:
    """
    Creates a new reply to a community message.
    """
    db_reply = models.Reply(
        id=str(uuid.uuid4()),
        message_id=str(reply.message_id),
        sender_id=str(reply.sender_id),
        content=reply.content
    )
    db.add(db_reply)
    db.commit()
    db.refresh(db_reply)
    return db_reply


def update_reply(db: Session, reply_id: str, content: str) -> Optional[models.Reply]:
    """
    Updates the content of an existing reply.
    """
    db_reply = get_reply(db, reply_id)
    if not db_reply:
        return None
    db_reply.content = content # type: ignore
    db.commit()
    db.refresh(db_reply)
    return db_reply


def delete_reply(db: Session, reply_id: str) -> bool:
    """
    Deletes a reply by its ID.
    Returns True if the reply was deleted, False otherwise.
    """
    db_reply = get_reply(db, reply_id)
    if not db_reply:
        return False
    db.delete(db_reply)
    db.commit()
    return True


def get_community_discussion_paginated(db: Session, community_id: str, skip: int = 0, limit: int = 20) -> List[models.CommunityMessage]:
    """
    Retrieves community messages and their replies for a given community, paginated.
    It eager loads sender and replies (with reply sender) to minimize database queries.
    """
    messages = db.query(models.CommunityMessage)\
        .options(
            joinedload(models.CommunityMessage.sender_obj),
            joinedload(models.CommunityMessage.replies).joinedload(models.Reply.sender_obj)
        )\
        .filter(models.CommunityMessage.community_id == community_id)\
        .order_by(models.CommunityMessage.created_at.desc())\
        .offset(skip).limit(limit)\
        .all()
    return messages


def search_users_in_community(db: Session, community_id: str, name_startswith: Optional[str] = None) -> List[models.User]:
    """
    Searches for users within a specific community, optionally filtering by name.
    """
    query = db.query(models.User)\
              .join(models.Membership)\
              .filter(models.Membership.community_id == community_id)\
              .distinct()
    
    if name_startswith:
        query = query.filter(models.User.name.ilike(f"{name_startswith}%"))

    return query.all()
