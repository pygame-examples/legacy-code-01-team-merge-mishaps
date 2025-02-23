"""
Constants

Universally available constants.
Enums go in interfaces.

Please don't change these in code, and don't import any parts of this project into here.

Or suffer JiffyRob's wrath
"""
from enum import Enum

TITLE = "Cool Platformer Game"  # title of the window

WINDOW_RESOLUTION: tuple[int, int] = (640, 480)  # game resolution (might be different than actual resolution of the window if resized)

# FPS for different loops
PHYSICS_FPS: int = 120
RENDER_FPS: int = 60
INPUT_FPS: int = 500

GRAVITY: tuple[int, int] = (0, 1000)  # acceleration for Physics sprites
MAX_SPEED: float = 1000  # max speed of phsyics sprites