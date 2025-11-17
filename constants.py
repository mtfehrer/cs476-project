import pygame
import random

pygame.init()
item_colors = {"Gadget": (255, 0, 0), "Widget": (0, 255, 0), "Sprocket": (100, 100, 255)}
font = pygame.font.SysFont("Arial", 30)
text_surfaces = {}

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
