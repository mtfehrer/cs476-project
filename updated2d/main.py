import pygame 
import sys

from importer import Importer
from warehouse import Warehouse
from constants import (
	SCREEN_SIZE,
	FRAMERATE,
	ITEMS_TIMER,
	GRID_SIZE,
	MAP_LAYOUT,
	ROBOT_IMAGE_PATH,
	ROBOT_IMAGE_SIZE,
	SHELF_IMAGE_PATH,
	SHELF_IMAGE_SIZE,
	INITIAL_STOCK,
	ITEM_HOME_LOCATIONS,
	ROBOT_CONFIG,
	ORDER_DROPOFF_POSITIONS,
	RECEIVING_STATION_POSITIONS,
	USER_ORDER_KEY_BINDINGS,
	SAMPLE_ORDERS,
)

screen = pygame.display.set_mode(SCREEN_SIZE)
clock = pygame.time.Clock()

robot_img = pygame.image.load(ROBOT_IMAGE_PATH).convert_alpha()
robot_img = pygame.transform.scale(robot_img, ROBOT_IMAGE_SIZE)
shelf_img = pygame.image.load(SHELF_IMAGE_PATH).convert_alpha()
shelf_img = pygame.transform.scale(shelf_img, SHELF_IMAGE_SIZE)

warehouse = Warehouse(
	MAP_LAYOUT,
	ITEM_HOME_LOCATIONS,
	shipping_station_positions=ORDER_DROPOFF_POSITIONS,
	receiving_station_positions=RECEIVING_STATION_POSITIONS,
)
warehouse_importer = Importer(warehouse)

for position, inventory in INITIAL_STOCK.items():
	for item_name, quantity in inventory.items():
		warehouse.stock_shelf(position, item_name, quantity)

for robot_config in ROBOT_CONFIG:
	warehouse.add_robot(robot_config["position"], role=robot_config["role"])

for idx, sample_order in enumerate(SAMPLE_ORDERS, start=1):
	description = ", ".join(f"{quantity}x {item}" for item, quantity in sample_order)
	print(f"Auto-queuing sample order {idx}: {description}")
	warehouse.create_user_order(sample_order)

for key, order in USER_ORDER_KEY_BINDINGS.items():
	key_name = pygame.key.name(key)
	order_description = ", ".join(f"{quantity}x {item}" for item, quantity in order)
	print(f"Press '{key_name}' to order {order_description}")

frames = 0
add_items_timer = 0
while True:
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			pygame.quit()
			sys.exit()
		elif event.type == pygame.KEYDOWN:
			order = USER_ORDER_KEY_BINDINGS.get(event.key)
			if order:
				warehouse.create_user_order(order)
	
	frames += 1
	should_move = (frames >= FRAMERATE)
	if should_move:
		frames = 0
	
	add_items_timer += 1
	
	should_add_item = (add_items_timer >= ITEMS_TIMER)
	if should_add_item:
		warehouse_importer.add_random_item()
		add_items_timer = 0
	
	
	warehouse.update(should_move)
	
	screen.fill((0, 0, 0))
	warehouse.render(screen, shelf_img, robot_img, GRID_SIZE)
	pygame.display.update()
	clock.tick(FRAMERATE)
