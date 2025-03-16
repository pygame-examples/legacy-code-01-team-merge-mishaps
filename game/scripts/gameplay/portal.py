import pygame

from ..interfaces import SpriteInitData, SpritePhysicsData, PhysicsType, Direction, PhysicsSpriteInterface, DIRECTION_TO_ANGLE

from .physics import PhysicsSprite

from .animation import ANIMATIONMYWAY
from .sprites_and_sounds import get_sfx

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

        rotation = DIRECTION_TO_ANGLE[self.orientation] - 90 # - 90 because the portal is FACING in that direciton
        # this is not in the consts_pg_loaded.py because the inherently can't be portals with the same sprites in the same level
        self.animation = ANIMATIONMYWAY(f"game/assets/sprites/portals/portal{data.properties["tunnel_id"]}.png", 5, frame_count=7, scale_factor=2, rotation=rotation)
        self.sound = get_sfx("game/assets/sfx/teleport.ogg")

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2, dt_since_physics: float) -> None:
        new_rect = self.rect.copy()
        new_rect.center = new_rect.center - offset
        self.animation.update(dt_since_physics)
        surface.blit(self.animation.get_frame(), new_rect)
        
