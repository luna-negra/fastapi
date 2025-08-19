import uuid
from typing import Optional
from datetime import datetime, timedelta, timezone
#from jose import jwt, JWTError
import jwt
from jwt import PyJWTError
from typing import Annotated
from fastapi import FastAPI, Depends, HTTPException, status, Response, Request
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
http_scheme = HTTPBasic(scheme_name="HTTP Basic Authorization Test")

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
async def user_login(user: HTTPBasicCredentials = Depends(http_scheme)):
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

"""
### OAuth Example with Token (Simple)
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    issue_datetime: datetime = datetime.now()
    expire_datetime: datetime = datetime.now() + timedelta(minutes=1)

@app.post(path="/oauth/token/",
          tags=["OAuth"],
          summary="get OAuth Token for authentication",
          response_model=Token,
          deprecated=True)
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
         summary="Get OAuth token for authorization",
         deprecated=True)
async def get_current_token(token: Annotated[str, Depends(oauth2_scheme)]):
    return {"current_token": token}
"""

### Session Test
session_storage: dict = {}

@app.post(path="/oauth/login",
          tags=["OAuth Session"],
          response_model=BasicResponse,
          response_model_exclude_unset=True,
          summary="OAuth Login Test")
async def oauth_login(response: Response, req: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    if req.cookies.get("session_id") is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Already Logged In.")

    tmp: dict | None = None
    for user in yield_dummy_data():
        if form_data.username == user.get("username") and form_data.password == user.get("password"):
            if form_data.username not in session_storage.values():
                tmp = user
                break

    if tmp is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Mismatch username and password")

    # store session information in db or in-memory
    session_id: str = str(uuid.uuid4())
    expire_datetime: datetime = datetime.now(timezone.utc) + timedelta(minutes=1)
    session_storage.update({session_id: {"username": tmp.get("username"), "expire_datetime": expire_datetime}})

    # send cookie to client browser
    response.set_cookie(key="session_id", value=session_id, expires=expire_datetime)

    return BasicResponse(msg="Succss to Login")


@app.post(path="/oauth/logout/",
          tags=["OAuth Session"],
          response_model=BasicResponse,
          response_model_exclude_unset=True)
async def oauth_logout(res: Response, req: Request):
    session_id = req.cookies.get("session_id") or None

    # if browser has a session_id in the browser' cookie
    if session_id is not None:# and session_storage.get(session_id).get("expire_datetime") > datetime.now():
        # remove session_id from session_storage
        if session_storage.get(session_id):
            del session_storage[session_id]
        # remove session_id from cookie
        res.delete_cookie(key="session_id")

        return BasicResponse(msg="Success to Logout")

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                        detail="You are already logged out.")


### JWT Test
# JWT requires secret_key and encryption algorithm
# WARNING: SECRET_KEY is required to be called from env var.
SECRET_KEY: str = "DUMMY_SECRET_KEY_FOR_ENCRYPTION"
ALGORITHM: str = "HS256"
# HS: HMAC Symmetric Algorithm
# RS: RSA Asymmetric Algorithm
# ES: ECDSA Asymmetric Algorithm (Ecliptic. more lighter than RS)
# None: Not Recommended.

class JWTToken(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserInDB(BaseModel):
    username: str

# function for creating JWT
def create_jwt_token(username: str):
    # create claims for JWT token data
    # Registered claim: standard for JWT
    # - iss: issuer
    # - sub: subject, who will get this token
    # - aud: receiver' domain or ip
    # - exp: expiration(datetime)
    # Private Claims: customized claims.
    claim_data: dict = {
        "iss": "luna-negra",
        "sub": username,
        "aud": "http://127.0.0.1:8000",    # this claim requires audience argument in jwt.decode.
        "exp": datetime.now() + timedelta(minutes=15)
    }

    # create jwt token with encode method. * claims: dict form data.
    token = jwt.encode(payload=claim_data, key=SECRET_KEY, algorithm=ALGORITHM)
    return token


oauth2_scheme = OAuth2PasswordBearer(scheme_name="OAuth2 Test", tokenUrl="oauth/jwt/login/")

# implement JWT Login and get JWT Token
@app.post(path="/oauth/jwt/login/",
          tags=["JWT"],
          response_model=JWTToken,
          summary="JWT Login Test")
async def oauth_jwt_login(res: Response, account: OAuth2PasswordRequestForm = Depends()):
    for user in yield_dummy_data():
        if account.username == user.get("username") and account.password == user.get("password"):
            # get token by transmitting necessary data
            token = create_jwt_token(username=account.username)
            res.set_cookie(key="jwt", value=token, httponly=True)
            return {"result": "ok", "msg": "success to create token", "access_token": token}

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Mismatch username and password.")

# get user information decode JWT token
async def get_user(req: Request):
    token: str | None = req.cookies.get("jwt") or None
    if token is None:
        token: str = Depends(oauth2_scheme)

    # validate key
    try:
        payload = jwt.decode(jwt=token,
                             key=SECRET_KEY,
                             algorithms=ALGORITHM,
                             audience="http://127.0.0.1:8000")

        if payload.get("sub") is None or payload.get("iss") != "luna-negra":
            raise PyJWTError

    except PyJWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Could not validate credentials",
                            headers={"WWW-Authenticate": "Bearer"})

    # check the aud in token is really exist.
    for user in yield_dummy_data():
        if user.get("username") == payload.get("sub"):
            return UserInDB(username=payload.get("sub"))

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Could not validate credentials",
                        headers={"WWW-Authenticate": "Bearer"})

# GET CURRENT USER with JWT
# protect endpoint by using 'get_user' function
@app.get(path="/oauth/jwt/get_user/",
         tags=["JWT"],
         summary="Get user data using JWT")
async def oauth_read_current_user(current_user: UserInDB = Depends(get_user)):
    return current_user

# Test for Logout with JWT
@app.post(path="/oauth/jwt/logout/",
          tags=["JWT"],
          summary="Test Logout with JWT")
async def oauth_jwt_logout(req: Request, res: Response, current_user: UserInDB = Depends(get_user)):
    token: str | None = req.cookies.get("jwt") or None

    if token is not None:
        res.delete_cookie(key="jwt", httponly=True)
        return {"result": "ok", "msg": "Success to logout"}

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                        detail="You are not logged in.")