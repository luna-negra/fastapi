from typing import Annotated, Union
from fastapi import FastAPI, Depends, Header, HTTPException
from pydantic import BaseModel


# fake db
fake_items_db = [{"item_name": "Foo"},
                 {"item_name": "Bar"},
                 {"item_name": "Baz"},
                 {"item_name": "Tor"}]

products_list = [
    {"id": 1, "product": "product1", "type": "pc", "public": True},
    {"id": 2, "product": "product2", "type": "smart phone", "public": True},
    {"id": 3, "product": "product3", "type": "pc", "public": False},
    {"id": 4, "product": "product4", "type": "pc", "public": False},
    {"id": 5, "product": "product5", "type": "smart phone", "public": False},
]

class CommonQ:
    def __init__(self, q: Union[str, None] = None, skip: int = 0, limit: int = 100):
        self.q: str = q
        self.skip: int = skip
        self.limit: int = limit

# First Dependency
async def public_dependency(public: bool = True):
    return public

# Second Dependency1
async def range_dependency(public: Annotated[bool, Depends(public_dependency)],
                           start_idx: int = 0,
                           end_idx: int = len(products_list)):
    return {"public": public, "start_idx": start_idx, "end_idx": end_idx}

# Second Dependency2
async def id_dependency(prod_id: int,
                        public: Annotated[bool, Depends(public_dependency)]):
    return {"public": public, "prod_id": prod_id}

####
app = FastAPI(title="Test")

@app.get(path="/class_dependencies", tags=["Dependency"])
async def test_dependencies(common_q: CommonQ = Depends(CommonQ)):
    response: dict = {}
    if common_q.q:
        response.update({"q": common_q.q})

    response.update({"data": fake_items_db[ common_q.skip : common_q.skip + common_q.limit ]})
    return response

@app.get(path="/products/", tags=["Dependency"])
async def get_products(q: Annotated[str, Depends(range_dependency)]):
    response = []
    for p in products_list:
        if q.get("public") and not p.get("public"):
            continue
        response.append(p)

    return {"msg": "ok", "data": response}

@app.delete("/products/{prod_id}", tags=["Dependency"])
async def delete_public_product(prod_id: int, q: Annotated[str, Depends(id_dependency)]):
    if q.get("public"):
        data = None
        for p in products_list:
            if p.get("id") == prod_id and p.get("public"):
                data = p

        if data is not None:
            return {
                "msg": f"deleted data for product {prod_id}",
                "data": data
            }
    return {"msg": f"Fail to delete product id {prod_id}"}

## Dependency Without Returning Value
async def validate_token(x_token: Annotated[str, Header()]):
    if x_token != "fake-super-secret-token":
        raise HTTPException(status_code=400, detail="X_Token Validation Failed.")

async def validate_key(x_key: Annotated[str, Header()]):
    if x_key != "fake-super-secret-key":
        raise HTTPException(status_code=400, detail="X_Key Validation Failed.")
    return x_key

@app.get(path="/users", dependencies=[Depends(validate_token), Depends(validate_key)], tags=["Dependency"])
async def get_users():
    return products_list


# Using yield
class InternalError(Exception):
    pass

def get_username():
    try:
        yield "Rick"
    except InternalError:
        print("We don't swallow the internal error here, we raise again 😎")
        raise

@app.get(path="/items/{item_id}", tags=["Dependency"])
def get_item(item_id: str, username: Annotated[str, Depends(get_username)]):
    if item_id == "portal-gun":
        raise InternalError(
            f"The portal gun is too dangerous to be owned by {username}"
        )
    if item_id != "plumbus":
        raise HTTPException(
            status_code=404, detail="Item not found, there's only a plumbus here"
        )
    return item_id
