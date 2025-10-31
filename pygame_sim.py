import pygame, sys, time

screen_size = (1200, 900)
screen = pygame.display.set_mode(screen_size)
clock = pygame.time.Clock()
framerate = 144
pygame.init()

map_ = [[1, 0, 1, 0, 1],
		[2, 0, 0, 0, 0],
		[1, 0, 1, 0, 1],
		[0, 0, 0, 0, 0],
		[1, 0, 1, 0, 1]]

robot_img = pygame.image.load("robot.png").convert_alpha()
robot_img = pygame.transform.scale(robot_img, (150, 200))

shelf_img = pygame.image.load("shelf.png").convert_alpha()
shelf_img = pygame.transform.scale(shelf_img, (150, 200))

grid_size = 175

robot_position = (1, 0)
remaining_path = [(1, 1), (1, 2), (1, 3), (2, 3), (3, 3), (3, 4)]
frames = 0

def render_map():
	for i in range(len(map_)):
		for j in range(len(map_[0])):
			c = map_[i][j]
			if c == 1:
				screen.blit(shelf_img, (j * grid_size, i * grid_size))
			if c == 2:
				screen.blit(robot_img, (j * grid_size, i * grid_size))

while True:
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			pygame.quit()
			sys.exit()

	frames += 1
	if frames == framerate:
		map_[robot_position[0]][robot_position[1]] = 0
		if remaining_path:
			robot_position = remaining_path[0]
			remaining_path = remaining_path[1:]
		map_[robot_position[0]][robot_position[1]] = 2
		frames = 0

	screen.fill((0, 0, 0))
	render_map()

	pygame.display.update()
	clock.tick(framerate)