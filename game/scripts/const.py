"""
Constants

Universally available constants.
Enums go in interfaces.

Please don't change these in code, and don't import any parts of this project into here.

Or suffer JiffyRob's wrath
"""
from __future__ import annotations

from enum import Enum, auto
import pygame


TITLE = "Untiteled mess"  # title of the window

WINDOW_RESOLUTION: tuple[int, int] = (640, 480)  # game resolution (might be different from the actual resolution of the window if resized)

# FPS for different loops
PHYSICS_FPS: int = 120
RENDER_FPS: int = 60
INPUT_FPS: int = 500

GRAVITY: tuple[int, int] = (0, 1000)  # acceleration for Physics sprites
MAX_SPEED: float = 1000  # max speed of physics sprites
AIR_CONTROLS_REDUCTION = 0.2  # how much control a dynamic physics object has when moving in the air
YEET_UP_PERCENTAGE = 0.5  # How much of the force is used to throw up, instead of forward
TO_SECONDS: float = 1000


class Actions(Enum):
    LEFT = auto()
    RIGHT = auto()
    UP = auto()
    DOWN = auto()
    JUMP = auto()
    INTERACT = auto()


DEFAULT_KEYBINDINGS = {
    Actions.UP: [pygame.K_UP, pygame.K_w],
    Actions.LEFT: [pygame.K_LEFT, pygame.K_a],
    Actions.RIGHT: [pygame.K_RIGHT, pygame.K_d],
    Actions.DOWN: [pygame.K_DOWN, pygame.K_s],
    Actions.JUMP: [pygame.K_SPACE],
    Actions.INTERACT: [pygame.K_e]
}

# reserve channels for sounds
DOOR_CHANNEL = 1
BUTTON_CHANNEL = 2

RESERVED_CHANNELS = [
    DOOR_CHANNEL,
    BUTTON_CHANNEL
]



## Util functions ##
def fit_surface(surf: pygame.Surface, onto: tuple[int, int]):
    """Scales surface to fit in range while keeping the aspect ratio unchanged"""
    scale = min(onto[0] / surf.width, onto[1] / surf.height)
    return pygame.transform.scale_by(surf, scale)
