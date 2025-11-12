import pygame

pygame.init()
item_colors = {"Gadget": (255, 0, 0), "Widget": (0, 255, 0), "Sprocket": (100, 100, 255)}
font = pygame.font.SysFont("Arial", 30)
text_surfaces = {}