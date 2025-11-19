import pygame
import random

pygame.init()

FRAMERATE = 144
ITEMS_TIMER = 500
BASE_GRID_SIZE = 175
MAX_SCREEN_WIDTH = 1400
MAX_SCREEN_HEIGHT = 900
IMPORTER_MIN_SHIPMENTS = 1
IMPORTER_MAX_SHIPMENTS = 3
IMPORTER_MIN_UNITS = 1
IMPORTER_MAX_UNITS = 3
SORTER_MAX_PENDING_BATCHES = 8

ROBOT_IMAGE_PATH = "robot.png"
SHELF_IMAGE_PATH = "shelf.png"


def _build_storage_map(shelf_rows: int, shelf_cols: int):
	rows = shelf_rows * 2 + 1
	cols = shelf_cols * 2 + 1
	layout = []
	for r in range(rows):
		row = []
		for c in range(cols):
			if r % 2 == 1 and c % 2 == 1:
				row.append(1)
			else:
				row.append(0)
		layout.append(row)
	return layout


MAP_LAYOUT = _build_storage_map(5, 5)
GRID_SIZE = min(
	BASE_GRID_SIZE,
	MAX_SCREEN_WIDTH // len(MAP_LAYOUT[0]),
	MAX_SCREEN_HEIGHT // len(MAP_LAYOUT),
)
GRID_SIZE = max(70, GRID_SIZE)
SCREEN_SIZE = (GRID_SIZE * len(MAP_LAYOUT[0]), GRID_SIZE * len(MAP_LAYOUT))
ROBOT_IMAGE_SIZE = (int(GRID_SIZE * 0.9), int(GRID_SIZE * 1.1))
SHELF_IMAGE_SIZE = (int(GRID_SIZE * 0.95), int(GRID_SIZE * 1.1))
FONT_SIZE = max(14, int(GRID_SIZE * 0.18))

# place source/orders just outside the storage columns
middle_row = len(MAP_LAYOUT) // 2
if middle_row % 2 == 1:
	middle_row += 1
RECEIVING_STATION_POSITIONS = [(middle_row, 0)]
ORDER_DROPOFF_POSITIONS = [(middle_row, len(MAP_LAYOUT[0]) - 1)]


def _get_shelf_positions():
	positions = []
	for row_idx, row in enumerate(MAP_LAYOUT):
		for col_idx, cell in enumerate(row):
			if cell == 1:
				positions.append((row_idx, col_idx))
	return positions


SHELF_POSITIONS = _get_shelf_positions()

font = pygame.font.SysFont("Arial", FONT_SIZE)
item_colors = {"Gadget": (255, 0, 0), "Widget": (0, 255, 0), "Sprocket": (100, 100, 255)}

new_items = [
	"toothpaste",
	"toothbrush",
	"cologne",
	"airpods",
	"iphone",
	"watch",
	"laptop",
	"dell laptop",
	"candy",
	"discord",
	"phone",
	"toilet paper",
	"paper",
	"pencil",
	"pen",
	"notebook",
	"face",
]

for item in new_items:
	item_colors[item] = (
		random.randint(0, 255),
		random.randint(0, 255),
		random.randint(0, 255),
	)

ITEM_HOME_LOCATIONS = {}
for idx, item in enumerate(item_colors.keys()):
	ITEM_HOME_LOCATIONS[item] = SHELF_POSITIONS[idx % len(SHELF_POSITIONS)]

INITIAL_STOCK = {
	ITEM_HOME_LOCATIONS["Widget"]: {"Widget": 40},
	ITEM_HOME_LOCATIONS["Gadget"]: {"Gadget": 35},
	ITEM_HOME_LOCATIONS["Sprocket"]: {"Sprocket": 30},
}

ROBOT_CONFIG = [
	{"role": "sorter", "position": (middle_row, 2)},
	{"role": "picker", "position": (middle_row, len(MAP_LAYOUT[0]) - 3)},
]

USER_ORDER_KEY_BINDINGS = {
	pygame.K_1: [("Widget", 5)],
	pygame.K_2: [("Gadget", 3), ("Widget", 2)],
	pygame.K_3: [("Sprocket", 2), ("Gadget", 1), ("Widget", 1)],
}

SAMPLE_ORDERS = [
	[("Widget", 2), ("Gadget", 1)],
	[("Sprocket", 3), ("Widget", 1)],
	[("Gadget", 2), ("Sprocket", 2)],
]
