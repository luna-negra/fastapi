from asyncio import start_unix_server

import jwt
from datetime import datetime, timedelta, timezone
from typing_extensions import Annotated, Doc

from jwt import PyJWTError
from pydantic import BaseModel, EmailStr
from fastapi import FastAPI, Depends, Request, Response, HTTPException, status, Form
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware


dummy_data: dict = {
    "alex@test.com": {
        "email": "alex@test.com",
        "name": "alex",
        "password": "abc-123",
    },
    "bretta@test.com": {
        "email": "brettta@test.com",
        "name": "bretta",
        "password": "123-abc"
    },
    "charles@test.com": {
        "email": "charles@test.com",
        "name": "charles",
        "password": "def-456"
    },
    "david@test.com": {
        "email": "david@test.com",
        "name": "david",
        "password": "456-deb"
    },
    "emil@test.com": {
        "email": "emil@test.com",
        "name": "emil",
        "password": "abc-456"
    },
    "pavel@test.com": {
        "email": "pavel@test.com",
        "name": "pavel",
        "password": "456-abc"
    }
}

# Initiate FastAPI Instance
app = FastAPI(title="ODIC Test")

# CORS Settings
origins: list = [
    "http://localhost:8000",
    "http://localhost:8001",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:8001"
]

app.add_middleware(
    middleware_class=CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT Setting
SECRET_KEY: str = "ThisIs@SecretkEy"
ALGORITHM: str = "HS256"

# define JWT Token Class
class AuthJWT(BaseModel):
    iss: str = "http://127.0.0.1:8000-tester"
    sub: str
    aud: str = "client-tester_12345"
    isa: int
    exp: int
    email: EmailStr
    name: str

class AccessJWT(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expire: int
    auth_token: str

class CustomPasswordInput:
    def __init__(self,
                 email: Annotated[EmailStr, Form(...,
                                            json_schem_extra={"format": "email"})],
                 password: Annotated[str, Form(...,
                                                json_schema_extra={"format": "password"})]):
        self.email = email
        self.password = password

# function to create and decode token
def create_token(payload: dict):
    return jwt.encode(payload=payload, key=SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str):
    try:
        payload: dict = jwt.decode(jwt=token, key=SECRET_KEY, algorithms=[ALGORITHM])

    except jwt.PyJWTError:
        return None

    return payload

def decode_auth_token(token: str):
    try:
        payload: dict = jwt.decode(jwt=token, key=SECRET_KEY, algorithms=[ALGORITHM], audience="client-tester-12345")

    except PyJWTError:
        return None

    return payload

# Define API
@app.post(path="/oauth/token/",
          tags=["OIDC"],
          summary="Get tokens for auth and access by logging in.",
          response_model=AccessJWT)
#async def login(user_input: UserInput):
async def login(user_input = Depends(CustomPasswordInput)):
    user: dict | None = dummy_data.get(user_input.email) or None
    if user is None or user.get("password") != user_input.password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Mismatch email and password")

    issue_at = datetime.now()
    auth_token_exp = issue_at + timedelta(minutes=5)
    access_token_exp = issue_at + timedelta(minutes=60)

    auth_token_payload: dict = {
        "iss": "http://127.0.0.1:8000-tester",
        "sub": user.get("email"),
        "aud": "client-tester-12345",
        "isa": int(issue_at.timestamp()),
        "exp": int(auth_token_exp.timestamp()),
        "email": user.get("email"),
        "name": user.get("name")
    }

    access_token_payload: dict = {
        "sub": user.get("email"),
        "scope": ["product:read", "product:write"]
    }

    auth_token: str = create_token(payload=auth_token_payload)
    access_token: str = create_token(payload=access_token_payload)
    return AccessJWT(access_token=access_token,
                     expire=int(access_token_exp.timestamp()),
                     auth_token=auth_token)


@app.get(path="/userinfo/",
         tags=["OIDC"],
         summary="OIDC Test - Authenticate User")
async def get_user(id_token: str):  # 사용자 코드에서는 auth_token이므로 id_token으로 파라미터명 그대로 유지
    # AuthJWT의 aud와 decode_auth_token의 audience가 "client-tester-12345"로 일치
    payload = decode_auth_token(token=id_token)  # auth_token을 디코딩하는 함수 사용
    if payload is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid Token")

    # --- ISSUER 검증 로직 수정 ---
    if payload.get("iss") != "http://127.0.0.1:8000-tester":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid Issuer")

    # --- SUB 검증 로직 수정 ---
    # payload.get("sub")가 dummy_data의 키(이메일) 중에 있는지 확인
    if payload.get("sub") not in dummy_data:  # dummy_data.keys() 대신 dummy_data 자체를 사용
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid Account")

    print(payload)
    return AuthJWT(**payload)


@app.get(path="/user/access_scope/",
         tags=["OIDC"],
         summary="Get Accessable Scope for User.")
async def get_user_scope(request: Request):  # Authorization 헤더를 읽기 위해 Request 객체 필요
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Bearer token required")

    access_token = auth_header.split(" ")[1]
    payload = decode_access_token(token=access_token)

    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid Access Token")

    return payload