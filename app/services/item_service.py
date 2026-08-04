from typing import List, Optional
from app.models.item_model import Item
from app.repositories.item_repository import ItemRepository

class ItemService:
    def __init__(self, repository: ItemRepository):
        self.repository = repository

    def get_all_items(self) -> List[dict]:
        return self.repository.get_all()

    def get_item_by_id(self, item_id: int) -> Optional[dict]:
        return self.repository.get_by_id(item_id)

    def create_item(self, item: Item) -> dict:
        # Aquí iría cualquier lógica de negocio (ej. validaciones, cálculos, etc)
        # Por ahora solo llamamos al repositorio
        return self.repository.create(item)
