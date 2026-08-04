from typing import List, Optional
from app.models.item_model import Item

class ItemRepository:
    def __init__(self):
        # En una app real esto sería una conexión a base de datos
        self.items_db = {}
        self.current_id = 1

    def get_all(self) -> List[dict]:
        return [{"id": k, **v.model_dump()} for k, v in self.items_db.items()]

    def get_by_id(self, item_id: int) -> Optional[dict]:
        item = self.items_db.get(item_id)
        if item:
            return {"id": item_id, **item.model_dump()}
        return None

    def create(self, item: Item) -> dict:
        item_id = self.current_id
        self.items_db[item_id] = item
        self.current_id += 1
        return {"id": item_id, **item.model_dump()}
