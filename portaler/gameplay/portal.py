import pygame

from ..interfaces import DIRECTION_TO_ANGLE, PhysicsType, SpriteInitData, SpritePhysicsData
from .animation import ANIMATIONMYWAY
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

        rotation = -DIRECTION_TO_ANGLE[self.orientation] - 90  # it works
        self.animation = ANIMATIONMYWAY(
            f"portals/portal{data.properties['tunnel_id']}.png",
            12,
            frame_count=7,
            scale_factor=2,
            rotation=rotation,
        )
        self.sound_name = "teleport.ogg"

    def update_physics(self, dt: float) -> None:
        super().update_physics(dt)
        self.animation.update(dt)

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2, dt_since_physics: float) -> None:
        surface.blit(self.animation.get_frame(), self.rect.move(-offset))
