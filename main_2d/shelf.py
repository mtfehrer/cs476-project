from typing import Dict, Tuple

class Shelf:
    
    def __init__(self, position: Tuple[int, int], items: Dict[str, int] = None):
        self.position = position
        self.items = items if items is not None else {}
    
    def add_item(self, item_name: str, quantity: int):
        if item_name in self.items:
            self.items[item_name] += quantity
        else:
            self.items[item_name] = quantity
    
    def remove_item(self, item_name: str, quantity: int) -> bool:
        if item_name not in self.items or self.items[item_name] < quantity:
            return False
        
        self.items[item_name] -= quantity
        if self.items[item_name] == 0:
            del self.items[item_name]
        return True
    
    def get_quantity(self, item_name: str) -> int:
        return self.items.get(item_name, 0)