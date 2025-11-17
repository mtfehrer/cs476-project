from shelf import Shelf

class Task:
    def __init__(self, shelf: Shelf, item_name: str, quantity: int, is_pickup: bool):
        self.shelf = shelf
        self.item_name = item_name
        self.quantity = quantity
        self.is_pickup = is_pickup