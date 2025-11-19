from __future__ import annotations

from typing import Dict, Iterable, List, Tuple


class Order:
	def __init__(self, order_id: int, line_items: Iterable[Tuple[str, int]]):
		self.id = order_id
		self.line_items: Dict[str, int] = {}
		for item_name, quantity in line_items:
			if quantity <= 0:
				continue
			self.line_items[item_name] = self.line_items.get(item_name, 0) + quantity
		self.remaining: Dict[str, int] = dict(self.line_items)

	@property
	def total_units(self) -> int:
		return sum(self.line_items.values())

	def register_fulfillment(self, item_name: str, quantity: int) -> None:
		if item_name not in self.remaining:
			return
		new_value = max(0, self.remaining[item_name] - quantity)
		self.remaining[item_name] = new_value

	def is_complete(self) -> bool:
		return all(quantity == 0 for quantity in self.remaining.values())

	def describe(self) -> str:
		parts: List[str] = []
		for item_name, quantity in self.line_items.items():
			parts.append(f"{quantity}x {item_name}")
		return ", ".join(parts)
