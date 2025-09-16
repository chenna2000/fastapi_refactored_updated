from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
import crud, schemas

load_dotenv()

SECRET_KEY: str = os.getenv("SECRET_KEY") or ""
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable not set")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/token")

def get_password_hash(password: str) -> str:
    """
    Hashes a plain password.
    """
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a JWT access token.
    'data' should contain the payload (e.g., {"sub": user_email}).
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user_from_db_by_email(db: Session, email: str):
    """
    Helper function to get a user from the database by email.
    """
    return db.query(models.User).filter(models.User.email == email).first()

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    """
    Retrieves the current user from the database based on the provided JWT token.
    Raises HTTPException if the token is invalid or the user is not found.
    Returns the SQLAlchemy User model instance.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None or not isinstance(email, str):
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user_from_db_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: models.User = Depends(get_current_user)
) -> schemas.UserOut:
    """
    Ensures the user is active and returns the public user schema.
    """
    if not bool(current_user.is_active):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return schemas.UserOut.model_validate(current_user)

def verify_password(plain_password, password):
    return pwd_context.verify(plain_password, password)

def authenticate_user(db: Session, email: str, password: str):
    user = crud.get_user_by_email(db, email=email)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user

# async def get_current_active_superuser(
#     current_user: models.User = Depends(get_current_user)
# ) -> schemas.UserOut:
#     """
#     Ensures the user is a superuser and returns the public user schema.
#     """
#     if not bool(current_user.is_superuser):
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN, detail="Not a superuser"
#         )
#     return schemas.UserOut.model_validate(current_user)