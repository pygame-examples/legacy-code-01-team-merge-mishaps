"""
This file is full of interfaces, dataclasses, and enums for type hinting.
I put in type hints for methods intended to be called by external code.

Classes implementing these interfaces should be subclasses of them.

Do not import any other parts of this project here.
Do not add any implementations here.

Or suffer JiffyRob's wrath
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from enum import Enum, IntEnum, auto
from types import EllipsisType
from typing import Any, Coroutine, TypeVar, cast, overload

import pygame
from pygame.typing import SequenceLike

from .gameplay.camera import Camera

_T = TypeVar("_T")

_S = TypeVar("_S", bound=type["SpriteInterface"])


class PhysicsType(Enum):
    STATIC = auto()  # Dynamic sprites collide with and stay off of
    DYNAMIC = auto()  # "character" sprite.  Walks, jumps, etc.
    TRIGGER = auto()  # Can message certain sprites when they collide with it
    KINEMATIC = auto()  # Not messed with by physics engine
    PORTAL = auto()  # PORTAL!!!!!
    ACTIVATED = auto()  # TRIGGER objects interact with these


class Axis(IntEnum):
    HORIZONTAL = 0
    VERTICAL = 1

    @property
    def opposite(self) -> Axis:
        return Axis(1 - self.value)


class ThrowableType(Enum):
    # values correspond to the spritesheet
    IRON = 0
    WOOD = 1
    GOLD = 2


THROWABLE_TYPE_INTO_WEIGHT = {
    ThrowableType.IRON.value: 50,
    ThrowableType.WOOD.value: 20,
    ThrowableType.GOLD.value: 125,
}


class HeightChangeState(Enum):
    LOWERING = auto()
    HIGHTENING = auto()


class PortalColor(Enum):
    GREEN = auto()
    YELLOW = auto()
    RED = auto()
    BLUE = auto()
    BEIGE = auto()
    CYAN = auto()
    BROWN = auto()
    MAGENTA = auto()
    GRAY = auto()
    DARK_GREEN = auto()
    OCEAN = auto()
    PALE_BLUE = auto()


class Direction(Enum):
    NORTH = (0, -1)
    SOUTH = (0, 1)
    EAST = (1, 0)
    WEST = (-1, 0)

    @property
    def opposite(self) -> Direction:
        return Direction((-self.value[0], -self.value[1]))

    @property
    def axis(self) -> Axis:
        return Axis.VERTICAL if self in {Direction.NORTH, Direction.SOUTH} else Axis.HORIZONTAL


DIRECTION_TO_ANGLE = {
    # Please note pygame's inverted y axis
    Direction.NORTH: 270,
    Direction.SOUTH: 90,
    Direction.EAST: 0,
    Direction.WEST: 180,
}


class GameInterface:
    state_stack: deque[GameStateInterface]

    def quit(self) -> None:
        pass

    async def run(self) -> None:
        pass

    def add_task(self, task: Coroutine) -> None:
        pass


class GameStateInterface(ABC):
    def init(self) -> None:
        pass

    def add_task(self, task: Coroutine) -> None:
        pass

    def on_enter(self) -> None:
        pass

    def on_exit(self) -> None:
        pass

    def handle_input(self, dt: float) -> None:
        pass

    async def update_actors(self, dt: float) -> None:
        pass

    async def update_physics(self, dt: float) -> None:
        pass

    @abstractmethod
    async def render(self, size: tuple[int, int], dt_since_physics: float) -> pygame.Surface:
        pass


class GameLevelInterface(GameStateInterface, ABC):
    groups: dict[str, pygame.sprite.AbstractGroup]
    game: GameInterface
    level_count: int
    _surface: pygame.Surface | None = None

    def spawn(
        self,
        cls: _S,
        data: SpriteInitData,
        target: bool = False,
    ) -> _S:
        """Spawn a new sprite"""
        # TODO: why does this exist
        sprite = cls(data)
        if target:
            self.camera.set_target(sprite)
        return sprite  # type: ignore[return-value]

    @overload
    def get_group(self, group_name: str, /) -> pygame.sprite.AbstractGroup: ...
    @overload
    def get_group(self, group_name: str, default: _T, /) -> pygame.sprite.AbstractGroup | _T: ...
    def get_group(
        self, group_name: str, default: _T | EllipsisType = ..., /
    ) -> pygame.sprite.AbstractGroup | _T:
        """
        Get a sprite group from a string

        Returns None if group does not exist
        """
        if default is Ellipsis:
            return self.groups[group_name]
        return self.groups.get(group_name, default)

    def add_to_groups(self, sprite: SpriteInterface, *groups: str) -> None:
        """
        Add a sprite to the given string groups

        Will create new ones if the groups do not exist
        """
        for group in groups:
            self.groups.setdefault(group, pygame.sprite.Group()).add(
                sprite
            )  # somehow creates a new group ????

    @property
    def camera(self) -> Camera:
        return cast(Camera, self.get_group("render"))

    async def render(self, size: tuple[int, int], dt_since_physics: float) -> pygame.Surface:
        """
        Return a drawn surface.

        dt_since_physics is how much time since the last physics update and is used for position interpolation
        """
        surface = self._surface
        if surface is None or surface.size != size:
            self._surface = surface = pygame.Surface(size)
        self.camera.draw(surface, dt_since_physics)
        return surface

    async def update_actors(self, dt):
        self.handle_input(dt)

        for sprite in self.get_group("actors"):
            sprite.act(dt)

    async def update_physics(self, dt):
        """
        Update the physics in this level
        """
        for sprite in self.get_group("physics"):
            sprite.update_physics(dt)

    def empty_all(self):
        for group in self.groups.values():
            group.empty()


@dataclass
class SpriteInitData:
    # Object used to init sprites with
    # Add stuff here as necessary
    rect: pygame.Rect | pygame.FRect  # initial position and size of sprite
    level: GameLevelInterface  # level that holds sprite
    target: bool = False  # whether the camera should follow the sprite
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
    yeet_force: float = 12000  # force (for dynamic sprites)
    horizontal_ground_speed: float = 250  # max walking speed (for dynamic sprites)
    horizontal_ground_acceleration: float = (
        4000  # acceleration for dynamic sprites that are on the ground (affects 'pulling' strength)
    )
    ground_damping: float = 1e-10  # damping of 0.9 means 10% velocity is lost per second
    horizontal_air_speed: float = 100  # movement speed for dynamic sprites that are in the air
    horizontal_air_acceleration: float = 2000  # acceleration for dynamic sprites that are in the air
    air_damping: float = 0.8
    jump_speed: float = 460.0  # jump speed (for dynamic sprites)
    duck_speed: float = 550.0  # duck speed (for dynamic sprites)
    coyote_time: float = 0.25  # time within witch, you can jump after walking of the ground (in seconds)
    one_way: bool = False  # whether a static sprite collides downward
    orientation: Direction = Direction.NORTH  # which way a portal shoots / accepts sprites
    tunnel_id: str = "default"  # portals with the same tunnel_id link to each other


class SpriteInterface(ABC):
    rect: pygame.FRect
    name: str

    def __init__(self, data: SpriteInitData):
        pass

    @property
    @abstractmethod
    def pos(self) -> tuple[int, int]:
        """Center position of Sprite"""
        pass

    @pos.setter
    @abstractmethod
    def pos(self, value: str | float | SequenceLike[float] | pygame.Vector2) -> None:
        pass

    @property
    @abstractmethod
    def collision_rect(self) -> pygame.FRect:
        pass

    def update_physics(self, dt) -> None:
        pass

    @abstractmethod
    def interpolated_pos(self, dt: float) -> tuple[float, float]:
        pass

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2, dt: float) -> None:
        pass


class PhysicsSpriteInterface(SpriteInterface, ABC):
    def trigger(self, other: SpriteInterface | None) -> None:
        pass

    def untrigger(self, other: SpriteInterface | None) -> None:
        pass

    def left(self) -> None:
        pass

    def right(self) -> None:
        pass

    def jump(self) -> None:
        pass

    def duck(self) -> None:
        pass

    def act(self, dt: float) -> None:
        pass
