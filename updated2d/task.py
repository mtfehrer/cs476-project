from __future__ import annotations

from typing import Optional

from shelf import Shelf


class Task:
	def __init__(self, shelf: Shelf, item_name: str, quantity: int, is_pickup: bool, follow_up: Optional["Task"] = None, order_id: Optional[int] = None, task_kind: str = "generic"):
		self.shelf = shelf
		self.item_name = item_name
		self.quantity = quantity
		self.is_pickup = is_pickup
		self.follow_up = follow_up
		self.order_id = order_id
		self.task_kind = task_kind
