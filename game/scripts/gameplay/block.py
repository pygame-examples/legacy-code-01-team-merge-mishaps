import pygame

from ..interfaces import PhysicsType
from .physics import PhysicsSprite, SpriteInitData, SpritePhysicsData

class Block(PhysicsSprite):
    """Static block that you run into"""
    def __init__(self, data: SpriteInitData):
        physics_data = SpritePhysicsData(
            physics_type=PhysicsType.STATIC
        )
        data.groups.extend(["render", "physics", "static-physics"])
        super().__init__(data, physics_data)

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2, dt_since_physics: float):
        new_rect = self.rect.copy()
        new_rect.center = new_rect.center - offset

        pygame.draw.rect(surface, "blue", new_rect)


class OneWayBlock(PhysicsSprite):
    """You can jump up through and duck down through this block"""
    def __init__(self, data: SpriteInitData):
        physics_data = SpritePhysicsData(
            physics_type=PhysicsType.STATIC,
            one_way=True
        )
        data.groups.extend(["render", "physics", "static-physics"])
        super().__init__(data, physics_data)

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2, dt_since_physics: float):
        new_rect = self.rect.copy()
        new_rect.center = new_rect.center - offset
        pygame.draw.rect(surface, "yellow", new_rect)

class ThrowableBlock(PhysicsSprite):
    """Meant for being picked up and thrown"""
    def __init__(self, data: SpriteInitData):
        physics_data = SpritePhysicsData(
            physics_type=PhysicsType.DYNAMIC,
            weight=20,
        )

        data.groups.extend(["render", "physics", "dynamic-physics", "throwable-physics"])
        super().__init__(data, physics_data)
        self.image = pygame.image.load("game/assets/sprites/cube.png").convert_alpha()
        scale_factor = self.rect.width // 16
        self.image = pygame.transform.scale_by(self.image, scale_factor)
        print(self.rect)
        # pygame.draw.rect(self.image, "red", (0, 0, *self.rect.size))

