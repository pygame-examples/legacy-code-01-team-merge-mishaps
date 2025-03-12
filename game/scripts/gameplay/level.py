from collections.abc import Callable
from typing import Awaitable

import pygame
from pygame.typing import RectLike

from ..interfaces import GameLevelInterface, SpriteInterface, SpriteInitData, GameInterface, Direction
from ..assets import LEVELS
from ..loaders import LevelLoader

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

        # Currently the only thing overwritten by the level loader
        self.groups["render"].view_range = pygame.FRect(0, 0, 1088, 320)

        self.loader = LevelLoader(self, LEVELS, "base")


    def init(self):
        """
        Spawn all sprites. Also, anything that needs to wait a frame or so before happening.
        
        I would put map loading here.
        """

        # NOTE: !!!!!! rect position, width and height are measured in tiles of 16px

        self.spawn(Block, SpriteInitData(
            rect=(2*16, 16*16, 64*16, 2*16),
            level=self,
        ))

        self.spawn(OneWayBlock, SpriteInitData(
            rect=(3*16, 10*16, 4*16, 1*16),
            level=self
        ))

        self.spawn(OneWayBlock, SpriteInitData(
            rect=(5*16, 5*16, 4*16, 1*16),
            level=self
        ))

        self.spawn(Player, SpriteInitData(
            rect=(2*16, 2*16, 2*16, 2*16),
            level=self,
        ),
        True
        )
        self.spawn(ThrowableBlock, SpriteInitData(
            rect=(11*16, 2*16, 2*16, 2*16),
            level=self,
        ))

        self.spawn(Portal, SpriteInitData(
            rect=(25*16, 11*16, 6*16, 1*16),
            level=self,
            properties={
                "orientation": Direction.SOUTH,
                "tunnel_id": "3"
            }
        ))
        self.spawn(Portal, SpriteInitData(
            rect=(11*16, 11*16, 6*16, 1*16),
            level=self,
            properties={
                "orientation": Direction.SOUTH,
                "tunnel_id": "3"
            }
        ))

    def set_camera_view(self, view: RectLike):
        self.groups["render"].view_range = pygame.FRect(view)

    def add_task(self, task: Awaitable) -> None:
        """Adds task to main game loop"""
        self.game.add_task(task)
