from typing import Annotated
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Cookie
from sqlmodel import SQLModel, create_engine, Session


# db config (will be split to config file)
db_type: str = "postgresql"
host: str = "127.0.0.1"
port: int = 5432
username: str = "postgres"
password: str = "password"
db_name: str = "postgres"
db_url = f"{db_type}://{username}:{password}@{host}:{port}/{db_name}"


# inform db tables model
from .models.users import Users

# create db engine
engine = create_engine(url=db_url, echo=True)

# set db startup
@asynccontextmanager
async def startup_db(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield


def get_session():
    with Session(engine) as session:
        yield session

DBSession = Annotated[Session, Depends(get_session)]
