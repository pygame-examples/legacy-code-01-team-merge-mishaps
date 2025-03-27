import pygame

from ..const import WINDOW_RESOLUTION
from ..interfaces import GameStateInterface


class Menu(GameStateInterface):
    """
    Main menu (NOT IMPLEMENTED)

    Only reason this exists is for testing ATM
    """

    def __init__(self): ...

    def update_physics(self, dt):
        return super().update_physics(dt)

    def render(self, dt_since_physics):
        return pygame.Surface(WINDOW_RESOLUTION)
