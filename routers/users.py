from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import schemas, models, crud, auth
from database import get_db
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(
    prefix="",
    tags=["Users"],
)

@router.post("/", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def create_user_route(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user.
    """
    existing_user = crud.get_user_by_email(db, email=user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    return crud.create_user(db=db, user=user)


@router.get("/", response_model=List[schemas.UserOut])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Get list of users (for admin or debugging).
    """
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@router.get("/me", response_model=schemas.UserOut)
def read_current_user(current_user: models.User = Depends(auth.get_current_active_user)):
    """
    Get current logged-in user.
    """
    return current_user


@router.get("/{user_id}", response_model=schemas.UserOut)
def read_user(user_id: str, db: Session = Depends(get_db)):
    """
    Get a user by ID.
    """
    db_user = crud.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return db_user


@router.put("/{user_id}", response_model=schemas.UserOut)
def update_user_route(
    user_id: str,
    user_update: schemas.UserBase,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    Update user details by ID. Only the user themselves can update their data.
    """
    db_user = crud.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if str(db_user.id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this user")

    updated_user = crud.update_user(db=db, user_id=user_id, user_update=user_update)
    return updated_user


@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
def delete_user_route(
    user_id: str,
    db: Session = Depends(get_db),
):
    """
    Delete a user by ID (admin only).
    """
    success = crud.delete_user(db=db, user_id=user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"detail": "User deleted successfully"}

@router.post("/token", response_model=schemas.Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token login, used by clients like Swagger UI and Postman.
    
    Returns:
        {"access_token": "JWT_TOKEN", "token_type": "bearer"}
    """
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# @router.post("/token", response_model=schemas.Token)
# def login_for_access_token(
#     login_request: schemas.LoginRequest,
#     db: Session = Depends(get_db)
# ):
#     """
#     OAuth2 compatible token login, used by clients like Swagger UI and Postman.
    
#     Returns:
#         {"access_token": "JWT_TOKEN", "token_type": "bearer"}
#     """
#     user = auth.authenticate_user(db, login_request.username, login_request.password)
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect email or password",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     access_token = auth.create_access_token(data={"sub": user.email})
#     return {"access_token": access_token, "token_type": "bearer"}
