from typing import List, Optional
from models.item_model import Item
from repositories.item_repository import ItemRepository

class ItemService:
    def __init__(self, repository: ItemRepository):
        self.repository = repository

    def get_all_items(self) -> List[dict]:
        return self.repository.get_all()

    def get_item_by_id(self, item_id: int) -> Optional[dict]:
        return self.repository.get_by_id(item_id)

    def create_item(self, item: Item) -> dict:
        return self.repository.create(item)
