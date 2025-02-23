import pygame
from pygame.typing import SequenceLike

from ..interfaces import SpriteInterface, SpriteInitData, SpriteControllerInterface, GameLevelInterface


class Sprite(pygame.sprite.Sprite, SpriteInterface):
    """
    Base sprite class.  
    
    Implements Sprite Interface on top of pygame.Sprite objects for group stuff
    """
    def __init__(self, data: SpriteInitData):
        super().__init__()
        self.controller: SpriteControllerInterface = data.controller
        self.rect: pygame.FRect = pygame.FRect(data.rect)
        self.level: GameLevelInterface = data.level
        self.level.add_to_groups(self, *data.groups)
        self.level.add_task(self.controller.run())

    @property
    def pos(self) -> tuple[int, int]:
        return self.rect.center
    
    @pos.setter
    def pos(self, value: str | float | SequenceLike[float] | pygame.Vector2) -> None:
        self.rect.center = pygame.Vector2(value)

    def interpolated_pos(self, dt_since_physics) -> tuple[int, int]:
        return self.pos

    def draw(self, surface) -> None:
        pass