from fastapi import FastAPI, Depends, Body, Query, Path, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, AfterValidator
from typing import Annotated

dummy_items = [
    {"id": 1, "product": "cellphone", "price": 1000, "manufacturer": "NOKIA"},
    {"id": 2, "product": "labtop", "price": 2500, "manufacturer": "Lenovo"},
    {"id": 3, "product": "smartphone", "price": 1100, "manufacturer": "Apple"},
    {"id": 4, "product": "smartphone", "price": 900, "manufacturer": "Samsung"},
    {"id": 5, "product": "cellphone", "price": 500, "manufacturer": "Blackberry"},
    {"id": 6, "product": "labtop", "price": 600, "manufacturer": "ASUS"},
    {"id": 7, "product": "labtop", "price": 700, "manufacturer": "ASUS"},
    {"id": 8, "product": "smartphone", "price": 600, "manufacturer": "Shaomi"},
    {"id": 9, "product": "HDD", "price": 200, "manufacturer": "Toshiba"},
]

max_id : int = 9

def check_item_id(item_id: int):
    if item_id > max_id or item_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"item_id is over the range.")
    return item_id

def search_item(item_id: int) -> dict:
    for i in dummy_items:
        if i.get("id") == item_id:
            return i

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"There is no item with id '{item_id}'")


def query_f(q: str | None, start_idx: int = 0, end_idx: int = max_id ):
    return {"q": q, "start_idx": start_idx, "end_idx": end_idx}


class QueryF:
    def __init__(self, q: str | None, start_idx: int = 0, end_idx: int = 0):
        self.q = q
        self.start_idx = start_idx
        self.end_idx = end_idx

class ItemResponse(BaseModel):
    product: str
    price: int
    manufacturer: str

class ItemRequest(ItemResponse):
    id: int


item_id_validator = Annotated[int, Depends(check_item_id)]

app = FastAPI(title="Dependency Test")

@app.get(path="/items/",
         tags=["Items"],
         summary="get all items",
         response_model=list[ItemResponse])
async def get_all_items(commons=Depends(QueryF)):
    if commons.q is None:
        return dummy_items

    result = []
    for i in dummy_items:
        if i.get("product") == commons.q:
            result.append(i)

    return result

@app.get(path="/items/{item_id}/",
         tags=["Items"],
         summary="get item for specific id",
         response_model=ItemResponse)
async def get_item(item_id: item_id_validator):
    return ItemResponse(**search_item(item_id=item_id))


@app.put(path="/items/{item_id}/",
         tags=["Items"],
         summary="update item for specific id",
         response_model=ItemResponse)
async def update_item(item_id: item_id_validator,
                      item: Annotated[ItemResponse, Body(embed=True)]):
    returned_item = search_item(item_id=item_id)
    returned_item.update(**jsonable_encoder(item))
    return returned_item

@app.delete(path="/items/{item_id}/",
            tags=["Items"],
            status_code=status.HTTP_202_ACCEPTED,
            summary="Delete registered item")
async def delete_item(item_id: item_id_validator):
    returned_item = search_item(item_id=item_id)
    del dummy_items[dummy_items.index(returned_item)]
    return JSONResponse(content={"result": "ok", "msg": f"Success to remove item id '{item_id}'"})
