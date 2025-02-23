import pygame

from ..interfaces import SpriteInitData, SpritePhysicsData, PhysicsType, Direction, PhysicsSpriteInterface

from .physics import PhysicsSprite

class Portal(PhysicsSprite):
    def __init__(self, data: SpriteInitData):
        data.groups.extend(["render", "physics", "portal-physics", data.properties["tunnel_id"]])
        physics_data = SpritePhysicsData(
            physics_type=PhysicsType.PORTAL,
            orientation=data.properties["orientation"],
            tunnel_id=data.properties["tunnel_id"],
        )
        super().__init__(data, physics_data)

    def draw(self, surface: pygame.Surface, dt_since_physics: float) -> None:
        pygame.draw.rect(surface, "green", self.rect)

    def receive(self, sprite: PhysicsSprite):
        if self.orientation == Direction.NORTH:
            sprite.rect.top = self.rect.centery
            sprite.velocity = pygame.Vector2(0, -1) * sprite.velocity.length()
        if self.orientation == Direction.SOUTH:
            sprite.rect.bottom = self.rect.centery
            sprite.velocity = pygame.Vector2(0, 1) * sprite.velocity.length()
        