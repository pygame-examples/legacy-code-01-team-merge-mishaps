import pygame

from ..const import Actions
from ..game_input import input_state
from ..interfaces import PhysicsType, SpriteInitData, SpritePhysicsData
from .physics import PhysicsSprite
from .sprites_and_sounds import get_image


class Player(PhysicsSprite):
    """Player sprite"""

    def __init__(self, data: SpriteInitData):
        physics_data = SpritePhysicsData(
            physics_type=PhysicsType.DYNAMIC,  # Use the defaults
            weight=100.0,
            air_damping=0.002,
        )
        # sprite will be added to these groups later
        data.groups.extend(["physics", "render", "dynamic-physics", "actors"])
        super().__init__(data, physics_data)

        scale_factor = data.rect[2] // 16  # 16 is the width of the unscaled player sprite
        self.image = pygame.transform.scale_by(get_image("player.png"), scale_factor).convert_alpha()

        self.last_down_press = 0
        self.timer = 0
        self.double_press_time = 0.2  # 200 milliseconds

    def get_facing(self):  # player has a different way of calculating 'facing' value
        self.facing.x = input_state.get(Actions.RIGHT) - input_state.get(Actions.LEFT)
        self.facing.y = input_state.get(Actions.DOWN) - (
            input_state.get(Actions.UP) or input_state.get(Actions.JUMP)
        )

    def act(self, dt: float):
        if input_state.get(Actions.LEFT):
            self.left(dt)

        if input_state.get(Actions.RIGHT):
            self.right(dt)

        if input_state.get(Actions.JUMP):
            self.jump(dt)

        if input_state.get_just(Actions.INTERACT):
            self.interact(dt)

        if input_state.get_just(Actions.DOWN):  # slam on double-press
            if self.timer - self.last_down_press <= self.double_press_time:
                self.duck(dt)
            self.last_down_press = self.timer

        self.timer += dt
