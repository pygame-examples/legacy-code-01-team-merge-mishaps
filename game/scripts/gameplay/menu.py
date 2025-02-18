import pygame

from ..interfaces import GameStateInterface
from ..const import WINDOW_RESOLUTION

class Menu(GameStateInterface):
    def __init__(self):
        ...


    def update_physics(self, dt):
        return super().update_physics(dt)
    
    def render(self, dt_since_physics):
        print("render with extra", dt_since_physics)
        return pygame.Surface(WINDOW_RESOLUTION).convert()