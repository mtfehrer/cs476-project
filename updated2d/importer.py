from __future__ import annotations

import random
from typing import TYPE_CHECKING

from constants import (
	item_colors,
	IMPORTER_MIN_SHIPMENTS,
	IMPORTER_MAX_SHIPMENTS,
	IMPORTER_MIN_UNITS,
	IMPORTER_MAX_UNITS,
)

if TYPE_CHECKING:
	from warehouse import Warehouse


class Importer:
	def __init__(self, warehouse: Warehouse):
		self.warehouse = warehouse
		self.possible_items = list(item_colors.keys())

	def add_random_item(self) -> None:
		min_shipments, max_shipments = sorted((IMPORTER_MIN_SHIPMENTS, IMPORTER_MAX_SHIPMENTS))
		min_units, max_units = sorted((IMPORTER_MIN_UNITS, IMPORTER_MAX_UNITS))
		shipments = random.randint(min_shipments, max_shipments)
		for _ in range(shipments):
			if not self.warehouse.can_accept_sorter_batch():
				break
			random_item = random.choice(self.possible_items)
			if not self.warehouse.is_relevant_item(random_item):
				continue
			quantity = random.randint(min_units, max_units)
			print(f"Receiving {quantity}x {random_item} from source")
			self.warehouse.receive_incoming_shipment(random_item, quantity)
