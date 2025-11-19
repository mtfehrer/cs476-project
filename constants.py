import pygame
import random

pygame.init()
item_colors = {"Gadget": (255, 0, 0), "Widget": (0, 255, 0), "Sprocket": (100, 100, 255)}
font = pygame.font.SysFont("Arial", 30)
text_surfaces = {}

new_items = [
    "Gadget",
    "Widget",
    "Sprocket"
]

for item in new_items:
    item_colors[item] = (
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255),
    )
