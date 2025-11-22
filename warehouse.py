from typing import List, Dict, Tuple, Optional
from shelf import Shelf
from robot import Robot
from task import Task
from utils import get_tasks_for_item_sort
import pygame
import random
from constants import font, item_colors, text_surfaces


class Warehouse:
	def __init__(self, map_layout: List[List[int]], items: List[str]):
		self.map_ = map_layout
		self.shelves: Dict[Tuple[int, int], Shelf] = {}
		self.task_queue: List[Task] = []
		self.robots: List[Robot] = []

		for i in range(len(self.map_)):
			for j in range(len(self.map_[0])):
				if self.map_[i][j] == 1:
					self.shelves[(i, j)] = Shelf((i, j))
		for pos in self.shelves.keys():
			for item in items:
				if random.randint(0, 1) == 1:
					to_add_amt = random.randint(1, 5)
					self.shelves[pos].add_item(item, to_add_amt)
					self.task_queue.extend(get_tasks_for_item_sort(self, item, to_add_amt, pos))

	def add_robot(self, position: Tuple[int, int]) -> Robot:
		robot = Robot(position, len(self.robots), self)
		self.robots.append(robot)
		return robot

	def get_robot_at(self, row: int, col: int) -> Optional[Robot]:
		""" Returns the robot at the given position, if any """
		for robot in self.robots:
			if robot.position == (row, col):
				return robot
		return None

	def is_occupied_at_time(self, row: int, col: int, time: int, exclude_robot_id: int = -1) -> bool:
		""" Checks if a specific cell (row, col) will be occupied at time """
		for robot in self.robots:
			if robot.robot_id == exclude_robot_id:
				continue

			robot_pos_at_time = robot.get_position_at_time(time)
			if robot_pos_at_time == (row, col):
				return True

		return False

	def is_position_occupied(self, row: int, col: int, exclude_robot: int = -1) -> bool:
		"""Legacy check for current time (time=0)"""
		return self.is_occupied_at_time(row, col, 0, exclude_robot)

	def update(self, should_move: bool):
		for robot in self.robots:
			robot.update(should_move)
		self._assign_tasks()

	def render(self, screen, shelf_img, robot_img, grid_size):
		rows = len(self.map_)
		cols = len(self.map_[0])
		grid_color = (50, 50, 50)

		for r in range(rows):
			for c in range(cols):
				rect = pygame.Rect(c * grid_size, r * grid_size, grid_size, grid_size)
				pygame.draw.rect(screen, grid_color, rect, 1)
		for pos, shelf in self.shelves.items():
			shelf_pos = (pos[1] * grid_size, pos[0] * grid_size)
			screen.blit(shelf_img, shelf_pos)

			item_text_dy = 0
			for item, q in shelf.items.items():
				if (item, q) not in text_surfaces:
					text_surfaces[(item, q)] = font.render( f"{item}: {q}", True, item_colors[item])
				screen.blit(text_surfaces[(item, q)], (shelf_pos[0], shelf_pos[1] + item_text_dy))
				item_text_dy += 30

		for robot in self.robots:
			screen.blit(robot_img,(robot.position[1] * grid_size, robot.position[0] * grid_size))
			id_text = font.render(f"{robot.robot_id}", True, (255, 255, 255))

			rob_x = robot.position[1] * grid_size
			rob_y = robot.position[0] * grid_size
			text_y = rob_y + robot_img.get_height() - id_text.get_height() - 25

			screen.blit(id_text, (rob_x, text_y))

	def get_random_shelf(self) -> Shelf:
		shelves_list = list(self.shelves.values())
		return shelves_list[random.randint(0, len(shelves_list) - 1)]

	def _assign_tasks(self):
		""" Assigns pending tasks to idle robots based on inventory requirements """
		if not self.task_queue:
			return

		for robot in self.robots:
			if robot.state == "idle":

				task_index = -1

				for i, task in enumerate(self.task_queue):
					if task.is_pickup:
						task_index = i
						break
					else:
						# check to see if you can take it
						amt_in_inventory = robot.inventory.get(task.item_name, 0)
						if amt_in_inventory >= task.quantity:
							task_index = i
							break

				if task_index != -1:
					task = self.task_queue.pop(task_index)
					robot.execute_order(task)
