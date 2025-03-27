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

TITLE = "Portaler"  # title of the window

WINDOW_RESOLUTION: tuple[int, int] = (
    1280,
    960,
)  # game resolution (might be different from the actual resolution of the window if resized)

# FPS for different loops
PHYSICS_FPS: int = 120
RENDER_FPS: int = 60
INPUT_FPS: int = 500

GRAVITY: tuple[int, int] = (0, 1000)  # acceleration for Physics sprites
MAX_SPEED: float = 2000  # max speed of physics sprites
AIR_CONTROLS_REDUCTION = 0.4  # how much control a dynamic physics object has when moving in the air
HORIZONTAL_YEET_ANGLE = 15  # angle of elevation for horizontal yeets


class Actions(Enum):  # ROB LITERALLY SAID NOT TO PUT ENUMS IN HERE LMAOO
    LEFT = auto()  # whatever, just keep this here loll
    RIGHT = auto()
    UP = auto()
    DOWN = auto()
    JUMP = auto()
    INTERACT = auto()


DEFAULT_KEYBINDINGS = {
    Actions.UP: [
        pygame.K_UP,
        pygame.K_w,
    ],  # just looking up to throw something up, but otherwise does nothing
    Actions.LEFT: [pygame.K_LEFT, pygame.K_a],
    Actions.RIGHT: [pygame.K_RIGHT, pygame.K_d],
    Actions.DOWN: [pygame.K_DOWN, pygame.K_s],
    Actions.JUMP: [pygame.K_SPACE],
    Actions.INTERACT: [pygame.K_e],
}

# reserve channels for sounds
DOOR_CHANNEL = 1
BUTTON_CHANNEL = 2

RESERVED_CHANNELS = [DOOR_CHANNEL, BUTTON_CHANNEL]


TILE_SIZE = 32  # 32px


## Util functions ##
def fit_surface(surf: pygame.Surface, onto: tuple[int, int]):
    """Scales surface to fit in range while keeping the aspect ratio unchanged"""
    scale = min(onto[0] / surf.width, onto[1] / surf.height)
    return pygame.transform.scale_by(surf, scale)
