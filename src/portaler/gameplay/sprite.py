from __future__ import annotations

import pygame
from pygame.typing import SequenceLike

from ..interfaces import GameLevelInterface, SpriteInitData, SpriteInterface


class Sprite(pygame.sprite.Sprite, SpriteInterface):
    """
    Base sprite class.

    Implements Sprite Interface on top of pygame.Sprite objects for group stuff
    """

    rect: pygame.FRect

    def __init__(self, data: SpriteInitData):
        super().__init__()
        self.rect: pygame.FRect = pygame.FRect(data.rect)
        self.level: GameLevelInterface = data.level
        self.level.add_to_groups(self, *data.groups)

    @property
    def pos(self) -> tuple[float, float]:
        return self.rect.center

    @pos.setter
    def pos(self, value: SequenceLike[float]) -> None:
        self.rect.center = value[0], value[1]

    @property
    def collision_rect(self):
        return self.rect.copy()

    def interpolated_pos(self, dt_since_physics: float) -> tuple[float, float]:
        return self.pos

    def draw(self, surface, offset) -> None:
        pass
