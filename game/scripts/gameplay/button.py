import pygame

from ..interfaces import SpriteInitData, SpritePhysicsData, PhysicsType, SpriteInterface
from .physics import PhysicsSprite

class Button(PhysicsSprite):
    def __init__(self, data: SpriteInitData):
        physics_data = SpritePhysicsData(
            physics_type=PhysicsType.TRIGGER
        )
        # sprite will be added to these groups later
        data.groups.extend(["physics", "render", "triggerable"])
        super().__init__(data, physics_data)

        self.linked_to: list[PhysicsSprite] = data.properties["linked-to"]

        image = pygame.image.load("game/assets/sprites/button.png").convert_alpha()

        scale_factor = data.rect[2] // 32  # 32 is the width of the sprite in the unscaled image
        self.states = {
            "rest": pygame.transform.scale_by(image.subsurface((0, 0, 32, 16)),  scale_factor),
            "triggered": pygame.transform.scale_by(image.subsurface((32, 0, 32, 16)),  scale_factor)
        }
        self.state = "rest"
        self.image = self.states[self.state]
    
    def draw(self, surface: pygame.Surface, offset: pygame.Vector2, dt_since_physics: float) -> None:
        new_rect = self.rect.copy()
        new_rect.center = new_rect.center - offset
        surface.blit(self.states[self.state], new_rect)
    
    def trigger(self, other: SpriteInterface):
        self.state = "triggered"
        self.linked_to.trigger(self)
    
    def untrigger(self):
        self.state = "rest"
        self.linked_to.untrigger(self)
