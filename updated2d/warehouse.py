from collections import deque
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
	
	def add_robot(self, position: Tuple[int, int], role: str = "sorter") -> MainRobot:
		robot_id = len(self.robots)
		robot = self._create_robot_instance(position, robot_id, role)
		self.robots.append(robot)
		self._assign_task_to_robot(robot)
		return robot

	def _create_robot_instance(self, position: Tuple[int, int], robot_id: int, role: str) -> MainRobot:
		if role == "sorter":
			return SorterRobot(position, robot_id, self)
		if role in ("picker", "order"):
			return OrderRobot(position, robot_id, self)
		return MainRobot(position, robot_id, role, self)

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
			home_shelf = self.shelves[home_position]
			if home_shelf.get_quantity(item_name) > 0:
				return home_shelf
		for shelf in self.shelves.values():
			if shelf.get_quantity(item_name) > 0:
				return shelf
		return None

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

	def create_user_order(self, order_items) -> None:
		normalized_items = self._normalize_order_items(order_items)
		if not normalized_items:
			print("Invalid order request")
			return
		shipping_station = self._select_station(self.shipping_stations)
		if not shipping_station:
			print("No shipping station configured")
			return
		prepared_lines: List[Tuple[str, int, Shelf]] = []
		for item_name, quantity in normalized_items:
			source_shelf = self._find_shelf_with_item(item_name)
			if not source_shelf:
				print(f"Item {item_name} unavailable for order")
				continue
			available = source_shelf.get_quantity(item_name)
			actual_quantity = min(quantity, available)
			if actual_quantity <= 0:
				print(f"Item {item_name} out of stock")
				continue
			prepared_lines.append((item_name, actual_quantity, source_shelf))
		if not prepared_lines:
			print("Order could not be queued; no items available")
			return
		order_id = self.next_order_id
		self.next_order_id += 1
		order = Order(order_id, [(item, quantity) for item, quantity, _ in prepared_lines])
		self.orders[order_id] = order
		print(f"Queued order #{order_id} for {order.describe()}")
		self._queue_order_tasks(order_id, prepared_lines, shipping_station)

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

	def _assign_tasks(self) -> None:
		for robot in self.robots:
			self._assign_task_to_robot(robot)

	def _assign_task_to_robot(self, robot: MainRobot) -> None:
		if not robot.is_available():
			return
		if robot.role == "sorter" and self.sort_task_queue:
			task = self.sort_task_queue.popleft()
			robot.execute_order(task)
		elif robot.role == "picker" and self.order_task_queue:
			task = self.order_task_queue.popleft()
			robot.execute_order(task)
	
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
		for robot in self.robots:
			robot.update(should_move)
		self._assign_tasks()
	
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
			screen.blit(robot_img, (robot.position[1] * grid_size, robot.position[0] * grid_size))

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
