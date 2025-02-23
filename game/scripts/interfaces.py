"""
This file is full of interfaces, dataclasses, and enums for type hinting.
I put in type hints for methods intended to be called by external code.

Classes implementing these interfaces should be subclasses of them.

Do not import any other parts of this project here.
Do not add any implementations here.

Or suffer JiffyRob's wrath
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterator, Any, Awaitable

import pygame
from pygame.typing import RectLike, SequenceLike


class WindowScale(Enum):
    INTEGER = 1
    STRETCH = 2
    DOUBLE_LETTER = 3


class PhysicsType(Enum):
    STATIC = 1  # Dynamic sprites collide with and stay off of
    DYNAMIC = 2  # "character" sprite.  Walks, jumps, etc.
    TRIGGER = 3  # Can message certain sprites when they collide with it
    KINEMATIC = 4  # Not messed with by physics engine
    PORTAL = 5  # PORTAL!!!!!


class Direction(Enum):
    NORTH = (0, -1)
    SOUTH = (0, 1)
    EAST = (1, 0)
    WEST = (-1, 0)


class GameInterface:
    def quit(self) -> None:
        pass

    async def run(self) -> None:
        pass

    def add_task(self, task: Awaitable) -> None:
        pass


class GameStateInterface:
    def init(self) -> None:
        pass

    def add_task(self, task: Awaitable) -> None:
        pass

    def on_enter(self) -> None:
        pass

    def on_exit(self) -> None:
        pass

    def update_physics(self, dt: float) -> None:
        pass

    def render(self, dt_since_physics: float) -> pygame.Surface:
        pass


class GameLevelInterface(GameStateInterface):
    def get_group(self, group_name: str) -> pygame.sprite.AbstractGroup:
        pass

    def add_to_groups(self, sprite: Any, *groups: str) -> None:  # TODO: get rid of Any here?
        pass


@dataclass
class SpriteCommand:
    command: str
    timestamp: int


class SpriteControllerInterface:
    async def run(self) -> None:
        pass

    def get_commands(self) -> Iterator[SpriteCommand]:
        return []


@dataclass
class SpriteInitData:
    # Object used to init sprites with
    # Add stuff here as necessary
    rect: RectLike  # initial position and size of sprite
    level: GameLevelInterface  # level that holds sprite
    controller: SpriteControllerInterface = SpriteControllerInterface()  # controller to pilot sprite
    groups: list[str] = field(default_factory=list)  # level groups to add sprite to

    # put any init data that is specific to a certain sprite type in here
    # like orientation of a portal, for example
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class SpritePhysicsData:
    # object used to init physics sprites with
    # add stuff here as necessary
    # no need for every sprite to use every bit of data
    physics_type: PhysicsType = PhysicsType.STATIC  # type of physics resolution to use
    weight: float = 10  # weight (not used RN)
    horizontal_speed: float = 400  # walking speed (for dynamic sprites)
    jump_speed: float = 128  # jump speed (for dynamic sprites)
    duck_speed: float = 128  # duck speed (for dynamic sprites)
    one_way: bool = False  # whether a static sprite collides downward
    orientation: Direction = Direction.NORTH  # which way a portal shoots / accepts sprites
    tunnel_id: str = "default"  # portals with the same tunnel_id link to each other


class SpriteInterface:
    def __init__(self, data: SpriteInitData):
        pass

    @property
    def pos(self) -> tuple[int, int]:
        """Center position of Sprite"""
        pass

    @pos.setter
    def pos(self, value: str | float | SequenceLike[float] | pygame.Vector2) -> None:
        pass

    def update_physics(self, dt) -> None:
        pass

    def interpolated_pos(self, dt_since_physics: float) -> None:
        pass

    def draw(self, surface: pygame.Surface, dt_since_physics: float) -> None:
        pass


class PhysicsSpriteInterface(SpriteInterface):
    def trigger(self, other: SpriteInterface) -> None:
        pass

    @property
    def collision_rect(self) -> pygame.FRect:
        pass

    def left(self) -> None:
        pass

    def right(self) -> None:
        pass

    def jump(self) -> None:
        pass

    def duck(self) -> None:
        pass