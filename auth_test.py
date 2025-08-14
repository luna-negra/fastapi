from typing import Annotated
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr

app = FastAPI(title="Security Test")

oauth_scheme = OAuth2PasswordBearer(tokenUrl="token")

# create user model
class User(BaseModel):
    username: str
    email: EmailStr | None = None
    fullname: str | None = None
    disable: bool | None = None

class UserInDB(User):
    password: str

async def fake_decoded_token(token):
    return User(username=token + "fakedecode",
                email="testuser@test.com",
                fullname="John Doe",
                disable=False)

def get_user(token: Annotated[str, Depends(fake_decoded_token)]):
    return fake_decoded_token(token)


def get_user_activated(user: Annotated[UserInDB, Depends(get_user)]):
    if user is None:
        raise HTTPException(status_code=400, detail="Username and password are not mathed.")
    return user

@app.get(path="/items/", tags=["Security"])
async def read_items(token: Annotated[str, Depends(oauth_scheme)]):
    return {"title": token}

@app.post(path="/token", tags=["Security"])
async def login(user: Annotated[User, Depends(oauth_scheme)]):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized")
    return user

@app.get(path="/current_user/", tags=["Security"])
async def current_user(user: Annotated[UserInDB, Depends(get_user_activated)]):
    return user