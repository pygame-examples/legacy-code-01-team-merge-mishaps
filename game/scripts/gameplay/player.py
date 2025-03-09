import pygame

from .physics import PhysicsSprite
from ..interfaces import SpriteInitData, SpritePhysicsData, PhysicsType
from ..const import Actions
from ..game_input import input_state


class Player(PhysicsSprite):
    """Player sprite"""
    def __init__(self, data: SpriteInitData):
        physics_data = SpritePhysicsData(
            physics_type=PhysicsType.DYNAMIC,
            weight=10,
            horizontal_speed=30,
            horizontal_air_speed=25,
            friction=20,
            air_friction=0.1,
            jump_speed=55,
            duck_speed=100,
            yeet_force=1000,
        )
        # sprite will be added to these groups later
        data.groups.extend(["physics", "render", "dynamic-physics", "actors"])
        super().__init__(data, physics_data)
        self.image = pygame.Surface(self.rect.size, pygame.SRCALPHA).convert_alpha()
        pygame.draw.rect(self.image, "red", (0, 0, *self.rect.size), 2)

    def act(self, dt: float):
        if input_state.get(Actions.LEFT):
            self.left(dt)
        if input_state.get(Actions.RIGHT):
            self.right(dt)

        if input_state.get(Actions.UP):
            self.jump(dt)

        if input_state.get(Actions.DOWN):
            self.duck(dt)

        if input_state.get_just(Actions.INTERACT):
            self.interact(dt)
