import pygame

from ..const import TILE_SIZE
from ..interfaces import THROWABLE_TYPE_INTO_WEIGHT, PhysicsType
from .physics import PhysicsSprite, SpriteInitData, SpritePhysicsData
from .sprites_and_sounds import get_image


class Block(PhysicsSprite):
    """Static block that you run into"""

    def __init__(self, data: SpriteInitData):
        physics_data = SpritePhysicsData(physics_type=PhysicsType.STATIC)
        data.groups.extend(["render", "physics", "static-physics"])
        super().__init__(data, physics_data)
        self.surface = data.properties["surface"]

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2, dt_since_physics: float):
        new_rect = self.rect.copy()
        new_rect.center = new_rect.center - offset
        surface.blit(self.surface, new_rect)


class OneWayBlock(PhysicsSprite):
    """You can jump up through and duck down through this block"""

    def __init__(self, data: SpriteInitData):
        physics_data = SpritePhysicsData(physics_type=PhysicsType.STATIC, one_way=True)
        data.groups.extend(["render", "physics", "static-physics"])
        super().__init__(data, physics_data)

        width = data.rect[2] // TILE_SIZE
        self.image = pygame.Surface(
            (width * 16, 16), pygame.SRCALPHA
        )  # this forgotten SRCALPHA flag costed me 30 mins of debugging >:[
        spritesheet = get_image("one-way-platform.png")

        if width == 1:
            self.image.blit(spritesheet.subsurface((48, 0, 16, 16)), (0, 0))
        else:
            for i in range(width):
                if i == 0:  # left-most bit of the platform
                    self.image.blit(spritesheet.subsurface((0, 0, 16, 16)), (16 * i, 0))
                elif i == (width - 1):  # right-most bit of the platform
                    self.image.blit(spritesheet.subsurface((32, 0, 16, 16)), (16 * i, 0))
                else:  # middle segment of the platform
                    self.image.blit(spritesheet.subsurface((16, 0, 16, 16)), (16 * i, 0))
        scale_factor = data.rect[2] // self.image.width
        self.image = pygame.transform.scale_by(self.image, scale_factor).convert_alpha()

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2, dt_since_physics: float):
        new_rect = self.rect.copy()
        new_rect.center = new_rect.center - offset
        surface.blit(self.image, new_rect)


class ThrowableBlock(PhysicsSprite):
    """Meant for being picked up and thrown"""

    def __init__(self, data: SpriteInitData):
        physics_data = SpritePhysicsData(
            physics_type=PhysicsType.DYNAMIC,
            weight=THROWABLE_TYPE_INTO_WEIGHT[data.properties["id"]],
        )

        data.groups.extend(["render", "physics", "dynamic-physics", "throwable-physics"])
        super().__init__(data, physics_data)
        self.image = get_image("cube.png").subsurface((data.properties["id"] * 16, 0, 16, 16))
        scale_factor = self.rect.width // 16  # 16 is the width of the unscaled sprite
        self.image = pygame.transform.scale_by(self.image, scale_factor)
