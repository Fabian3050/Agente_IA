from fastapi import APIRouter, HTTPException, Depends
from app.models.item_model import Item
from app.services.item_service import ItemService
from app.repositories.item_repository import ItemRepository

router = APIRouter(
    prefix="/items",
    tags=["items"]
)

# En una aplicación real usaríamos Dependency Injection avanzado o el framework de inyección de FastAPI.
# Para simplicidad, instanciamos aquí un repositorio global.
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
    # Agregamos 'q' a la respuesta para mantener la funcionalidad original de ejemplo
    return {"item": item, "q": q}

@router.post("/")
def create_item(item: Item, svc: ItemService = Depends(get_item_service)):
    created_item = svc.create_item(item)
    return {"item_name": item.name, "message": "Item created successfully", "item_price": item.price, "data": created_item}
