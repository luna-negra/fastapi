from datetime import datetime, timedelta
from typing import Annotated
from fastapi import FastAPI, Body, Depends, Query, Path, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.security import HTTPBasic, HTTPBasicCredentials, OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr


dummy_data = {
    1: {"username": "testuser1", "password": "abc123", "first_name": "Alex", "last_name": "Cabassar", "email": "testuser1@company.com", "department": "HR", "is_login": False},
    2: {"username": "testuser2", "password": "123abc", "first_name": "Bretta", "last_name": "Holmes", "email": "testuser2@company.com", "department": "Dev", "is_login": False},
    3: {"username": "testuser3", "password": "def456", "first_name": "Charles", "last_name": "Leclare", "email": "testuser3@company.com", "department": "Sales", "is_login": False},
    4: {"username": "testuser4", "password": "456def", "first_name": "David", "last_name": "Vowie", "email": "testuser4@company.com", "department": "HR", "is_login": False},
    5: {"username": "testuser5", "password": "abc456", "first_name": "Emil", "last_name": "Mueller", "email": "testuser5@company.com", "department": "Engineer", "is_login": False},
    6: {"username": "testuser6", "password": "456abc", "first_name": "Pavel", "last_name": "Hayashi", "email": "testuser6@compay.com", "department": "Dev", "is_login": False}
}

def yield_dummy_data():
    for user in dummy_data.values():
        try:
            yield user
        except Exception as e:
            HTTPException(status_code=500,
                          detail="Yield Users has some problem.")

class UserQ:
    def __init__(self,
                 first_name: str | None = None,
                 last_name: str | None = None,
                 email: EmailStr | None = None,
                 department: str | None = None):
        self.first_name: str | None = f"{first_name[0].upper()}{first_name[1:]}" if first_name is not None else None
        self.last_name: str | None = f"{last_name[0].upper()}{last_name[1:]}" if last_name is not None else None
        self.email: EmailStr | None = email
        self.department: str | None = department

class BasicResponse(BaseModel):
    result: str = "ok"
    msg: str
    count: int | None = None
    data: list | None = None

class UserPasswordInRequest(BaseModel):
    password: str

class UserUsername(BaseModel):
    username: str

class UserLogin(UserPasswordInRequest, UserUsername):
    pass

class UserBasicResponseForm(BaseModel):
    username: str
    first_name: str
    last_name: str
    email: EmailStr
    department: str

class UserRegisterRequestForm(UserPasswordInRequest, UserBasicResponseForm):
    pass


app = FastAPI()
security = HTTPBasic()

@app.get(path="/",
         tags=["Health Check"],
         summary="Main Path for Test.",
         response_model=BasicResponse,
         response_model_exclude_none=True)
async def main():
    return BasicResponse(msg="You can use this API.")

@app.get(path="/users/",
         tags=["Security"],
         summary="Get All User' Basic Info with ID",
         response_model=BasicResponse,
         response_model_exclude_unset=True)
async def get_users(q: Annotated[dict | None, Depends(UserQ)]):
    key: str | None = None
    value: str | None = None
    for k, v in q.__dict__.items():
        if v is not None:
            key = k
            value = v

    if key is None or value is None:
        return BasicResponse(msg="success to get users",
                             count=len(dummy_data),
                             data=[UserBasicResponseForm(**user) for user in yield_dummy_data()])

    result = [ UserBasicResponseForm(**user) for user in yield_dummy_data() if user.get(key).lower() == value.lower() ]
    return BasicResponse(msg="Get User' Information",
                         count=len(result),
                         data=result)

"""
@app.post(path="/user/login/",
          tags=["Security"],
          summary="Login Account.",
          response_model=BasicResponse,
          response_model_exclude_unset=True)
async def user_login(user: Annotated[UserLogin, Body(embed=True)]):
    for u in yield_dummy_data():
        if u.get("username") == user.username and u.get("password") == user.password and not u.get("is_login"):
            u.update({"is_login": True})
            return BasicResponse(msg="Success to Login",
                                 count=1,
                                 data=[UserBasicResponseForm(**u)])

        if u.get("username") == user.username and u.get("is_login"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already Logged In")

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Mismatch username and password.")

@app.post(path="/user/logout/",
          tags=["Security"],
          summary="Logout Account",
          response_model=BasicResponse,
          response_model_exclude_unset=True)
async def user_logout(user: Annotated[UserUsername, Body(embed=True)]):
    for u in yield_dummy_data():
        if u.get("username") == user.username and u.get("is_login"):
            u.update({"is_login": False})
            return BasicResponse(msg="Success to logout",
                                 count=1,
                                 data=[UserBasicResponseForm(**u)])

        if not u.get("is_login"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Already Logged Out.")

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                        detail=f"there is no username {user.username}")
"""

@app.get(path="/user/login/",
          tags=["Security"],
          summary="Login Account",
          response_model=BasicResponse,
          response_model_exclude_unset=True)
async def user_login(user: HTTPBasicCredentials = Depends(security)):
    for u in yield_dummy_data():
        if user.username == u.get("username") and user.password == u.get("password") and not u.get("is_login"):
            u.update({"is_login": True})
            return BasicResponse(msg="Success to login",
                                 count=1,
                                 data=[UserBasicResponseForm(**u)])

        if user.username == u.get("username") and u.get("is_login"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Already logged in.")

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Mismatch username and password.")

# This - Logout process - can not be possible with HTTPBasic.
@app.post(path="/user/logout/",
          tags=["Security"],
          summary="Logout Account - Can not possible with HTTPBasic",
          response_model=BasicResponse,
          response_model_exclude_unset=True,
          deprecated=True)
async def user_logout(username: str):
    for u in yield_dummy_data():
        if username == u.get("username") and u.get("is_login"):
            u.update({"is_login": False})
            return BasicResponse(msg="Success to logout",
                                 count=1,
                                 data=[UserBasicResponseForm(**u)])

        if username == u.get("username") and not u.get("is_login"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Already logged out.")

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                        detail=f"There is no logged in user '{username}'")

### OAuth
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    issue_datetime: datetime = datetime.now()
    expire_datetime: datetime = datetime.now() + timedelta(minutes=15)

@app.post(path="/oauth/token/",
          tags=["OAuth"],
          summary="get OAuth Token for authentication",
          response_model=Token)
async def get_token(account: OAuth2PasswordRequestForm = Depends()):
    for user in yield_dummy_data():
        if user.get("username") == account.username and user.get("password") == account.password:
            return Token(access_token=f"{account.username}_dummy_token")

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Mismatch username and password.")

# get current token: not be used manually
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="oauth/token")
@app.get(path="/user/current",
         tags=["OAuth"],
         summary="Get OAuth token for authorization")
async def get_current_token(token: Annotated[str, Depends(oauth2_scheme)]):
    return {"current_token": token}

