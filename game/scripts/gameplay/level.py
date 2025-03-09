from collections.abc import Callable
from typing import Awaitable

import pygame

from ..interfaces import GameLevelInterface, SpriteInterface, SpriteInitData, GameInterface, Direction
from ..const import WINDOW_RESOLUTION

from .player import Player
from .block import Block, OneWayBlock, ThrowableBlock
from .portal import Portal
from .camera import Camera


class Level(GameLevelInterface):
    """
    Game state for gameplay
    
    This thing probably needs a camera as well as some map loading code. (camera implemented)
    I didn't want to decide nor spend the time on a map loading stack this early.
    """
    def __init__(self, game: GameInterface):
        self.groups: dict[str, pygame.sprite.AbstractGroup] = {
            "render": Camera(),
            "physics": pygame.sprite.Group(),
            "static-physics": pygame.sprite.Group(),
            "dynamic-physics": pygame.sprite.Group(),
            "throwable-physics": pygame.sprite.Group(), # currently not in use
            "trigger-physics": pygame.sprite.Group(),
            "portal-physics": pygame.sprite.Group(),
            "actors": pygame.sprite.Group(),
        }
        self.game: GameInterface = game
        self.groups["render"].view_range = pygame.FRect(0, 0, 1088, 320)


    def init(self):
        """
        Spawn all sprites. Also, anything that needs to wait a frame or so before happening.
        
        I would put map loading here.
        """
        self.spawn(Block, SpriteInitData(
            rect=(32, 256, 1024, 32),
            level=self,
        ))
        self.spawn(OneWayBlock, SpriteInitData(
            rect=(48, 150, 32, 32),
            level=self
        ))
        self.spawn(Player, SpriteInitData(
            rect=(32, 32, 32, 32),
            level=self,
        ),
        True
        )
        self.spawn(ThrowableBlock, SpriteInitData(
            rect=(132, 32, 32, 32),
            level=self,
        ))
        self.spawn(Portal, SpriteInitData(
            rect=(180, 160, 96, 8),
            level=self,
            properties={
                "orientation": Direction.NORTH,
                "tunnel_id": "tunnel2"
            }
        ))
        self.spawn(Portal, SpriteInitData(
            rect=(400, 160, 8, 96),
            level=self,
            properties={
                "orientation": Direction.WEST,
                "tunnel_id": "tunnel2"
            }
        ))


    def add_task(self, task: Awaitable) -> None:
        """Adds task to main game loop"""
        self.game.add_task(task)

    def spawn(self, cls: Callable[[SpriteInitData], SpriteInterface], data: SpriteInitData, target: bool = False) -> SpriteInterface:
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
            self.groups.setdefault(group, pygame.sprite.Group()).add(sprite)

    async def render(self, dt_since_physics: float) -> pygame.Surface:
        """
        Return a drawn surface.

        dt_since_physics is how much time since the last physics update and is used for position interpolation
        """
        surface: pygame.Surface = pygame.Surface(WINDOW_RESOLUTION).convert()
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
