"""
This file is full of interfaces, dataclasses, and enums for type hinting.
I put in type hints for methods intended to be called by external code.

Classes implementing these interfaces should be subclasses of them.

Do not import any other parts of this project here.
Do not add any implementations here.

Or suffer JiffyRob's wrath
"""
from __future__ import annotations

import pathlib
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable

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

    async def update_actors(self, dt: float) -> None:
        pass

    async def update_physics(self, dt: float) -> None:
        pass

    async def render(self, size: tuple[int, int], dt_since_physics: float) -> pygame.Surface:
        pass


class GameLevelInterface(GameStateInterface, ABC):
    groups: dict[str, pygame.sprite.AbstractGroup]

    def spawn(self, cls: Callable[[SpriteInitData], SpriteInterface], data: SpriteInitData,
              target: bool = False) -> SpriteInterface:
        """Spawn a new sprite"""
        sprite = cls(data)
        if target:
            self.get_group("render").set_target(sprite)
        return sprite

    def get_group(self, group_name: str) -> pygame.sprite.AbstractGroup:
        """
        Get a sprite group from a string

        Returns None if group does not exist
        """
        return self.groups.get(group_name)

    def add_to_groups(self, sprite: SpriteInterface, *groups: str) -> None:
        """
        Add a sprite to the given string groups

        Will create new ones if the groups do not exist
        """
        for group in groups:
            self.groups.setdefault(group, pygame.sprite.Group()).add(sprite)  # somehow creates a new group ????

    @abstractmethod
    def set_camera_view(self, view: RectLike):
        pass

    async def render(self, size: tuple[int, int], dt_since_physics: float) -> pygame.Surface:
        """
        Return a drawn surface.

        dt_since_physics is how much time since the last physics update and is used for position interpolation
        """
        surface: pygame.Surface = pygame.Surface(size).convert()
        surface.fill("black")
        self.get_group("render").draw(surface, dt_since_physics)
        return surface

    async def update_actors(self, dt):
        for sprite in self.get_group("actors"):
            sprite.act(dt)

    async def update_physics(self, dt):
        """
        Update the physics in this level
        """
        for sprite in self.get_group("physics"):
            sprite.update_physics(dt)



@dataclass
class SpriteInitData:
    # Object used to init sprites with
    # Add stuff here as necessary
    rect: RectLike  # initial position and size of sprite
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
    yeet_force: float = 0.5  # flight speed (for dynamic sprites)
    horizontal_speed: float = 30  # walking speed (for dynamic sprites)
    horizontal_air_speed: float = 25  # movement speed for dynamic sprites that are in the air
    friction: float = 20  # amount by which acceleration changes (for dynamic sprites)
    air_friction: float = 0.1 # amount by which acceleration changes (for dynamic sprites) when in the air
    jump_speed: float = 55  # jump speed (for dynamic sprites)
    duck_speed: float = 100  # duck speed (for dynamic sprites)
    coyote_time: float = 0.25  # time within witch, you can jump after walking of the ground (in seconds)
    one_way: bool = False  # whether a static sprite collides downward
    orientation: Direction = Direction.NORTH  # which way a portal shoots / accepts sprites
    tunnel_id: str = "default"  # portals with the same tunnel_id link to each other


class SpriteInterface(ABC):
    rect: pygame.FRect

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

    def interpolated_pos(self, dt_since_physics: float) -> None:
        pass

    def draw(self, surface: pygame.Surface, dt_since_physics: float) -> None:
        pass


class PhysicsSpriteInterface(SpriteInterface, ABC):
    def trigger(self, other: SpriteInterface) -> None:
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
