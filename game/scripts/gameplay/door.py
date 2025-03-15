import pygame

from ..interfaces import SpriteInitData, SpritePhysicsData, PhysicsType, SpriteInterface, Axis
from .physics import PhysicsSprite
from math import ceil


class Door(PhysicsSprite):
    def __init__(self, data: SpriteInitData):
        physics_data = SpritePhysicsData(
            physics_type=PhysicsType.ACTIVATED,
            orientation=data.properties["orientation"]
        )
        # sprite will be added to these groups later
        data.groups.extend(["physics", "render", "static-physics"])
        super().__init__(data, physics_data)

        image = pygame.image.load("game/assets/sprites/pressure-door.png").convert_alpha()

        scale_factor = data.rect[2] // 32  # 32 is the width of the sprite in the unscaled image

        self.state = "closing"  # "opening" or "closing"
        self.max_height = data.rect[3]  # max height of the oppening in the door
        self.min_height = 0  # smallest height of the oppening in the door
        self.current_height = self.max_height

        if data.properties["orientation"] == Axis.VERTICAL:
            self.head_rect = pygame.FRect(0, 0, self.rect.width, 16*scale_factor)
            self.base_rect = pygame.FRect(0, self.rect.height-16*scale_factor, self.rect.width, 16*scale_factor)
        elif data.properties["orietation"] == Axis.HORIZONTAL:
            self.head_rect = pygame.FRect(0, 0, 16*scale_factor, self.rect.width)
            self.base_rect = pygame.FRect(0, self.rect.width-16*scale_factor, 16*scale_factor, self.rect.width)

        self.middle_rect = self.rect.copy()

        self.segments = {   # the entire door will be drawn by segments
            "head": pygame.transform.scale_by(image.subsurface((0, 0, 32, 16)), scale_factor),
            "middle": pygame.transform.scale_by(image.subsurface((0, 16, 32, 16)), scale_factor),
            "base": pygame.transform.scale_by(image.subsurface((0, 32, 32, 16)), scale_factor),
            "tip": pygame.transform.scale_by(image.subsurface((32, 0, 32, 16)), scale_factor),
            "light-green": pygame.transform.scale_by(image.subsurface((32, 16, 32, 16)), scale_factor),
            "light-red": pygame.transform.scale_by(image.subsurface((32, 32, 32, 16)), scale_factor)
        }

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2, dt_since_physics: float) -> None:
        door_surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)

        # draw the bar
        times_to_draw_middle = ceil(self.current_height / self.segments["middle"].height) - 1
        door_surface.blit(self.segments["tip"], (0, self.current_height))
        for i in range(1, times_to_draw_middle+2):
            pos = (0, self.current_height - i * self.segments["middle"].height)
            door_surface.blit(self.segments["middle"], pos)
        
        door_surface = pygame.transform.rotate(door_surface, 180)

        # draw head and base
        door_surface.blit(self.segments["head"], (0, 0, self.head_rect.width, self.head_rect.height))
        door_surface.blit(self.segments["base"], (0, self.base_rect.y - self.head_rect.y, self.base_rect.width, self.base_rect.height))

        # change height depending on the state
        if self.state == "opening":
            self.current_height -= self.segments["middle"].height*dt_since_physics
        else:
            self.current_height += self.segments["middle"].height*dt_since_physics
        self.current_height = min(max(self.current_height, self.min_height), self.max_height)

        # blit everything onto the screen
        new_rect = self.rect.copy()
        new_rect.center = new_rect.center - offset

        surface.blit(door_surface, new_rect)
    
    def trigger(self, other: SpriteInterface):
        self.state = "opening"
    
    def untrigger(self, other: SpriteInterface):
        self.state = "closing"

    @property
    def collision_rect(self):
        return pygame.Rect(self.rect.left, self.rect.bottom - self.current_height - self.segments["tip"].height, self.rect.width, self.current_height)
