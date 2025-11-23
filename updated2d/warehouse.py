from collections import deque, Counter
from typing import List, Dict, Tuple, Optional, Set

from shelf import Shelf
from robot import MainRobot, OrderRobot, SorterRobot
from task import Task
import random
from constants import font, item_colors, SORTER_MAX_PENDING_BATCHES
from order import Order

class Warehouse:
	def __init__(self, map_layout: List[List[int]], item_home_locations: Optional[Dict[str, Tuple[int, int]]] = None, shipping_station_positions: Optional[List[Tuple[int, int]]] = None, receiving_station_positions: Optional[List[Tuple[int, int]]] = None):
		self.map_ = map_layout
		self.shelves: Dict[Tuple[int, int], Shelf] = {}
		self.robots: List[MainRobot] = []
		self.orders: Dict[int, Order] = {}
		self.next_order_id = 1
		self.item_home_locations = item_home_locations or {}
		self.sort_task_queue = deque()
		self.order_task_queue = deque()
		self.shipping_stations: List[Shelf] = []
		self.receiving_stations: List[Shelf] = []
		self.shipping_station_positions: Set[Tuple[int, int]] = set()
		self.receiving_station_positions: Set[Tuple[int, int]] = set()
		self.receiving_transfer_tasks: Dict[Tuple[Tuple[int, int], str], Task] = {}
		self.order_shipping_assignments: Dict[int, Shelf] = {}
		self.order_pickup_unlocked = True
		if shipping_station_positions:
			for position in shipping_station_positions:
				station = Shelf(position)
				self.shipping_stations.append(station)
				self.shipping_station_positions.add(position)
		if receiving_station_positions:
			for position in receiving_station_positions:
				station = Shelf(position)
				self.receiving_stations.append(station)
				self.receiving_station_positions.add(position)
		
		for i in range(len(self.map_)):
			for j in range(len(self.map_[0])):
				if self.map_[i][j] == 1:
					self.shelves[(i, j)] = Shelf((i, j))
	
	def add_robot(self, position: Tuple[int, int], role: str = "sorter", name: Optional[str] = None) -> MainRobot:
		robot_id = len(self.robots)
		robot = self._create_robot_instance(position, robot_id, role, name)
		self.robots.append(robot)
		self._assign_task_to_robot(robot)
		return robot

	def _create_robot_instance(self, position: Tuple[int, int], robot_id: int, role: str, name: Optional[str]) -> MainRobot:
		if role == "sorter":
			return SorterRobot(position, robot_id, self, name=name)
		if role in ("picker", "order"):
			return OrderRobot(position, robot_id, self, name=name)
		return MainRobot(position, robot_id, role, self, name=name)

	def stock_shelf(self, position: Tuple[int, int], item_name: str, quantity: int) -> None:
		shelf = self.shelves.get(position)
		if shelf is None:
			raise ValueError(f"Shelf at position {position} does not exist")
		shelf.add_item(item_name, quantity)
		self.handle_item_added(shelf, item_name, quantity)

	def receive_incoming_shipment(self, item_name: str, quantity: int) -> None:
		if quantity <= 0:
			return
		receiving_station = self._select_station(self.receiving_stations)
		if not receiving_station:
			print("No receiving station configured; stocking directly")
			home_position = self.item_home_locations.get(item_name)
			if home_position and home_position in self.shelves:
				self.stock_shelf(home_position, item_name, quantity)
			return
		receiving_station.add_item(item_name, quantity)
		self._queue_incoming_sort(receiving_station, item_name, quantity)

	def _queue_incoming_sort(self, source: Shelf, item_name: str, quantity: int) -> None:
		home_position = self.item_home_locations.get(item_name)
		if not home_position:
			return
		destination_shelf = self.shelves.get(home_position)
		if destination_shelf is None:
			return
		self._queue_receiving_transfer(source, destination_shelf, item_name)

	def _queue_receiving_transfer(self, source: Shelf, destination: Shelf, item_name: str) -> None:
		total_quantity = source.get_quantity(item_name)
		if total_quantity <= 0:
			return
		key = (source.position, item_name)
		existing_task = self.receiving_transfer_tasks.get(key)
		if existing_task:
			if total_quantity > existing_task.quantity:
				existing_task.quantity = total_quantity
				if existing_task.follow_up:
					existing_task.follow_up.quantity = total_quantity
			return
		pickup_task = self._queue_transfer_task(source, destination, item_name, total_quantity, task_kind="sort")
		self.receiving_transfer_tasks[key] = pickup_task

	def handle_item_added(self, shelf: Shelf, item_name: str, quantity: int) -> None:
		if quantity <= 0:
			return
		if shelf.position in self.shipping_station_positions:
			return
		if shelf.position in self.receiving_station_positions:
			return
		home_position = self.item_home_locations.get(item_name)
		if not home_position or home_position == shelf.position:
			return
		destination_shelf = self.shelves.get(home_position)
		if destination_shelf is None:
			return
		self._queue_transfer_task(shelf, destination_shelf, item_name, quantity)

	def _queue_transfer_task(self, source: Shelf, destination: Shelf, item_name: str, quantity: int, task_kind: str = "sort") -> Task:
		pickup_task = Task(source, item_name, quantity, is_pickup=True, task_kind=task_kind)
		dropoff_task = Task(destination, item_name, quantity, is_pickup=False, task_kind=task_kind)
		pickup_task.follow_up = dropoff_task
		self.sort_task_queue.append(pickup_task)
		self._assign_tasks()
		return pickup_task

	def _station_load(self, station: Shelf) -> int:
		return sum(station.items.values())

	def _select_station(self, stations: List[Shelf]) -> Optional[Shelf]:
		if not stations:
			return None
		return min(stations, key=self._station_load)

	def can_accept_sorter_batch(self) -> bool:
		if SORTER_MAX_PENDING_BATCHES <= 0:
			return True
		active_sorters = sum(
			1
			for robot in self.robots
			if robot.role == "sorter" and robot.current_order is not None
		)
		return (len(self.sort_task_queue) + active_sorters) < SORTER_MAX_PENDING_BATCHES

	def is_relevant_item(self, item_name: str) -> bool:
		return item_name in self.item_home_locations

	def _find_shelf_with_item(self, item_name: str) -> Optional[Shelf]:
		home_position = self.item_home_locations.get(item_name)
		if home_position and home_position in self.shelves:
			return self.shelves[home_position]
		return next((shelf for shelf in self.shelves.values() if shelf.get_quantity(item_name) > 0), None)

	def _normalize_order_items(self, order_items) -> List[Tuple[str, int]]:
		if isinstance(order_items, tuple):
			order_items = [order_items]
		normalized: List[Tuple[str, int]] = []
		for entry in order_items:
			if not entry or len(entry) != 2:
				continue
			item_name, quantity = entry
			if quantity <= 0:
				continue
			normalized.append((item_name, quantity))
		return normalized

	def create_user_order(self, order_items) -> bool:
		normalized_items = self._normalize_order_items(order_items)
		if not normalized_items:
			print("Invalid order request")
			return False
		shipping_station = self._select_station(self.shipping_stations)
		if not shipping_station:
			print("No shipping station configured")
			return False
		prepared_lines: List[Tuple[str, int, Shelf]] = []
		for item_name, quantity in normalized_items:
			source_shelf = self._find_shelf_with_item(item_name)
			if not source_shelf:
				continue
			prepared_lines.append((item_name, quantity, source_shelf))
		if not prepared_lines:
			return False
		order_id = self.next_order_id
		self.next_order_id += 1
		order = Order(order_id, [(item, quantity) for item, quantity, _ in prepared_lines])
		self.orders[order_id] = order
		print(f"Queued order #{order_id} for {order.describe()}")
		self._queue_order_tasks(order_id, prepared_lines, shipping_station)
		return True

	def _queue_order_tasks(self, order_id: int, prepared_lines: List[Tuple[str, int, Shelf]], shipping_station: Shelf) -> None:
		self.order_shipping_assignments[order_id] = shipping_station
		for item_name, quantity, source_shelf in prepared_lines:
			pickup_task = Task(source_shelf, item_name, quantity, is_pickup=True, order_id=order_id, task_kind="order")
			dropoff_task = Task(shipping_station, item_name, quantity, is_pickup=False, order_id=order_id, task_kind="order")
			pickup_task.follow_up = dropoff_task
			self.order_task_queue.append(pickup_task)
		self._assign_tasks()

	def record_order_fulfillment(self, order_id: int, item_name: str, quantity: int) -> None:
		order = self.orders.get(order_id)
		if not order:
			return
		order.register_fulfillment(item_name, quantity)
		if order.is_complete():
			shipping_shelf = self.order_shipping_assignments.pop(order_id, None)
			if shipping_shelf:
				for line_item, line_quantity in order.line_items.items():
					available = shipping_shelf.get_quantity(line_item)
					if available <= 0:
						continue
					to_remove = min(line_quantity, available)
					shipping_shelf.remove_item(line_item, to_remove)
			print(f"Order #{order_id} packed and cleared from order shelf")
			del self.orders[order_id]
	
	def _has_open_order_for_item(self, item_name: str) -> bool:
		for order in self.orders.values():
			if order.remaining.get(item_name, 0) > 0:
				return True
		return False
	
	def unlock_order_pickup(self) -> None:
		if self.order_pickup_unlocked:
			return
		self.order_pickup_unlocked = True
		print("Order pickup unlocked; dispatching picker tasks")
		self._assign_tasks()

	def handle_sort_dropoff(self, shelf: Shelf, item_name: str, quantity: int) -> None:
		if quantity <= 0:
			return
		if self._has_open_order_for_item(item_name):
			return
		shipping_station = self._select_station(self.shipping_stations)
		if not shipping_station:
			return
		available = shelf.get_quantity(item_name)
		if available <= 0:
			return
		request_qty = min(quantity, available)
		self.create_user_order([(item_name, request_qty)])

	def handle_sort_pickup_complete(self, task: Task) -> None:
		if task.task_kind != "sort":
			return
		if task.shelf.position not in self.receiving_station_positions:
			return
		key = (task.shelf.position, task.item_name)
		existing = self.receiving_transfer_tasks.get(key)
		if existing is task:
			del self.receiving_transfer_tasks[key]

	def notify_robot_idle(self, robot: MainRobot) -> None:
		self._assign_task_to_robot(robot)

	def is_walkable(self, row: int, col: int) -> bool:
		return (
			0 <= row < len(self.map_)
			and 0 <= col < len(self.map_[0])
			and self.map_[row][col] == 0
		)

	def _assign_tasks(self) -> None:
		for robot in self.robots:
			self._assign_task_to_robot(robot)

	def _assign_task_to_robot(self, robot: MainRobot) -> None:
		queue = self.sort_task_queue or self.order_task_queue
		if queue:
			robot.execute_order(queue.popleft())
	
	def get_adjacent_path_position(self, target: Tuple[int, int]) -> Optional[Tuple[int, int]]:
		rows, cols = len(self.map_), len(self.map_[0])
		r, c = target
		if 0 <= r < rows and 0 <= c < cols and self.map_[r][c] == 0:
			return target
		visited = set()
		queue = deque([((r, c), 0)])
		while queue:
			(pos_r, pos_c), dist = queue.popleft()
			for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
				nr, nc = pos_r + dr, pos_c + dc
				if not (0 <= nr < rows and 0 <= nc < cols):
					continue
				if (nr, nc) in visited:
					continue
				visited.add((nr, nc))
				if self.map_[nr][nc] == 0:
					return (nr, nc)
				if dist < 2:
					queue.append(((nr, nc), dist + 1))
		return None
	
	def is_position_occupied(self, row: int, col: int, exclude_robot: int = -1) -> bool:
		for robot in self.robots:
			if robot.robot_id == exclude_robot:
				continue
			
			if robot.position == (row, col):
				return True
			
			if robot.path and len(robot.path) > 0 and robot.path[0] == (row, col):
				return True
		
		return False
	
	def update(self, should_move: bool):
		move_permissions = self._compute_move_permissions(should_move)
		for robot in self.robots:
			robot.update(should_move, can_move=move_permissions.get(robot.robot_id, True))
		self._assign_tasks()
	
	def _compute_move_permissions(self, should_move: bool) -> Dict[int, bool]:
		if not should_move:
			return {}
		desired_moves: Dict[int, Tuple[int, int]] = {}
		for robot in self.robots:
			step = robot.peek_next_step()
			if step:
				desired_moves[robot.robot_id] = step
		if not desired_moves:
			return {}

		target_counts = Counter(desired_moves.values())
		position_lookup = {robot.position: robot.robot_id for robot in self.robots}
		permissions: Dict[int, bool] = {}
		debug_msgs = []
		for robot in self.robots:
			step = desired_moves.get(robot.robot_id)
			if step is None:
				continue

			can_move = True

			if target_counts[step] > 1:
				priority_robot = min(rid for rid, pos in desired_moves.items() if pos == step)
				if robot.robot_id != priority_robot:
					can_move = False
					debug_msgs.append(f"Robot {robot.robot_id} yields to {priority_robot} to avoid clash at {step}")

			occupant_id = position_lookup.get(step)
			if occupant_id is not None and occupant_id != robot.robot_id:
				occupant_target = desired_moves.get(occupant_id)
				occupant_leaving = occupant_target is not None and occupant_target != step
				if occupant_target == robot.position:
					# allow only one robot in a head-on swap; lower id wins the tie
					can_move = robot.robot_id < occupant_id
					if can_move:
						debug_msgs.append(f"Robot {robot.robot_id} proceeds in swap with {occupant_id} toward {step}")
					else:
						debug_msgs.append(f"Robot {robot.robot_id} pauses to avoid swap with {occupant_id} at {step}")
				elif not occupant_leaving:
					can_move = False
					debug_msgs.append(f"Robot {robot.robot_id} waits; {occupant_id} occupies {step}")

			permissions[robot.robot_id] = can_move
		if debug_msgs:
			seen = set()
			for msg in debug_msgs:
				if msg in seen:
					continue
				seen.add(msg)
				print(msg)
		return permissions
	
	def render(self, screen, shelf_img, robot_img, grid_size):
		for pos, shelf in self.shelves.items():
			shelf_pos = (pos[1] * grid_size, pos[0] * grid_size)
			screen.blit(shelf_img, shelf_pos)

			for idx, (item, q) in enumerate(shelf.items.items()):
				label = font.render(f"{item}: {q}", True, item_colors.get(item, (255, 255, 255)))
				text_position = (shelf_pos[0] + 10, shelf_pos[1] + 10 + idx * font.get_linesize())
				screen.blit(label, text_position)

		if self.receiving_stations:
			self._render_station_column(screen, shelf_img, grid_size, self.receiving_stations, "Source", (135, 206, 250))

		if self.shipping_stations:
			self._render_station_column(screen, shelf_img, grid_size, self.shipping_stations, "Orders", (255, 215, 0))

		for robot in self.robots:
			robot_pos = (robot.position[1] * grid_size, robot.position[0] * grid_size)
			screen.blit(robot_img, robot_pos)
			label = font.render(robot.name, True, (255, 255, 255))
			label_rect = label.get_rect(center=(robot_pos[0] + robot_img.get_width() // 2, robot_pos[1] - 5))
			screen.blit(label, label_rect)

	def get_random_shelf(self) -> Shelf:
		shelves_list = list(self.shelves.values())
		return shelves_list[random.randint(0, len(shelves_list) - 1)]

	def _render_station_column(self, screen, shelf_img, grid_size, stations: List[Shelf], column_title: str, title_color: Tuple[int, int, int]):
		for idx, station in enumerate(stations):
			title = column_title if idx == 0 else ""
			self._render_station(screen, shelf_img, grid_size, station, title, title_color)

	def _render_station(self, screen, shelf_img, grid_size, station: Shelf, title: str, title_color: Tuple[int, int, int]):
		station_pos = (
			station.position[1] * grid_size,
			station.position[0] * grid_size,
		)
		screen.blit(shelf_img, station_pos)
		y_offset = 10
		if title:
			title_surface = font.render(title, True, title_color)
			screen.blit(title_surface, (station_pos[0] + 10, station_pos[1] + y_offset))
			y_offset += font.get_linesize()
		for idx, (item, q) in enumerate(station.items.items()):
			label = font.render(f"{item}: {q}", True, item_colors.get(item, (255, 255, 255)))
			text_position = (
				station_pos[0] + 10,
				station_pos[1] + y_offset + idx * font.get_linesize(),
			)
			screen.blit(label, text_position)
