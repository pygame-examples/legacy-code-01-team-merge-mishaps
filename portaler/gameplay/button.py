import pygame

from ..const import BUTTON_CHANNEL
from ..interfaces import PhysicsType, SpriteInitData, SpriteInterface, SpritePhysicsData
from .animation import Animation
from .physics import PhysicsSprite
from .sprites_and_sounds import get_image, play_sound


class Button(PhysicsSprite):
    def __init__(self, data: SpriteInitData):
        """
        A simple mechanism, designed to activate complex machinery inside the facility.
        """
        physics_data = SpritePhysicsData(physics_type=PhysicsType.TRIGGER)
        # sprite will be added to these groups later
        data.groups.extend(["physics", "render", "triggerable"])
        super().__init__(data, physics_data)

        self.linked_to: list[PhysicsSprite] = data.properties["linked-to"]

        scale_factor = data.rect[2] // 32  # 32 is the width of the sprite in the unscaled image
        self.states = {
            "rest": pygame.transform.scale_by(
                get_image("button.png").subsurface((0, 0, 32, 16)), scale_factor
            ),
            "triggered": pygame.transform.scale_by(
                get_image("button.png").subsurface((32, 0, 32, 16)), scale_factor
            ),
        }
        self.state = "rest"
        self.image = self.states[self.state]

        self.previous_state = "rest"

        self.sound_names = {
            "press": "button-press.ogg",
            "unpress": "unpress.ogg",
        }

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2, dt_since_physics: float) -> None:
        surface.blit(self.states[self.state], self.rect.move(-offset))

    def trigger(self, other: SpriteInterface | None):
        self.state = "triggered"

        if self.previous_state != self.state:
            play_sound(self.sound_names["press"], BUTTON_CHANNEL)

        for activator in self.linked_to:
            activator.trigger(self)

        self.previous_state = self.state

    def untrigger(self, other: SpriteInterface | None):
        self.state = "rest"

        if self.previous_state != self.state:
            play_sound(self.sound_names["unpress"], BUTTON_CHANNEL)

        for activator in self.linked_to:
            activator.untrigger(self)

        self.previous_state = self.state


class FinishButton(PhysicsSprite):
    def __init__(self, data: SpriteInitData):
        """
        A simple mechanism, designed to activate complex machinery inside the facility.
        """
        physics_data = SpritePhysicsData(physics_type=PhysicsType.TRIGGER)
        # sprite will be added to these groups later
        data.groups.extend(["physics", "render", "triggerable"])
        super().__init__(data, physics_data)
        self.animation = Animation("finish.png", 10, frame_count=2, scale_factor=2)
        self.data = data

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2, dt_since_physics: float) -> None:
        self.animation.update(dt_since_physics)
        surface.blit(self.animation.get_frame(), self.rect.move(-offset))

    def trigger(self, other: SpriteInterface | None):
        self.data.level.game.state_stack.pop()

        from .level import Level

        next_level = Level(self.data.level.game)
        next_level.level_count = self.data.level.level_count + 1
        self.data.level.game.state_stack.append(next_level)
        next_level.init()
