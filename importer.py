import random
from shelf import Shelf
from constants import item_colors


class Importer:
	def __init__(self):
		self.possible_items = list(item_colors.keys())
	
	def add_random_item(self, shelf: Shelf) -> None:
		random_item = self.possible_items[random.randint(0, len(self.possible_items) - 1)]
		print(f"Adding a random item")
		shelf.add_item(random_item, random.randint(1, 5))
