import pygame
import sys
from warehouse import Warehouse
from task import Task
from importer import Importer

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

warehouse.shelves[(0, 0)].add_item("Widget", 50)
warehouse.shelves[(0, 2)].add_item("Gadget", 30)
warehouse.shelves[(2, 0)].add_item("Sprocket", 20)

robot1 = warehouse.add_robot((1, 0))
robot2 = warehouse.add_robot((3, 0))

order1 = Task(warehouse.shelves[(0, 0)], "Widget", 5, is_pickup=True)
order2 = Task(warehouse.shelves[(0, 2)], "Gadget", 3, is_pickup=True)

robot1.execute_order(order1)
robot2.execute_order(order2)

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
		warehouse_importer.add_random_item(random_shelf)
		add_items_timer = 0
	
	
	warehouse.update(should_move)
	
	screen.fill((0, 0, 0))
	warehouse.render(screen, shelf_img, robot_img, grid_size)
	pygame.display.update()
	clock.tick(framerate)