import heapq
from typing import Dict, List, Optional, Tuple

from task import Task


class MainRobot:
	def __init__(self, position: Tuple[int, int], robot_id: int, role: str, warehouse):
		self.position = position
		self.robot_id = robot_id
		self.role = role
		self.warehouse = warehouse
		self.path: List[Tuple[int, int]] = []
		self.current_order: Optional[Task] = None
		self.inventory: Dict[str, int] = {}
		self.state = "idle"

	def is_available(self) -> bool:
		return self.state == "idle" and self.current_order is None and not self.path

	def goto(self, target: Tuple[int, int]):
		self.path = self._astar(self.position, target)
		print("calculated path")
		print(self.path)
		if self.path:
			self.path = self.path[1:]
			if self.path:
				self.state = "moving"
			else:
				self.state = "idle"
				if self.current_order:
					self._fulfill_order()
				else:
					self.warehouse.notify_robot_idle(self)
		else:
			self.state = "idle"
			if self.current_order is None:
				self.warehouse.notify_robot_idle(self)

	def _astar(self, start: Tuple[int, int], goal: Tuple[int, int]) -> List[Tuple[int, int]]:
		def heuristic(a: Tuple[int, int], b: Tuple[int, int]) -> int:
			return abs(a[0] - b[0]) + abs(a[1] - b[1])

		def get_neighbors(pos: Tuple[int, int]) -> List[Tuple[int, int]]:
			neighbors = []
			for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
				new_r, new_c = pos[0] + dr, pos[1] + dc
				if 0 <= new_r < len(self.warehouse.map_) and 0 <= new_c < len(self.warehouse.map_[0]):
					if self.warehouse.map_[new_r][new_c] == 0 or (new_r, new_c) == goal:
						if not self.warehouse.is_position_occupied(new_r, new_c, exclude_robot=self.robot_id):
							neighbors.append((new_r, new_c))
			return neighbors

		frontier = [(0, start)]
		came_from = {start: None}
		cost_so_far = {start: 0}

		while frontier:
			_, current = heapq.heappop(frontier)

			if current == goal:
				break

			for next_pos in get_neighbors(current):
				new_cost = cost_so_far[current] + 1

				if next_pos not in cost_so_far or new_cost < cost_so_far[next_pos]:
					cost_so_far[next_pos] = new_cost
					priority = new_cost + heuristic(next_pos, goal)
					heapq.heappush(frontier, (priority, next_pos))
					came_from[next_pos] = current

		if goal not in came_from:
			return []

		path = []
		current = goal
		while current is not None:
			path.append(current)
			current = came_from[current]
		path.reverse()
		return path

	def execute_order(self, order: Task):
		self.current_order = order
		self.goto(order.shelf.position)

	def update(self, should_move: bool):
		if self.state == "moving" and self.path and should_move:
			next_pos = self.path[0]
			print(f"moving to position {next_pos}")

			if not self.warehouse.is_position_occupied(next_pos[0], next_pos[1], exclude_robot=self.robot_id):
				self.position = next_pos
				self.path = self.path[1:]

				if not self.path:
					self.state = "idle"
					if self.current_order:
						self._fulfill_order()
			else:
				if self.current_order:
					self.goto(self.current_order.shelf.position)

	def _fulfill_order(self):
		if not self.current_order:
			return

		order = self.current_order

		if order.is_pickup:
			if order.shelf.remove_item(order.item_name, order.quantity):
				self.inventory[order.item_name] = self.inventory.get(order.item_name, 0) + order.quantity
				print(f"Robot {self.robot_id} picked up {order.quantity}x {order.item_name}")
				if order.task_kind == "sort":
					self.warehouse.handle_sort_pickup_complete(order)
		else:
			if order.item_name in self.inventory and self.inventory[order.item_name] >= order.quantity:
				order.shelf.add_item(order.item_name, order.quantity)
				self.inventory[order.item_name] -= order.quantity
				if self.inventory[order.item_name] == 0:
					del self.inventory[order.item_name]
				print(f"Robot {self.robot_id} dropped off {order.quantity}x {order.item_name}")
				if order.order_id is not None:
					self.warehouse.record_order_fulfillment(order.order_id, order.item_name, order.quantity)

		follow_up = order.follow_up
		if follow_up:
			self.current_order = follow_up
			self.goto(follow_up.shelf.position)
		else:
			self.current_order = None
			self.state = "idle"
			self.warehouse.notify_robot_idle(self)


class SorterRobot(MainRobot):
	def __init__(self, position: Tuple[int, int], robot_id: int, warehouse):
		super().__init__(position, robot_id, "sorter", warehouse)


class OrderRobot(MainRobot):
	def __init__(self, position: Tuple[int, int], robot_id: int, warehouse):
		super().__init__(position, robot_id, "picker", warehouse)
