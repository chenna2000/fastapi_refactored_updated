from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime
import uuid

class UserBase(BaseModel):
    email: EmailStr
    name: str
    profile_picture: Optional[str] = None
    is_staff: bool = False
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    # id: uuid.UUID
    id: str
    password: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class UserOut(UserBase):
    # id: uuid.UUID
    id: str
    model_config = ConfigDict(from_attributes=True)

from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str

class ConversationBase(BaseModel):
    user1_id: uuid.UUID
    user2_id: uuid.UUID
    last_message: Optional[str] = None
    last_message_time: Optional[datetime] = None

class ConversationCreate(ConversationBase):
    pass

class ConversationOut(ConversationBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    user1_obj: Optional[UserOut] = None
    user2_obj: Optional[UserOut] = None
    model_config = ConfigDict(from_attributes=True)

class OneToOneMessageBase(BaseModel):
    conversation_id: uuid.UUID
    sender_id: uuid.UUID
    content: str

class OneToOneMessageCreate(OneToOneMessageBase):
    pass

class OneToOneMessageOut(OneToOneMessageBase):
    id: uuid.UUID
    created_at: datetime
    sender_obj: Optional[UserOut] = None
    model_config = ConfigDict(from_attributes=True)

class ConversationRequestBase(BaseModel):
    sender_id: uuid.UUID
    request_message: Optional[str] = None
    expert_email: EmailStr

class ConversationRequestCreate(ConversationRequestBase):
    pass

class ConversationRequestOut(ConversationRequestBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    is_accepted: bool
    
    sender_email: Optional[EmailStr] = None
    sender_obj: Optional[UserOut] = None
    expert_obj: Optional[UserOut] = None
    model_config = ConfigDict(from_attributes=True)

class CommunityBase(BaseModel):
    name: str
    description: Optional[str] = None

class CommunityCreate(CommunityBase):
    pass

class CommunityOut(CommunityBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class MembershipBase(BaseModel):
    community_id: uuid.UUID
    user_id: uuid.UUID
    is_admin: bool = False

class MembershipCreate(MembershipBase):
    pass

class MembershipOut(MembershipBase):
    id: uuid.UUID
    joined_at: datetime
    community_obj: Optional[CommunityOut] = None
    user_obj: Optional[UserOut] = None
    model_config = ConfigDict(from_attributes=True)

class CommunityMessageBase(BaseModel):
    community_id: uuid.UUID
    sender_id: uuid.UUID
    content: str

class CommunityMessageCreate(CommunityMessageBase):
    pass

class CommunityMessageOut(CommunityMessageBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    community_obj: Optional[CommunityOut] = None
    sender_obj: Optional[UserOut] = None
    model_config = ConfigDict(from_attributes=True)

class ReplyBase(BaseModel):
    message_id: uuid.UUID
    sender_id: uuid.UUID
    content: str

class ReplyCreate(ReplyBase):
    pass

class ReplyOut(ReplyBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    message_obj: Optional['CommunityMessageOut'] = None
    sender_obj: Optional[UserOut] = None
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

