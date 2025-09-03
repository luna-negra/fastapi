from datetime import date, datetime
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field, Date, DateTime, Uuid


class UserBasicModel(SQLModel):
    username: str = Field(index=True, unique=True)
    f_name: str = Field(index=True)
    l_name: str = Field(index=True)
    birthdate: date = Field(sa_type=Date)


class UserCreateModel(UserBasicModel):
    password: str = Field(index=True)


class Users(UserCreateModel, table=True):
    uuid: UUID = Field(default=uuid4(), index=True, primary_key=True)
    last_access_dt: datetime = Field(sa_type=DateTime, default_factory=datetime.now)
    registered_dt: datetime = Field(sa_type=DateTime, default=datetime.now())


class UserPublicModel(UserCreateModel):
    uuid: UUID
    username: str
    f_name: str
    l_name: str
    last_access_dt: datetime
    registered_dt: datetime
