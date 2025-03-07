from __future__ import annotations

import pygame

from .sprite import Sprite


class Camera(pygame.sprite.LayeredUpdates):
    """
    Camera group, meant for following a specific sprite while rendering

    TODO:
        1) fix the jitteryness of the camera - DONE!
        2) add a screen shake for when objects collide >:]
        3) add constraining rect for camera
    """
    def __init__(self) -> None:
        super().__init__()
        self.target: Sprite | None = None
        self.offset = pygame.Vector2(0, 0)
        self.follow_coefficient = 1/50

    def draw(self, surface: pygame.Surface, dt: float = 1) -> None:
        if self.target:
            pos = self.target.interpolated_pos(dt) - self.offset
            view_frect = surface.get_frect(center=(0,0))
            view_frect.scale_by_ip(0.25)
            self.offset.x += min(pos.x - view_frect.left, 0) + max(pos.x - view_frect.right, 0)
            self.offset.y += min(pos.y - view_frect.top, 0) + max(pos.y - view_frect.bottom, 0)

        # Offset the camera to the center of the screen and round it, because there are sprites with fractional position
        # and due to rounding errors, they would appear jittery
        offset = round(self.offset - pygame.Vector2(surface.get_size()) / 2)

        for sprite in self.sprites():
            sprite.draw(surface, offset, dt)

    def set_target(self, target: Sprite) -> None:
        self.target = target
        self.offset = pygame.Vector2(self.target.pos)
