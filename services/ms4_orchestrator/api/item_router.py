from fastapi import APIRouter, HTTPException, Depends
from models.item_model import Item
from services.item_service import ItemService
from repositories.item_repository import ItemRepository

router = APIRouter(
    prefix="/items",
    tags=["items"]
)

repository = ItemRepository()
service = ItemService(repository)

def get_item_service():
    return service

@router.get("/")
def get_items(svc: ItemService = Depends(get_item_service)):
    return svc.get_all_items()

@router.get("/{item_id}")
def read_item(item_id: int, q: str | None = None, svc: ItemService = Depends(get_item_service)):
    item = svc.get_item_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"item": item, "q": q}

@router.post("/")
def create_item(item: Item, svc: ItemService = Depends(get_item_service)):
    created_item = svc.create_item(item)
    return {"item_name": item.name, "message": "Item created successfully", "item_price": item.price, "data": created_item}
