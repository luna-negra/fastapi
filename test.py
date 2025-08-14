from fastapi import FastAPI, Depends, HTTPException, status, Path, Query, Body
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import Annotated
from pydantic import BaseModel


app = FastAPI(title="My API Test")

# dummy data
items: dict = {
    1: {"item": "watch", "price": 1000, "manufacturer": "casio"},
    2: {"item": "gaming labtop", "price": 5000, "manufacturer": "toshiba"},
    3: {"item": "chair", "price": 4000, "manufacturer": "IKEA"},
    4: {"item": "tire", "price": 800, "manufacturer": "michelline"}
}



class ResponseForm(BaseModel):
    msg: str = "OK"
    detail: str | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "msg": "result message of calling API.",
                    "detail": "Detail message about result."
                }
            ]
        }
    }

class ItemResponseForm(ResponseForm):
    count: int = 0
    data: dict

    model_config = {**ResponseForm.model_config}
    model_config["json_schema_extra"]["examples"][0].update({"count": "the number of data returned",
                                                             "data": "detail information about data."})

class ItemRequest(BaseModel):
    item: str
    price: int
    manufacturer: str

class ItemManRequest(BaseModel):
    manufacturer: str


@app.get(path="/",
         tags=["Health Check"],
         summary="Validate whether this API can be used or not.",
         response_model=ResponseForm)
async def health_check() -> ResponseForm:
    return ResponseForm(detail="You can use this API.")

@app.get(path="/data/item/{item_id}",
         tags=["Items"],
         summary="Test get method",
        response_model=ItemResponseForm,
         response_model_exclude_unset=False)
async def get_data(item_id: int):
    if item_id not in items.keys():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"There is no item with id {item_id}")
    return ItemResponseForm(msg="OK",
                            detail="Success to get item",
                            data=items[item_id])

@app.post(path="/data/item/",
          tags=["Items"],
          summary="Register new item")
async def add_new_item(item: Annotated[ItemRequest, Body(embed=True)]):
    new_item_id = len(items.keys()) + 1
    try:
        items.update({new_item_id: jsonable_encoder(item)})
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Fail to add new item due to the internal error.")
    return ResponseForm(detail="Success to add new item")

@app.put(path="/data/item/{item_id}",
         tags=["Items"],
         summary="Update registered item")
async def update_item(item_id: Annotated[int, Path(title="item id", gt=0, le=max(items.keys()))],
                      item: Annotated[ItemRequest, Body(#embed=True,
                                                        openapi_examples={
                                                            "normal": {
                                                                "summary": "A normal example",
                                                                "description": "A **normal** item works fine.",
                                                                "value": {
                                                                    "name": "Foo",
                                                                    "price": 35.4,
                                                                    "description": "A very nice Item"
                                                                },
                                                            },
                                                            "invalid_price": {
                                                                "summary": "Invalid price",
                                                                "description": "Item with an invalid price.",
                                                                "value": {
                                                                    "name": "Bar",
                                                                    "price": "not-a-number",
                                                                    "description": "Price is not a number."
                                                                },
                                                            },
                                                        }
                                                        )]):
    if item_id not in items.keys():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"There is no item with id {item_id}")
    items[item_id] = jsonable_encoder(item)
    return ItemResponseForm(detail=f"Success to update item '{item_id}'",
                            data=items[item_id])

@app.patch(path="/data/item/{item_id}",
           tags=["Items"],
           summary="Update only manufacturer for one item")
async def update_manufacturer(item_id: Annotated[int, Path(title="item id", gt=0, le=max(items.keys()))],
                              manufacturer: Annotated[str, Body(embed=True)]):
    items[item_id].update({"manufacturer": manufacturer})
    return ItemResponseForm(detail=f"Success to update manufacturer for item '{item_id}'",
                            data=items[item_id])

@app.delete(path="/data/item/{item_id}",
            tags=["Items"],
            summary="Delete registered item",
            status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: Annotated[int, Path(title="item id", gt=0, le=max(items.keys()))]):
    if item_id not in items.keys():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"There is no item with id {item_id}")
    del items[item_id]
    return None

@app.get(path="/get/items/",
         tags=["Items"],
         summary="redirect test")
async def redirect(redirect: Annotated[bool, Query()] = False):
    return RedirectResponse(url="https://github.com") if redirect else (
        JSONResponse(content={"msg": "ok", "detail": "Not Redirect"}))
