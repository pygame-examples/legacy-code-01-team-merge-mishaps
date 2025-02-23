import pygame

from ..interfaces import PhysicsType
from .physics import PhysicsSprite, SpriteInitData, SpritePhysicsData

class Block(PhysicsSprite):
    """Static block that you run into"""
    def __init__(self, data: SpriteInitData):
        physics_data = SpritePhysicsData(
            physics_type=PhysicsType.STATIC,
        )
        data.groups.extend(["render", "physics", "static-physics"])
        super().__init__(data, physics_data)

    def draw(self, surface: pygame.Surface, dt_since_physics: float):
        pygame.draw.rect(surface, "blue", self.rect)


class OneWayBlock(PhysicsSprite):
    """You can jump up through and duck down through this block"""
    def __init__(self, data: SpriteInitData):
        physics_data = SpritePhysicsData(
            physics_type=PhysicsType.STATIC,
            one_way=True
        )
        data.groups.extend(["render", "physics", "static-physics"])
        super().__init__(data, physics_data)

    def draw(self, surface: pygame.Surface, dt_since_physics: float):
        pygame.draw.rect(surface, "yellow", self.rect)