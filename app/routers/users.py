from typing_extensions import Annotated, Doc
from fastapi import APIRouter, HTTPException, status
from sqlmodel import select
from uuid import UUID

from ..dependencies import DBSession
from ..models.users import UserPublicModel, UserCreateModel, Users, uuid4

router = APIRouter(prefix="/users",
                   tags=["users"])


@router.get(path="/",
            response_model=list[UserPublicModel],
            summary="get all user information")
async def get_all_users(session: DBSession):
    """
    This is a Test

    :param session: DB Session
    :return: list[UserPublicModel]
    """
    return session.exec(select(Users)).all()

@router.get(path="/{uuid}",
            response_model=UserPublicModel,
            summary="get user with uuid")
async def get_user_with_uuid(uuid: Annotated[UUID,
                                             Doc("Input user's unique UUID")],
                             session: DBSession):
    return session.exec(select(Users).where(Users.uuid == uuid)).one_or_none()

@router.post(path="/",
             summary="register new user",
             response_model=UserPublicModel,
             responses={"400": {"details": "Username is already exist"}})
async def register_new_user(user_info: Annotated[UserCreateModel,
                                                 Doc("username, first_name, last_name, birthdate")],
                            session: DBSession):

    user = Users.model_validate(user_info)
    exist_user = session.exec(select(Users).where(Users.username == user.username)).one_or_none()

    if exist_user is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

    user.uuid = uuid4()

    session.add(user)
    session.commit()
    session.refresh(user)
    return UserPublicModel(**user.model_dump())
