from contextlib import asynccontextmanager
from typing import Annotated, Optional
from fastapi import FastAPI, HTTPException, Depends, Path, status
from sqlmodel import SQLModel, Session, Field, create_engine, select
from fastapi.responses import JSONResponse
from pydantic import BaseModel


# define table named 'Hero'
class HeroInput(BaseModel):
    name: str = Field(index=True, unique=True)
    age: int | None = Field(default=None)
    secret_name: str = Field(index=True)

class HeroInputUpdate(HeroInput):
    name: Optional[str] = None
    age: Optional[int] = None
    secret_name: Optional[str] = None

class Hero(HeroInput, SQLModel, table=True):
    """
    table: this model class is for table.
    """
    id: int | None = Field(primary_key=True, default=None)   # Auto Increment (primary_key and default None)


# set vars for PostgreSQL DB connection
host: str = "127.0.0.1"
port: int = 5432
username: str = "postgres"
password: str = "password"
db_name: str = "postgres"

# create sql engine
postgresql_url: str = f"postgresql://{username}:{password}@{host}:{port}/{db_name}"
engine = create_engine(url=postgresql_url)


# define function to create database and table
def create_db_and_table():
    SQLModel.metadata.create_all(engine)

# define function to get session
def get_session():
    with Session(engine) as session:
        yield session

# define function to set action at startup
@asynccontextmanager
async def startup_event(app: FastAPI):
    print("Start Server and Create DB / Table...")
    create_db_and_table()
    yield
    print("This code will be executed after terminating server.")

# create FastAPI instance
app = FastAPI(lifespan=startup_event)


@app.get(path="/hero/",
         tags=["DB Test"],
         response_model=list[Hero],
         summary="Get All Hero Information")
async def get_hero(name: str | None = None,
                   age: int | None = None,
                   secret_name: str | None = None,
                   session: Session = Depends(get_session)) -> list[Hero]:
    heros = session.exec(statement=select(Hero)).all()
    return heros

@app.post(path="/hero/",
          tags=["DB Test"],
          summary="Register New Hero")
async def add_hero(hero: HeroInput,
                   session: Session = Depends(get_session)):

    # hero = Hero(**hero.__dict__)         # this code will bypass pydantic validation logic
    hero = Hero.model_validate(hero)
    check_exist = session.exec(select(Hero).where(Hero.name==hero.name)).one_or_none()

    if check_exist is not None:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content={"result": "Fail", "msg": "Already Exist Name"})

    session.add(hero)
    session.commit()
    session.refresh(hero)       # update current referenced table
    return {"result": "OK", "data": hero}


@app.delete(path="/hero/{id}",
            summary="Delete hero with id",
            tags=["DB Test"])
async def delete_hero(id: Annotated[int, Path(gt=0)],
                      session: Session = Depends(get_session)):

    exist_hero = session.exec(select(Hero).where(Hero.id==id)).one_or_none()
    if exist_hero is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"No Hero Exist with id '{id}'")

    session.delete(exist_hero)
    session.commit()
    session.delete(exist_hero)
    return {"result": "OK"}


@app.put(path="/hero/{id}",
         summary="Update hero",
         tags=["DB Test"])
async def update_hero(id: Annotated[int, Path(ge=1)],
                      hero: HeroInputUpdate,
                      session: Session = Depends(get_session)):
    exist_hero = session.exec(select(Hero).where(Hero.id==id)).one_or_none()
    if exist_hero is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"No Hero Exist with id '{id}'")

    update_data = hero.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(exist_hero, key, value)

    session.add(exist_hero)
    session.commit()
    session.refresh(exist_hero)
    return {"result": "OK"}
