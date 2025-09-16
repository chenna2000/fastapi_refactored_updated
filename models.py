import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "user"

    # For UUIDField, we use BINARY(16) for MySQL or UUID for PostgreSQL.
    # We'll use String(36) to store the UUID as a string for broader compatibility and easier debugging,
    # and then convert it to UUID object in Pydantic schemas.
    # Alternatively, for MySQL, you can use sqlalchemy.dialects.mysql.BINARY(16)
    # and store UUIDs as actual binary data for performance.
    # For simplicity, I'm using String(36) here.
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    # Storing hashed passwords directly, similar to Django's CharField for password
    password = Column(String(128), nullable=True) # Renamed from 'password' to 'hashed_password' for clarity
    name = Column(String(64), nullable=False)
    profile_picture = Column(String(255), nullable=True) # URLField becomes String

    # Django PermissionsMixin and AbstractBaseUser fields
    is_staff = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    # not necessary field
    # is_superuser = Column(Boolean, default=False, nullable=False) # PermissionsMixin adds this
    # permissions field from PermissionsMixin
    # SQLAlchemy doesn't have a direct equivalent to Django's ManyToManyField for user_permissions,
    # but for simple checks like is_superuser, is_staff, these columns suffice.
    # If you have custom permissions, you'd define separate tables and relationships.

    # Relationships (not explicitly in your Django User model, but implied by FKs)
    conversations_as_user1 = relationship("Conversation", back_populates="user1_obj", foreign_keys="[Conversation.user1_id]")
    conversations_as_user2 = relationship("Conversation", back_populates="user2_obj", foreign_keys="[Conversation.user2_id]")
    sent_messages = relationship("OneToOneMessage", back_populates="sender_obj")
    sent_requests = relationship("ConversationRequest", back_populates="sender_obj", foreign_keys="[ConversationRequest.sender_id]")
    received_requests = relationship("ConversationRequest", back_populates="expert_obj", foreign_keys="[ConversationRequest.expert_id]")
    
    community_memberships = relationship("Membership", back_populates="user_obj")
    community_messages = relationship("CommunityMessage", back_populates="sender_obj")
    replies = relationship("Reply", back_populates="sender_obj")


    def __repr__(self):
        return f"<User(id='{self.id}', email='{self.email}')>"

class Conversation(Base):
    __tablename__ = "conversation"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    user1_id = Column(String(36), ForeignKey("user.id"), nullable=False)
    user2_id = Column(String(36), ForeignKey("user.id"), nullable=False)
    
    last_message = Column(Text, nullable=True)
    last_message_time = Column(DateTime, nullable=True)

    user1_obj = relationship("User", foreign_keys=[user1_id], back_populates="conversations_as_user1")
    user2_obj = relationship("User", foreign_keys=[user2_id], back_populates="conversations_as_user2")
    messages = relationship("OneToOneMessage", back_populates="conversation_obj")

    __table_args__ = (
        Index('idx_conversation_user1_user2', user1_id, user2_id),
        Index('idx_conversation_last_message_time', last_message_time),
    )

    def __repr__(self):
        return f"<Conversation(id='{self.id}', user1_id='{self.user1_id}', user2_id='{self.user2_id}')>"


class OneToOneMessage(Base):
    __tablename__ = "onetoonemessage"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    conversation_id = Column(String(36), ForeignKey("conversation.id"), nullable=False)
    sender_id = Column(String(36), ForeignKey("user.id"), nullable=False)
    
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    conversation_obj = relationship("Conversation", back_populates="messages")
    sender_obj = relationship("User", back_populates="sent_messages")

    def __repr__(self):
        return f"<OneToOneMessage(id='{self.id}', conversation_id='{self.conversation_id}', sender_id='{self.sender_id}')>"


class ConversationRequest(Base):
    __tablename__ = "conversation_request"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    sender_id = Column(String(36), ForeignKey("user.id"), nullable=False)
    expert_id = Column(String(36), ForeignKey("user.id"), nullable=False)
    
    request_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_accepted = Column(Boolean, default=False, nullable=False)

    sender_obj = relationship("User", foreign_keys=[sender_id], back_populates="sent_requests")
    expert_obj = relationship("User", foreign_keys=[expert_id], back_populates="received_requests")

    __table_args__ = (UniqueConstraint('sender_id', 'expert_id', name='_sender_expert_uc'),)


    def __repr__(self):
        return f"<ConversationRequest(id='{self.id}', sender_id='{self.sender_id}', expert_id='{self.expert_id}')>"


class Community(Base):
    __tablename__ = "community"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(128), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    memberships = relationship("Membership", back_populates="community_obj")
    messages = relationship("CommunityMessage", back_populates="community_obj")

    def __repr__(self):
        return f"<Community(id='{self.id}', name='{self.name}')>"


class Membership(Base):
    __tablename__ = "membership"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    community_id = Column(String(36), ForeignKey("community.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("user.id"), nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)

    community_obj = relationship("Community", back_populates="memberships")
    user_obj = relationship("User", back_populates="community_memberships")

    __table_args__ = (UniqueConstraint('community_id', 'user_id', name='_community_user_uc'),)

    def __repr__(self):
        return f"<Membership(id='{self.id}', community_id='{self.community_id}', user_id='{self.user_id}')>"


class CommunityMessage(Base):
    __tablename__ = "community_message"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    community_id = Column(String(36), ForeignKey("community.id"), nullable=False)
    sender_id = Column(String(36), ForeignKey("user.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    community_obj = relationship("Community", back_populates="messages")
    sender_obj = relationship("User", back_populates="community_messages")
    replies = relationship("Reply", back_populates="message_obj")


    def __repr__(self):
        return f"<CommunityMessage(id='{self.id}', community_id='{self.community_id}', sender_id='{self.sender_id}')>"


class Reply(Base):
    __tablename__ = "reply"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(String(36), ForeignKey("community_message.id"), nullable=False)
    sender_id = Column(String(36), ForeignKey("user.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    message_obj = relationship("CommunityMessage", back_populates="replies")
    sender_obj = relationship("User", back_populates="replies")

    def __repr__(self):
        return f"<Reply(id='{self.id}', message_id='{self.message_id}', sender_id='{self.sender_id}')>"
