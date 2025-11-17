from typing import List, Dict, Tuple
from shelf import Shelf
from robot import Robot
import random
from constants import font, item_colors, text_surfaces

class Warehouse:
	def __init__(self, map_layout: List[List[int]]):
		self.map_ = map_layout
		self.shelves: Dict[Tuple[int, int], Shelf] = {}
		self.robots: List[Robot] = []
		
		for i in range(len(self.map_)):
			for j in range(len(self.map_[0])):
				if self.map_[i][j] == 1:
					self.shelves[(i, j)] = Shelf((i, j))
	
	def add_robot(self, position: Tuple[int, int]) -> Robot:
		robot = Robot(position, len(self.robots), self)
		self.robots.append(robot)
		return robot
	
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
	
	def render(self, screen, shelf_img, robot_img, grid_size):
		for pos, shelf in self.shelves.items():
			shelf_pos = (pos[1] * grid_size, pos[0] * grid_size)
			screen.blit(shelf_img, shelf_pos)

			for item, q in shelf.items.items():
				if (item, q) not in text_surfaces:
					text_surfaces[(item, q)] = font.render(f"{item}: {q}", True, item_colors[item])
				screen.blit(text_surfaces[(item, q)], shelf_pos)

		for robot in self.robots:
			screen.blit(robot_img, (robot.position[1] * grid_size, robot.position[0] * grid_size))

	def get_random_shelf(self) -> Shelf:
			shelves_list = list(self.shelves.values())
			return shelves_list[random.randint(0, len(shelves_list) - 1)]