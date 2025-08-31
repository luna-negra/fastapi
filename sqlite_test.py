from contextlib import asynccontextmanager
from typing import Annotated, Optional
from pydantic import BaseModel
from fastapi import (FastAPI,
                     Depends,
                     HTTPException,
                     Path,
                     Query,
                     status)
from fastapi.responses import JSONResponse
from sqlmodel import (SQLModel,
                      Field,
                      Session,
                      select,
                      create_engine,
                      func)
from sqlmodel.sql.expression import or_


# Define Table
class HeroInput(BaseModel):
    name: str = Field(index=True, unique=True)
    age: int | None = Field(default=None)
    secret_name: str | None = Field(index=True, default=None)

class HeroUpdateInput(HeroInput):
    name: Optional[str] = None
    age: Optional[int] = None
    secret_name: Optional[str] = None

class Hero(HeroInput, SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)

# Config for sqlite file
SQL_FILE: str = "./sqlite3_test.db"
SQL_URL: str = f"sqlite:///{SQL_FILE}"

# create sqlite engine
engine = create_engine(url=SQL_URL,
                       echo=True,                                     # will print out SQL Query in terminal
                       connect_args={"check_same_thread": False})     # will allow multiple threads (especially in SQLite3)


@asynccontextmanager
async def start_db(app: FastAPI):
    print("Start DB: check database and tables")
    create_db_table()
    yield

    print("--- Termination of DB Session ---")

def create_db_table():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

# create FastAPI instance and run
app = FastAPI(lifespan=start_db)


@app.get(path="/hero/",
         tags=["sqlite_test"],
         summary="Get Hero' Information",
         response_model=list[Hero])
async def get_hero(session: Annotated[Session, Depends(get_session)],
                   name: str | None = None,
                   age: int | None = None,
                   secret_name: str | None = None):
    statement = select(Hero)
    condition: list = []

    if name is not None:
        condition.append(func.lower(Hero.name).like(f"%{name.lower()}%"))

    if age is not None:
        condition.append(Hero.age == age)

    if secret_name is not None:
        condition.append(func.lower(Hero.secret_name).like(f"%{secret_name.lower()}%"))

    if condition:
        statement = select(Hero).where(or_(*condition))

    return session.exec(statement).all()

@app.post(path="/hero/",
          tags=["sqlite_test"],
          summary="Add new hero")
async def add_hero(hero: HeroInput,
                   session: Session = Depends(get_session)):

    # validate input
    hero = Hero.model_validate(hero)

    # check unique value
    exist_hero = session.exec(select(Hero).where(Hero.name==hero.name)).one_or_none()
    if exist_hero is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Already Exist Hero")

    # add to database
    session.add(hero)
    session.commit()
    session.refresh(hero)
    return {"result": "ok",
            "msg": "success to register a new hero",
            "data": hero}


@app.put(path="/hero/{id}",
         tags=["sqlite_test"],
         summary="Update Hero Information")
async def update_hero(id: Annotated[int, Path(gt=0)],
                      hero: HeroUpdateInput,
                      session: Session = Depends(get_session)):
    exist_hero = session.exec(select(Hero).where(Hero.id == id)).one_or_none()
    if exist_hero is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"There is no hero with id '{id}'")

    new_info = hero.model_dump(exclude_unset=True)
    for key, value in new_info.items():
        setattr(exist_hero, key, value)

    session.add(exist_hero)
    session.commit()
    session.refresh(exist_hero)
    return {"result": "ok",
            "msg": "success to update a new hero",
            "data": exist_hero}

@app.delete(path="/hero/{id}",
            tags=["sqlite_test"],
            summary="Delete Hero")
async def delete_hero(id: Annotated[int, Path(gt=0)],
                      session: Session = Depends(get_session)):
    exist_hero = session.exec(select(Hero).where(Hero.id == id)).one_or_none()
    if exist_hero is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"There is no hero with id '{id}'")

    session.delete(exist_hero)
    session.commit()
    return {"result": "ok",
            "msg": "success to remove hero"}