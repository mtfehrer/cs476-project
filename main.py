import pygame
import sys
from warehouse import Warehouse
from task import Task
from importer import Importer
from utils import *

screen_size = (1200, 900)
screen = pygame.display.set_mode(screen_size)
clock = pygame.time.Clock()
framerate = 144
items_timer = 500

robot_img = pygame.image.load("robot.png").convert_alpha()
robot_img = pygame.transform.scale(robot_img, (150, 200))
shelf_img = pygame.image.load("shelf.png").convert_alpha()
shelf_img = pygame.transform.scale(shelf_img, (150, 200))

warehouse_importer = Importer()

grid_size = 175

map_layout = [
	[1, 0, 1, 0, 1],
	[0, 0, 0, 0, 0],
	[1, 0, 1, 0, 1],
	[0, 0, 0, 0, 0],
	[1, 0, 1, 0, 1]
]

warehouse = Warehouse(map_layout)

robot1 = warehouse.add_robot((1, 0))

task_queue = []

frames = 0
add_items_timer = 0
while True:
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			pygame.quit()
			sys.exit()
	
	frames += 1
	should_move = (frames >= framerate)
	if should_move:
		frames = 0
	
	add_items_timer += 1
	
	should_add_item = (add_items_timer >= items_timer)
	if should_add_item:
		random_shelf = warehouse.get_random_shelf()
		item, amount = warehouse_importer.add_random_item(random_shelf)
		task_queue = task_queue + get_tasks_for_item_sort(warehouse, robot1, item, amount, random_shelf.position)
		add_items_timer = 0

	if robot1.state == "idle" and task_queue:
		cur_task = task_queue.pop(0)
		robot1.execute_order(cur_task)
	
	warehouse.update(should_move)
	print(robot1.state)
	
	screen.fill((0, 0, 0))
	warehouse.render(screen, shelf_img, robot_img, grid_size)
	pygame.display.update()
	clock.tick(framerate)