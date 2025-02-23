import pygame

from .physics import PhysicsSprite
from ..interfaces import SpriteInitData, SpritePhysicsData, PhysicsType

class Player(PhysicsSprite):
    def __init__(self, data: SpriteInitData):
        physics_data = SpritePhysicsData(
            physics_type=PhysicsType.DYNAMIC,
            weight=10,
            horizontal_speed=196,
            jump_speed=500,
            duck_speed=200,
        )
        # sprite will be added to these groups later
        data.groups.extend(["player", "physics", "render", "dynamic-physics"])
        super().__init__(data, physics_data)
        self.image = pygame.Surface(self.rect.size, pygame.SRCALPHA).convert_alpha()
        pygame.draw.rect(self.image, "red", (0, 0, *self.rect.size), 2)
    