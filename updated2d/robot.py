from typing import Optional, Tuple

from task import Task


class MainRobot:
	def __init__(self, position: Tuple[int, int], robot_id: int, role: str, warehouse, name: Optional[str] = None):
		self.position = position
		self.robot_id = robot_id
		self.role = role
		self.name = name or f"{role.capitalize()} #{robot_id}"
		self.warehouse = warehouse
		self.current_order: Optional[Task] = None
		self.path = []

	def is_available(self) -> bool:
		return True

	def goto(self, target: Tuple[int, int]):
		self.position = target

	def peek_next_step(self) -> Optional[Tuple[int, int]]:
		return None

	def execute_order(self, order: Task):
		self.current_order = order
		self.goto(order.shelf.position)

	def update(self, should_move: bool, can_move: bool = True):
		if self.current_order and should_move:
			self.current_order = None
			self.warehouse.notify_robot_idle(self)


class SorterRobot(MainRobot):
	def __init__(self, position: Tuple[int, int], robot_id: int, warehouse, name: Optional[str] = None):
		super().__init__(position, robot_id, "sorter", warehouse, name=name)


class OrderRobot(MainRobot):
	def __init__(self, position: Tuple[int, int], robot_id: int, warehouse, name: Optional[str] = None):
		super().__init__(position, robot_id, "picker", warehouse, name=name)
