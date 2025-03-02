import pygame

from ..interfaces import SpriteInitData, SpritePhysicsData, PhysicsType, Direction, PhysicsSpriteInterface

from .physics import PhysicsSprite

class Portal(PhysicsSprite):
    """
    Dynamic sprites can teleport through these

    Must be instantiated in pairs with the same "tunnel_id" data property.
    Necessary data properties:
     - tunnel_id: must be same value as twin portal.  I recommend strings.
     - orientation: a Direction enum value.  Which directions sprites are going when they EXIT this portal.
        they exit the other direction
    """
    def __init__(self, data: SpriteInitData):
        data.groups.extend(["render", "physics", "portal-physics", data.properties["tunnel_id"]])
        physics_data = SpritePhysicsData(
            physics_type=PhysicsType.PORTAL,
            orientation=data.properties["orientation"],
            tunnel_id=data.properties["tunnel_id"],
        )
        super().__init__(data, physics_data)

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2, dt_since_physics: float) -> None:
        new_rect = self.rect.copy()
        new_rect.center = new_rect.center - offset
        pygame.draw.rect(surface, "green", new_rect)

    def receive(self, sprite: PhysicsSprite):
        if self.orientation == Direction.NORTH:
            sprite.rect.top = self.rect.centery
            sprite.velocity = pygame.Vector2(0, -1) * sprite.velocity.length()
        if self.orientation == Direction.SOUTH:
            sprite.rect.bottom = self.rect.centery
            sprite.velocity = pygame.Vector2(0, 1) * sprite.velocity.length()
        
