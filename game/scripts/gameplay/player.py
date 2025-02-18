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

    def update_physics(self, dt: float) -> None:
        return super().update_physics(dt)

    def draw(self, surface, dt_since_physics: float):
        new_rect: pygame.FRect = self.rect.copy()
        new_rect.center = self.interpolated_pos(dt_since_physics)
        pygame.draw.rect(surface, "red", new_rect, 2)

    