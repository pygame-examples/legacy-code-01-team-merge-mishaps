"""
Constants

Universally available constants.
Enums go in interfaces.

Please don't change these in code, and don't import any parts of this project into here.

Or suffer JiffyRob's wrath
"""
from enum import Enum

TITLE = "Cool Platformer Game"

WINDOW_RESOLUTION: tuple[int, int] = (640, 480)

PHYSICS_FPS: int = 120
RENDER_FPS: int = 60
INPUT_FPS: int = 1000

GRAVITY: tuple[int, int] = (0, 1000)