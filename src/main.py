from fastapi import FastAPI
import uvicorn
from typing import Union
from pydantic import BaseModel


class Item(BaseModel):
    name: str
    price: float
    is_offer: Union[bool, None] = None


app = FastAPI(
    title="Тестовое API",
    description="Тестовое описание API. Можно использовать **Markdown**.",
    version="1.0.0",
    terms_of_service="https://example.com/terms/",
    contact={
        "name": "Коцоев Герман",
        "url": "https://example.com/contact",
        "email": "gef3dx@gmail.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)


@app.get("/")
async def index():
    return {
        "Hello": "World",
    }


@app.get("/items/{item_id}")
async def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item):
    return {"item_name": item.name, "item_id": item_id}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
