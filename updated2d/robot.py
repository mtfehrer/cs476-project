import heapq
import random
from typing import Dict, List, Optional, Tuple

from task import Task


class MainRobot:
	def __init__(self, position: Tuple[int, int], robot_id: int, role: str, warehouse, name: Optional[str] = None):
		self.position = position
		self.robot_id = robot_id
		self.role = role
		self.name = name or f"{role.capitalize()} #{robot_id}"
		self.warehouse = warehouse
		self.path: List[Tuple[int, int]] = []
		self.current_order: Optional[Task] = None
		self.inventory: Dict[str, int] = {}
		self.state = "idle"
		self.stalled_steps = 0

	def is_available(self) -> bool:
		return self.state == "idle" and self.current_order is None and not self.path

	def goto(self, target: Tuple[int, int]):
		approach_target = self.warehouse.get_adjacent_path_position(target)
		if approach_target is None:
			print(f"Robot {self.robot_id} cannot find path near {target}")
			self.state = "idle"
			if self.current_order is None:
				self.warehouse.notify_robot_idle(self)
			return
		self.path = self._astar(self.position, approach_target)
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

	def peek_next_step(self) -> Optional[Tuple[int, int]]:
		if self.state == "moving" and self.path:
			return self.path[0]
		return None

	def _astar(self, start: Tuple[int, int], goal: Tuple[int, int]) -> List[Tuple[int, int]]:
		def heuristic(a: Tuple[int, int], b: Tuple[int, int]) -> int:
			return abs(a[0] - b[0]) + abs(a[1] - b[1])

		def get_neighbors(pos: Tuple[int, int]) -> List[Tuple[int, int]]:
			neighbors = []
			for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
				new_r, new_c = pos[0] + dr, pos[1] + dc
				if 0 <= new_r < len(self.warehouse.map_) and 0 <= new_c < len(self.warehouse.map_[0]):
					if self.warehouse.map_[new_r][new_c] == 0 or (new_r, new_c) == goal:
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
	
	def _is_adjacent_to(self, position: Tuple[int, int]) -> bool:
		return abs(self.position[0] - position[0]) + abs(self.position[1] - position[1]) <= 1

	def execute_order(self, order: Task):
		self.current_order = order
		self.goto(order.shelf.position)

	def update(self, should_move: bool, can_move: bool = True):
		if self.state == "moving" and self.path and should_move:
			next_pos = self.path[0]
			print(f"moving to position {next_pos}")

			self.position = next_pos
			self.path = self.path[1:]
			self.stalled_steps = 0

			if not self.path:
				self.state = "idle"
				if self.current_order:
					self._fulfill_order()

	def _fulfill_order(self):
		if not self.current_order:
			return

		order = self.current_order
		if not self._is_adjacent_to(order.shelf.position):
			self.goto(order.shelf.position)
			return

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
				if order.task_kind == "sort":
					self.warehouse.handle_sort_dropoff(order.shelf, order.item_name, order.quantity)

		follow_up = order.follow_up
		if follow_up:
			self.current_order = follow_up
			self.goto(follow_up.shelf.position)
		else:
			self.current_order = None
			self.state = "idle"
			self.warehouse.notify_robot_idle(self)
	
	def _attempt_sidestep(self) -> bool:
		directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
		random.shuffle(directions)
		for dr, dc in directions:
			nr, nc = self.position[0] + dr, self.position[1] + dc
			if not self.warehouse.is_walkable(nr, nc):
				continue
			if self.warehouse.is_position_occupied(nr, nc, exclude_robot=self.robot_id):
				continue
			self.position = (nr, nc)
			print(f"Robot {self.robot_id} sidesteps to {self.position} to avoid collision")
			return True
		return False


class SorterRobot(MainRobot):
	def __init__(self, position: Tuple[int, int], robot_id: int, warehouse, name: Optional[str] = None):
		super().__init__(position, robot_id, "sorter", warehouse, name=name)


class OrderRobot(MainRobot):
	def __init__(self, position: Tuple[int, int], robot_id: int, warehouse, name: Optional[str] = None):
		super().__init__(position, robot_id, "picker", warehouse, name=name)
