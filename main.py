import pygame
import sys
from warehouse import Warehouse
from importer import Importer
from brain import Brain

screen_size = (1200, 900)
screen = pygame.display.set_mode(screen_size)
clock = pygame.time.Clock()
framerate = 144

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
robot2 = warehouse.add_robot((3, 4))
robot3 = warehouse.add_robot((1, 4))

brain = Brain(warehouse, warehouse_importer)

frames = 0
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    frames += 1
    should_move = (frames >= framerate)
    if should_move:
        frames = 0

    brain.update()

    warehouse.update(should_move)

    screen.fill((0, 0, 0))
    warehouse.render(screen, shelf_img, robot_img, grid_size)
    pygame.display.update()
    clock.tick(framerate)