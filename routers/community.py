from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import schemas, models, crud, auth
from database import get_db
from fastapi import Response

router = APIRouter(
    prefix="",
    tags=["Community"],
)

@router.get("/", response_model=List[schemas.CommunityOut])
def list_communities_route(
    user_id: Optional[str] = Query(None, description="Optional user ID to list communities they are a member of. If not provided, lists popular communities."),
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Retrieve a list of communities. If `user_id` is provided, returns communities
    the specified user is a member of. Otherwise, returns the top popular communities.
    """
    if user_id:
        user = crud.get_user(db, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        communities = crud.get_user_communities(db=db, user_id=user_id)
    else:
        communities_with_member_count = crud.get_popular_communities(db=db, limit=limit)
        # crud.get_popular_communities returns tuples of (Community, total_members),
        communities = [community_obj for community_obj, _ in communities_with_member_count]

    return communities


@router.post("/create/", response_model=schemas.CommunityOut, status_code=status.HTTP_201_CREATED)
def create_community_route(
    community_create: schemas.CommunityCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    Create a new community and automatically make the creator a member.
    """
    existing_community = db.query(models.Community).filter(models.Community.name == community_create.name).first()
    if existing_community:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Community with this name already exists")

    db_community = crud.create_community(db=db, community=community_create)

    membership_data = schemas.MembershipCreate(
        community_id=db_community.id, # type: ignore
        user_id=current_user.id, # type: ignore
        is_admin=True
    )
    crud.create_membership(db=db, membership=membership_data)

    return db_community


@router.get("/{community_id}/details/", response_model=schemas.CommunityOut)
def get_community_details_route(
    community_id: str,
    db: Session = Depends(get_db)
):
    """
    Get details of a specific community, including its member count.
    """
    community = crud.get_community(db=db, community_id=community_id)
    if not community:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community not found")
    
    # member_count = crud.get_community_member_count(db, community_id)
    # return {"community": schemas.CommunityOut.from_orm(community), "member_count": member_count}
    
    return community

@router.post("/{community_id}/join/", response_model=schemas.MembershipOut, status_code=status.HTTP_201_CREATED)
def join_community_route(
    community_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    Allow a user to join a specific community.
    """
    community = crud.get_community(db, community_id)
    if not community:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community not found")

    existing_membership = crud.get_membership_by_community_and_user(db, community_id, current_user.id) # type: ignore
    if existing_membership:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already a member of this community")
    
    membership_data = schemas.MembershipCreate(
        community_id=community_id, # type: ignore
        user_id=current_user.id, # type: ignore
        is_admin=False
    )
    db_membership = crud.create_membership(db=db, membership=membership_data)
    return db_membership

@router.post("/{community_id}/messages/", response_model=schemas.CommunityMessageOut, status_code=status.HTTP_201_CREATED)
def send_community_message_route(
    community_id: str,
    message_create: schemas.CommunityMessageCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    Send a new message to a community.
    """
    community = crud.get_community(db, community_id)
    if not community:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community not found")

    if str(current_user.id) != str(message_create.sender_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to send message as this user")

    if not crud.is_user_community_member(db, current_user.id, community_id): # type: ignore
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not a member of this community")

    db_message = crud.create_community_message(db=db, message=message_create)
    return db_message


@router.post("/messages/{message_id}/replies/", response_model=schemas.ReplyOut, status_code=status.HTTP_201_CREATED)
def send_reply_route(
    message_id: str,
    reply_create: schemas.ReplyCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    Send a reply to a specific community message.
    """
    message = crud.get_community_message(db, message_id)
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")

    if str(current_user.id) != str(reply_create.sender_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to send reply as this user")

    if not crud.is_user_community_member(db, current_user.id, message.community_id): # type: ignore
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not a member of this community")

    db_reply = crud.create_reply(db=db, reply=reply_create)
    return db_reply


@router.get("/{community_id}/discussion/", response_model=List[schemas.CommunityMessageOut])
def get_community_discussion_route(
    community_id: str,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Get paginated discussion (messages and their replies) for a specific community.
    Messages are ordered from newest to oldest.
    """
    community = crud.get_community(db, community_id)
    if not community:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community not found")
    
    messages = crud.get_community_discussion_paginated(db=db, community_id=community_id, skip=skip, limit=limit)
    return messages


@router.get("/{community_id}/users/search/", response_model=List[schemas.UserOut])
def search_community_users_route(
    community_id: str,
    name: Optional[str] = Query(None, description="Partial name to search for users within the community"),
    db: Session = Depends(get_db)
):
    """
    Search for users within a specific community, optionally by name.
    """
    community = crud.get_community(db, community_id)
    if not community:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community not found")

    users = crud.search_users_in_community(db=db, community_id=community_id, name_startswith=name)
    return users

@router.delete("/{community_id}", status_code=status.HTTP_200_OK)
def delete_community_route(
    community_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    community = crud.get_community(db, community_id)
    if not community:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community not found")

    membership = crud.get_membership_by_community_and_user(db, community_id, current_user.id)
    if not membership or not membership.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only community admins can delete a community")

    success = crud.delete_community(db=db, community_id=community_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete community")

    return Response(status_code=status.HTTP_204_NO_CONTENT)
