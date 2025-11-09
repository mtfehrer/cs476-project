from shelf import Shelf

class Order:
    def __init__(self, shelf: Shelf, item_name: str, quantity: int, is_pickup: bool):
        self.shelf = shelf
        self.item_name = item_name
        self.quantity = quantity
        self.is_pickup = is_pickup