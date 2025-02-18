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
    STATIC = 1
    DYNAMIC = 2
    TRIGGER = 3


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
    rect: RectLike
    level: GameLevelInterface
    controller: SpriteControllerInterface = SpriteControllerInterface()
    groups: list[str] = field(default_factory=list)


@dataclass
class SpritePhysicsData:
    # object used to init physics sprites with
    # add stuff here as necessary
    physics_type: PhysicsType = PhysicsType.STATIC
    weight: float = 10
    horizontal_speed: float = 400
    jump_speed: float = 128
    duck_speed: float = 128
    one_way: bool = False


class SpriteInterface:
    def __init__(self, data: SpriteInitData):
        pass

    @property
    def pos(self) -> tuple[int, int]:
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