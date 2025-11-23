import pygame
import random

pygame.init()

FRAMERATE = 144
ITEMS_TIMER = 500
BASE_GRID_SIZE = 175
MAX_SCREEN_WIDTH = 1400
MAX_SCREEN_HEIGHT = 900
ORDER_PICKUP_DELAY_SECONDS = 180
STARTER_SHIPMENT_QUANTITY = 6
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


def _add_side_buffer_columns(layout):
	padded = []
	for row in layout:
		# keep outer wall columns, insert a buffer aisle between sources/orders and storage
		padded.append([row[0], 0, *row[1:-1], 0, row[-1]])
	return padded


MAP_LAYOUT = _build_storage_map(3, 3)
MAP_LAYOUT = _add_side_buffer_columns(MAP_LAYOUT)
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
STARTER_SORT_ITEMS = [
	"laptop",
	"airpods",
	"toothpaste",
	"notebook",
	"discord",
	"pen",
	"cologne",
]

ITEM_HOME_LOCATIONS = {}
for idx, item in enumerate(item_colors.keys()):
	ITEM_HOME_LOCATIONS[item] = SHELF_POSITIONS[idx % len(SHELF_POSITIONS)]

INITIAL_STOCK = {
	ITEM_HOME_LOCATIONS["Widget"]: {"Widget": 70},
	ITEM_HOME_LOCATIONS["Gadget"]: {"Gadget": 60},
	ITEM_HOME_LOCATIONS["Sprocket"]: {"Sprocket": 55},
	ITEM_HOME_LOCATIONS["laptop"]: {"laptop": 10},
	ITEM_HOME_LOCATIONS["airpods"]: {"airpods": 9},
	ITEM_HOME_LOCATIONS["toothpaste"]: {"toothpaste": 11},
	ITEM_HOME_LOCATIONS["notebook"]: {"notebook": 9},
	ITEM_HOME_LOCATIONS["discord"]: {"discord": 8},
	ITEM_HOME_LOCATIONS["pen"]: {"pen": 10},
	ITEM_HOME_LOCATIONS["cologne"]: {"cologne": 7},
}

ROBOT_CONFIG = [
	{"role": "sorter", "position": (middle_row, 1), "name": "Sorter-1"},
	{"role": "picker", "position": (middle_row, len(MAP_LAYOUT[0]) - 4), "name": "Picker-1"},
]

USER_ORDER_KEY_BINDINGS = {
	pygame.K_1: [("Widget", 12)],
	pygame.K_2: [("Gadget", 8), ("Widget", 6)],
	pygame.K_3: [("Sprocket", 6), ("Gadget", 4), ("Widget", 5)],
}

SAMPLE_ORDERS = [
	[("laptop", 18), ("airpods", 14)],
	[("toothpaste", 22), ("notebook", 18)],
	[("discord", 14), ("pen", 12), ("cologne", 10)],
]

# Orders queued immediately at startup to demonstrate picker traffic.
DEMO_ORDERS = [
	[("Widget", 12), ("Gadget", 10)],
	[("Sprocket", 14), ("Widget", 8)],
	[("laptop", 6), ("toothpaste", 6)],
	[("pen", 8), ("discord", 6)],
	[("airpods", 8), ("cologne", 5)],
	[("notebook", 8), ("Widget", 6), ("Gadget", 4)],
]
