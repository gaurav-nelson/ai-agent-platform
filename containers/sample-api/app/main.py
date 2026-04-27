from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="Sample Inventory API",
    description="A demo REST API for the AI Agent API Explorer",
    version="1.0.0",
)

items_db: dict[str, dict] = {
    "1": {"id": "1", "name": "Widget A", "quantity": 100, "price": 9.99},
    "2": {"id": "2", "name": "Widget B", "quantity": 50, "price": 19.99},
    "3": {"id": "3", "name": "Gadget C", "quantity": 200, "price": 4.99},
}


class ItemCreate(BaseModel):
    name: str
    quantity: int
    price: float


class Item(ItemCreate):
    id: str


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/items", response_model=list[Item])
def list_items():
    """List all items in the inventory."""
    return list(items_db.values())


@app.get("/items/{item_id}", response_model=Item)
def get_item(item_id: str):
    """Get a specific item by ID."""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    return items_db[item_id]


@app.post("/items", response_model=Item, status_code=201)
def create_item(item: ItemCreate):
    """Create a new item in the inventory."""
    new_id = str(max(int(k) for k in items_db) + 1) if items_db else "1"
    new_item = {"id": new_id, **item.model_dump()}
    items_db[new_id] = new_item
    return new_item


@app.put("/items/{item_id}", response_model=Item)
def update_item(item_id: str, item: ItemCreate):
    """Update an existing item."""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    items_db[item_id] = {"id": item_id, **item.model_dump()}
    return items_db[item_id]


@app.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: str):
    """Delete an item from the inventory."""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    del items_db[item_id]
