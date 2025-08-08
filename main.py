import re
from typing import Annotated
from enum import Enum
from fastapi import (FastAPI,
                     Body,
                     Path,
                     Query,
                     Cookie,
                     Header,
                     Response,
                     Form,
                     UploadFile,
                     File,
                     HTTPException,
                     status)
from dataclasses import dataclass
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import (BaseModel,
                      AfterValidator,
                      HttpUrl,
                      EmailStr)


class OSType(Enum):
    windows = "windows"
    mac = "mac"
    linux = "linux"

data = [{"type": "pc", "product": "Thinkpad"},
        {"type": "pc", "product": "Xenon"},
        {"type": "cellphone", "product": "Iphone14"},
        {"type": "cellphone", "product": "GalaxyS25"}]

class Data(BaseModel):
    name: str
    age: int
    nation: str
    birth_year: int
    birth_month: int
    birth_day: int
    description: str | None = None

class Item(BaseModel):
    item_id: int
    name: str
    product: str
    description: str | None = None

class User(BaseModel):
    user_id: int
    username: str
    test: set[str] = set()
    test2: dict[str, int] = {}

class Image(BaseModel):
    name: str
    url: HttpUrl

app = FastAPI()

"""
@app.get(path="/")
async def main() -> dict:
    return {"msg": "Hello FastAPI"}
"""

@app.get(path="/items/{item_id}")
async def get_item(item_id: int) -> dict:
    return {"msg": "OK", "id": f"{item_id}"}

@app.get(path="/os/{os_type}")
async def get_os(os_type: OSType):
    if os_type in (OSType.windows, OSType.mac, OSType.linux):
        return {"msg": "OK", "OS": os_type}

    return {"msg": "ERROR", "OS": None}

@app.get(path="/file/{file_path:path}")
async def get_file(file_path) -> dict:
    return {"msg": "OK", "file_path": file_path}

@app.get(path="/product")
async def get_product(start_idx: int = 0, end_idx: int = 10):
    return {"msg": "OK",
            "data": data[start_idx:end_idx]}

@app.get(path="/user")
async def get_user(username:str):
    return {"msg": "OK", "username": username}

"""
@app.get("/items")
async def get_items(q: Annotated[str | None, Query(include_in_schema=True)] = None) -> dict:
    result = {"items": [{"item_id": 10}, {"item_id": 11}]}
    if q:
        result.update({"q": q})
    return result
"""

def validate_p_type(p_type: str):
    if p_type not in ("pc", "cellphone"):
        raise ValueError("Value Error Test")
    return p_type

@app.get(path="/items")
async def get_items(p_type: Annotated[str, AfterValidator(validate_p_type)]):
    result = {"msg": "OK", "data": []}
    for d in data:
        if p_type == d["type"]: result["data"].append(d)
    return result

# test
@app.get("/items/{item_id}")
async def read_items(q: str, item_id: Annotated[int, Path(title="The ID of the item to get", ge=1)]):
    results = {"item_id": item_id}
    if q:
        results.update({"q": q})
    return results

@app.post(path="/items")
async def send_data(userdata: Data):
    return userdata

# Add Key for Single Body
@app.put(path="/item/{item_id}")
async def change_item(item_id: Annotated[int, Path(title="item's id", ge=0)],
                      item: Annotated[Item, Body(embed=True)]):
    return {"item_id": item_id, "item": item}

# Multiple Bodies
@app.put(path="/items2/{item_id}")
async def change_item2(item_id: Annotated[int, Path(title="item's id", ge=0)],
                       item: Item,
                       user: User):
    return {"item_id": item_id, "item": item, "user": user}

@app.post(path="/image/")
async def upload_image(image: Image):
    return {"msg": "ok", "image": image}

# Define Example (Metadata)

class Developer(BaseModel):
    name: str
    email: EmailStr
    github: HttpUrl

    # set model_config to express how to write this body
    """
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Input Your Name",
                    "email": "Input Your Email: username@id_or_domain",
                    "github": "Input your Github: https://github.com/USERNAME"
                }
            ]
        }
    }
    """

class Product(BaseModel):
    name: str
    version: float
    developer: Developer

@app.get(path="/app/{program_id}")
async def get_app(program_id: Annotated[int, Path(title="app id", ge=0)],
                  dev: Developer,
                  product: Product):
    return {"msg": "ok", "dev": dev, "product": product}


@app.post(path="/app/{app_id}")
async def add_app(app_id: Annotated[int, Path],
                  app: Annotated[Developer, Body(openapi_examples={
                          "normal": {
                                  "summary": "A normal example",
                                  "description": "get application information",
                                  "value": {
                                      "name": "App Name",
                                      "version": 0.1,
                                      "developer": {
                                          "name": "Dev Name",
                                          "email": "user@domain_addr",
                                          "github": "https://github.com/USERNAME"
                                      }
                                  }
                          },
                          "converted": {
                                  "summary": "Type Casting Information",
                                  "description": "version with string would be converted into float",
                                  "value": {
                                      "version": "0.1"
                                  }
                          },
                              "invalid": {
                                  "summary": "Invalid Response",
                                  "description": "If there is an error.",
                                  "value": {
                                      "summary": "Invalid data is rejected with an error",
                                            "value": {
                                                "name": "Baz",
                                                "version": "test",
                                            },
                                  }
                              }
                      })]):
    return {"msg": "ok", "app": app}

@app.get(path="/os/")
async def get_all_os(session_id: Annotated[str | None, Cookie()] = None):
    return {"msg": "ok", "result": "Cookie Test"}


class HeaderTemplate(BaseModel):
    accept: str
    user_agent: str
    x_tag: list[str] = []

@app.get(path="/")
async def main(header: Annotated[HeaderTemplate, Header()]):
    return {"msg": "ok", "header": header}

class LoginResult1(BaseModel):
    username: str

class LoginResult2(BaseModel):
    username: str
    age: int | None = None

class LoginTemplate(BaseModel):
    username: str
    password: str

@app.post(path="/login/", tags=["users"], response_model=LoginResult1)
async def login1(user: LoginTemplate):
    return user

@app.post(path="/login2/", tags=["users"],response_model=LoginResult2)
async def login2(user: LoginTemplate) -> LoginTemplate:
    return user

# Return Response
@app.get(path="/response")
async def response(redirect: bool = False) -> Response:
    url = "https://github.com"
    return RedirectResponse(url=url) if redirect else JSONResponse(content={"msg": "ok", "url": url})


class ExcludeItem(BaseModel):
    name: str
    price: float
    tax_percentage: int
    description: str | None = None

@app.get(path="/exclude_field", response_model=ExcludeItem, response_model_exclude_unset=True)
async def get_item() -> ExcludeItem:
    return ExcludeItem(name="product1", price=10.2, tax_percentage=2)


# Form Data and Files
class LoginInput(BaseModel):
    username: str | None = None
    password: str | None = None
    model_config = {"extra": "forbid"}

class LoginResult(LoginInput):
    result: str = "OK"
    message: str = "Login Success"
    session: str | None = None

@app.post(path="/form_login",
          tags=["users"],
          response_model=LoginResult,
          response_model_exclude={"username", "password"},
          response_model_exclude_unset=True)
async def legacy_login(login_input: Annotated[LoginInput, Form()]):
    if login_input.username == "testuser" and login_input.password == "P@ssw0rd":
        return LoginResult(session="R@ndl0mV@1ue")
    return LoginResult(result="Fail",
                       message="Fail to Login")

@app.post(path="/upload_file", tags=["files"])
async def upload_file(file: UploadFile):
    return {"msg": "ok", "filename": file.filename, "size": file.size}

@app.post("/upload_file2/", tags=["files"])
async def create_file(file: Annotated[bytes, File()]):
    if not file:
        return {"message": "No file sent"}
    else:
        return {"file_size": len(file)}

@app.post(path="/upload_files", tags=["files"])
async def upload_multiple_files(files: list[UploadFile]):
    return {"msg": "ok", "filenames": [ f.filename for f in files ]}

@app.post(path="/upload_files2", tags=["files"])
async def upload_multiple_files2(files: Annotated[list[bytes], File()]):
    return {"msg": "ok", "filesize": [ len(f) for f in files ]}

# HTTPException
regex_dt = re.compile(r"^\d{4}-\d{1,2}-\d{1,2}$")
@app.get(path="/get_data/{date}")
async def get_data(date: str):
    if not regex_dt.match(date):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Date must be 'yyyy-mm-dd'.")
    return {"msg": "ok", "data": date}
