from __future__ import annotations

from typing import ClassVar
from weakref import WeakSet

import pygame

from ..const import LIFTER_CHANNEL, TILE_SIZE
from ..interfaces import HeightChangeState, PhysicsType, SpriteInitData, SpriteInterface, SpritePhysicsData
from .physics import PhysicsSprite
from .sprites_and_sounds import get_image, play_sound


class Lifter(PhysicsSprite):
    # goofy implementation so that sound works with multiple lifters
    sounding_lifters: ClassVar[WeakSet[Lifter]] = WeakSet()

    def __init__(self, data: SpriteInitData) -> None:
        """
        A machine of Herculean power.
        Able to lift any object, no matter the weight.
        """
        physics_data = SpritePhysicsData(physics_type=PhysicsType.ACTIVATED)
        # sprite will be added to these groups later
        data.groups.extend(["physics", "render", "static-physics"])
        super().__init__(data, physics_data)

        scale_factor = TILE_SIZE // 16  # 16 is the width of the sprite in the unscaled image

        self.default_state = data.properties["starting_state"]
        self.state = data.properties["starting_state"]

        self.max_height = data.rect[3] - 5 * scale_factor
        self.min_height = -0.01
        self.current_height = (
            self.max_height if self.state == HeightChangeState.HIGHTENING else self.min_height
        )

        self.duration = 1.0  # How long it takes to lower/lift fully

        spritesheet = get_image("lifter.png")
        self.segments = {
            "beam": pygame.transform.scale_by(spritesheet.subsurface((16, 48, 16, 16)), scale_factor),
            "beam-end": pygame.transform.scale_by(spritesheet.subsurface((16, 32, 16, 16)), scale_factor),
            "platform-left-smooth": pygame.transform.scale_by(
                spritesheet.subsurface((0, 27, 16, 16)), scale_factor
            ),
            "platfotm-left-sharp": pygame.transform.scale_by(
                spritesheet.subsurface((0, 11, 16, 16)), scale_factor
            ),
            "platform-right-smooth": pygame.transform.scale_by(
                spritesheet.subsurface((32, 27, 16, 16)), scale_factor
            ),
            "platfotm-right-sharp": pygame.transform.scale_by(
                spritesheet.subsurface((32, 11, 16, 16)), scale_factor
            ),
            "platfotm-middle": pygame.transform.scale_by(
                spritesheet.subsurface((16, 27, 16, 16)), scale_factor
            ),
            "platform-singular": pygame.transform.scale_by(
                spritesheet.subsurface((16, 11, 16, 16)), scale_factor
            ),
        }

        self.sound_name = "pressure-door.ogg"  # for now the same as the door

        self.image_size = data.rect.size

        # get the lifter platform
        self.lifter_platform_image = pygame.Surface((data.rect[2], 5 * scale_factor), pygame.SRCALPHA)

        if data.properties["segments"] == 1:
            self.lifter_platform_image.blit(self.segments["platform-singular"], (0, 0))
        else:
            for i in range(data.properties["segments"]):
                x = i * TILE_SIZE
                current_segment = None
                if i == 0:
                    if data.properties["is_left_sharp"]:
                        current_segment = self.segments["platform-left-sharp"]
                    else:
                        current_segment = self.segments["platform-left-smooth"]
                elif i == data.properties["segments"] - 1:
                    if data.properties["is_right_sharp"]:
                        current_segment = self.segments["platform-right-sharp"]
                    else:
                        current_segment = self.segments["platform-right-smooth"]
                else:
                    current_segment = self.segments["platform-middle"]

                self.lifter_platform_image.blit(current_segment, (x, 0))

        self.beam_image = pygame.Surface((TILE_SIZE, data.rect[3]), pygame.SRCALPHA)
        height = int(data.rect[3] // TILE_SIZE)
        for i in range(height):
            if i == 0:
                self.beam_image.blit(self.segments["beam-end"], (0, i * TILE_SIZE))
            else:
                self.beam_image.blit(self.segments["beam"], (0, i * TILE_SIZE))

    def update_physics(self, dt: float) -> None:
        super().update_physics(dt)

        # change height depending on the state
        total = self.max_height - self.min_height
        offset = total * dt / self.duration
        self.current_height += offset if self.state == HeightChangeState.LOWERING else -offset
        self.current_height = min(max(self.current_height, self.min_height), self.max_height + 0.01)

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2, dt: float) -> None:
        lifter_surface = pygame.Surface(self.image_size, pygame.SRCALPHA)

        lifter_surface.blit(self.beam_image, ((lifter_surface.width - self.beam_image.width) // 2, 0))
        lifter_surface.blit(self.lifter_platform_image, (0, self.current_height))

        if self.min_height < self.current_height < self.max_height:
            self.sounding_lifters.add(self)
        else:
            self.sounding_lifters.discard(self)
        if not self.sounding_lifters:
            pygame.Channel(LIFTER_CHANNEL).stop()
        elif not pygame.Channel(LIFTER_CHANNEL).get_busy():
            # Keep playing sound continuously
            play_sound(self.sound_name, LIFTER_CHANNEL, volume=0.25)
            # TODO: ANNOYING AHH SOUND, PLEASE MAKE A BETTER ONE

        # blit everything onto the screen
        surface.blit(lifter_surface, self.rect.move(-offset))

    def trigger(self, other: SpriteInterface | None):
        self.state = (
            HeightChangeState.HIGHTENING
            if self.default_state == HeightChangeState.LOWERING
            else HeightChangeState.LOWERING
        )

    def untrigger(self, other: SpriteInterface | None):
        self.state = self.default_state

    @property
    def collision_rect(self):
        scale_factor = TILE_SIZE // 16
        rect = pygame.Rect(
            self.rect.left,
            self.rect.bottom - (self.max_height - self.current_height + 5 * scale_factor),
            self.rect.width,
            5 * scale_factor,
        )
        return rect
