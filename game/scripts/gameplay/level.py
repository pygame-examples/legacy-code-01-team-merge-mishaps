from collections.abc import Callable
from typing import Awaitable

import pygame

from ..interfaces import GameLevelInterface, SpriteInterface, SpriteInitData, GameInterface
from ..const import WINDOW_RESOLUTION

from .player import Player
from .block import Block, OneWayBlock
from .sprite_controller import InputController


class Level(GameLevelInterface):
    def __init__(self, game: GameInterface):
        self.groups: dict[str, pygame.sprite.AbstractGroup] = {
            "render": pygame.sprite.LayeredUpdates(),
            "physics": pygame.sprite.Group(),
            "static-physics": pygame.sprite.Group(),
            "dynamic-physics": pygame.sprite.Group(),
            "trigger-physics": pygame.sprite.Group(),
        }
        self.game: GameInterface = game

    def init(self):
        self.spawn(Player, SpriteInitData(
            rect=(32, 32, 32, 32),
            level=self,
            controller=InputController(),
        ))
        self.spawn(Block, SpriteInitData(
            rect=(32, 256, 96, 32),
            level=self,
        ))
        self.spawn(OneWayBlock, SpriteInitData(
            rect=(48, 150, 32, 32),
            level=self
        ))

    def add_task(self, task: Awaitable) -> None:
        self.game.add_task(task)

    def spawn(self, cls: Callable[[SpriteInitData], SpriteInterface], data: SpriteInitData) -> SpriteInterface:
        return cls(data)

    def get_group(self, group_name: str) -> pygame.sprite.AbstractGroup:
        return self.groups.get(group_name)
    
    def add_to_groups(self, sprite: SpriteInterface, *groups: str) -> None:
        for group in groups:
            self.groups.setdefault(group, pygame.sprite.Group()).add(sprite)

    def render(self, dt_since_physics: float) -> pygame.Surface:
        surface: pygame.Surface = pygame.Surface(WINDOW_RESOLUTION).convert()
        surface.fill("black")
        for sprite in self.get_group("render"):
            sprite.draw(surface, dt_since_physics)
        return surface

    def update_physics(self, dt):
        for sprite in self.get_group("physics"):
            sprite.update_physics(dt)