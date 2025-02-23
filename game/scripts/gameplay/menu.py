import pygame

from ..interfaces import GameStateInterface
from ..const import WINDOW_RESOLUTION

class Menu(GameStateInterface):
    """
    Main menu (NOT IMPLEMENTED)

    Only reason this exists is for testing ATM
    """
    def __init__(self):
        ...


    def update_physics(self, dt):
        return super().update_physics(dt)
    
    def render(self, dt_since_physics):
        print("render with extra", dt_since_physics)
        return pygame.Surface(WINDOW_RESOLUTION).convert()