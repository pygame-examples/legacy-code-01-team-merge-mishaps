from __future__ import annotations

from math import ceil
from typing import ClassVar
from weakref import WeakSet

import pygame

from ..const import DOOR_CHANNEL
from ..interfaces import Axis, PhysicsType, SpriteInitData, SpriteInterface, SpritePhysicsData
from .physics import PhysicsSprite
from .sprites_and_sounds import get_image, play_sound


class Door(PhysicsSprite):
    # goofy implementation so that sound works with multiple doors
    sounding_doors: ClassVar[WeakSet[Door]] = WeakSet()

    def __init__(self, data: SpriteInitData) -> None:
        """
        A mechanical obstacle, designed to be impenetrable by any means.
        The only way to bypass this restricting beam of metal is to
        activate a button, wired up specifically to supress this beast and
        allow others to pass through previously unpassable barrier.
        """
        physics_data = SpritePhysicsData(
            physics_type=PhysicsType.ACTIVATED,
            orientation=data.properties["orientation"],
        )
        # sprite will be added to these groups later
        data.groups.extend(["physics", "render", "static-physics"])
        super().__init__(data, physics_data)

        self.orientation = data.properties["orientation"]  # TODO: axis is not direction
        if self.orientation.axis == Axis.VERTICAL:
            scale_factor = data.rect[2] // 32  # 32 is the width of the sprite in the unscaled image
        else:
            scale_factor = data.rect[3] // 32

        self.state = "closing"  # possible states: "opening", "closing"
        # HACK: apparently -32 needs to be added to each height
        self.max_height = (
            data.rect[3] if self.orientation.axis == Axis.VERTICAL else data.rect[2]
        ) - 32  # how big can the door opening be?
        self.min_height = 0 - 32  # how small can the door opening be?
        self.current_height = self.max_height  # currently CLOSED
        self.image_size = (
            self.rect.size if self.orientation.axis == Axis.VERTICAL else (self.rect.h, self.rect.w)
        )  # we sill draw the thing vertically, then rotate it

        self.draw_head = True  # whether to draw head of the door

        if self.orientation.axis == Axis.VERTICAL:
            head_rect = pygame.FRect(0, 0, self.rect.width, 16 * scale_factor)
            base_rect = pygame.FRect(
                0, self.rect.height - 16 * scale_factor, self.rect.width, 16 * scale_factor
            )
        else:
            head_rect = pygame.FRect(0, 0, 16 * scale_factor, self.rect.width)
            base_rect = pygame.FRect(
                0, self.rect.width - 16 * scale_factor, 16 * scale_factor, self.rect.width
            )
        self.head_rect = head_rect
        self.base_rect = base_rect

        self.middle_rect = self.rect.copy()
        self.duration = 1.0  # How long it takes to open fully

        spritesheet = get_image("pressure-door.png")
        self.segments = {  # the entire door will be drawn by segments
            "head": pygame.transform.scale_by(spritesheet.subsurface((0, 0, 32, 16)), scale_factor),
            "middle": pygame.transform.scale_by(spritesheet.subsurface((0, 16, 32, 16)), scale_factor),
            "base": pygame.transform.scale_by(spritesheet.subsurface((0, 32, 32, 16)), scale_factor),
            "tip": pygame.transform.scale_by(spritesheet.subsurface((32, 0, 32, 16)), scale_factor),
            "light-green": pygame.transform.scale_by(spritesheet.subsurface((32, 16, 32, 16)), scale_factor),
            "light-red": pygame.transform.scale_by(spritesheet.subsurface((32, 32, 32, 16)), scale_factor),
        }

        self.sound_name = "pressure-door.ogg"

    def update_physics(self, dt: float) -> None:
        super().update_physics(dt)
        # change height depending on the state
        total = self.max_height - self.min_height
        offset = total * dt / self.duration
        self.current_height += offset if self.state != "opening" else -offset
        self.current_height = min(max(self.current_height, self.min_height), self.max_height + 0.01)

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2, dt_since_physics: float) -> None:
        door_surface = pygame.Surface(self.image_size, pygame.SRCALPHA)

        # draw the bar
        times_to_draw_middle = ceil(self.current_height / self.segments["middle"].height) - 1
        door_surface.blit(self.segments["tip"], (0, self.current_height))
        for i in range(1, times_to_draw_middle + 2):
            pos = (0, self.current_height - i * self.segments["middle"].height)
            door_surface.blit(self.segments["middle"], pos)

        # rotate the bar, so it appears as if the whole thing is lowering
        # could this have been implemented better? Probably yes. But i don't care, if it works don't touch it
        door_surface = pygame.transform.rotate(door_surface, 180)

        # draw head and base
        if self.draw_head:
            door_surface.blit(self.segments["head"], self.head_rect)
        door_surface.blit(self.segments["base"], self.base_rect)

        # draw lights indicating opening and closing
        if self.state == "opening":
            door_surface.blit(self.segments["light-green"], self.base_rect)
        else:
            door_surface.blit(self.segments["light-red"], self.base_rect)

        if self.min_height < self.current_height < self.max_height:
            self.sounding_doors.add(self)
        else:
            self.sounding_doors.discard(self)
        if not self.sounding_doors:
            pygame.Channel(DOOR_CHANNEL).stop()
        elif not pygame.Channel(DOOR_CHANNEL).get_busy():
            # Keep playing sound continuously
            play_sound(self.sound_name, DOOR_CHANNEL, volume=0.25)
            # TODO: ANNOYING AHH SOUND, PLEASE MAKE A BETTER ONE

        # rotate the thing
        if self.orientation.axis == Axis.HORIZONTAL:
            door_surface = pygame.transform.rotate(door_surface, 90)

        # blit everything onto the screen
        surface.blit(door_surface, self.rect.move(-offset))

    def trigger(self, other: SpriteInterface | None):
        self.state = "opening"

    def untrigger(self, other: SpriteInterface | None):
        self.state = "closing"

    @property
    def collision_rect(self):
        if self.orientation.axis == Axis.VERTICAL:
            rect = pygame.Rect(
                self.rect.left + self.segments["middle"].width // 4,
                self.rect.bottom - self.current_height - self.segments["tip"].height,
                self.rect.width // 2,
                self.current_height + self.segments["tip"].height,
            )
        else:
            rect = pygame.Rect(
                self.rect.right - self.current_height - self.segments["tip"].height,
                self.rect.top + self.segments["middle"].width // 4,
                self.current_height + self.segments["tip"].height,
                self.rect.height // 2,
            )
        return rect
