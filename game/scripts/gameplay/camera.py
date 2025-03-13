from __future__ import annotations

import pygame

from .sprite import Sprite


class Camera(pygame.sprite.LayeredUpdates):
    """
    Camera group, meant for following a specific sprite while rendering

    TODO:
        add a screen shake for when objects collide >:]   - ??
    """
    def __init__(self) -> None:
        super().__init__()
        self.target: Sprite | None = None
        self.offset = pygame.Vector2(0, 0)
        self.view_range: pygame.FRect | None = None

    def draw(self, surface: pygame.Surface, dt: float = 1) -> None:
        cam = surface.get_frect(center=self.offset)
        if self.target is not None:
            pos = self.target.interpolated_pos(dt) - self.offset
            view_frect = surface.get_frect(center=(0,0))
            view_frect.scale_by_ip(0.25)
            self.offset.x += min(pos.x - view_frect.left, 0) + max(pos.x - view_frect.right, 0)
            self.offset.y += min(pos.y - view_frect.top, 0) + max(pos.y - view_frect.bottom, 0)

        # Limit the camera within the boundary of the view_range
        if self.view_range is not None:
            if cam.left < self.view_range.left:cam.left = self.view_range.left
            if cam.right > self.view_range.right: cam.right = self.view_range.right
            if cam.top < self.view_range.top: cam.top = self.view_range.top
            if cam.bottom > self.view_range.bottom: cam.bottom = self.view_range.bottom

            if cam.width > self.view_range.width:
                cam.centerx = self.view_range.centerx

            if cam.height > self.view_range.height:
                cam.centery = self.view_range.centery

        # Offset the camera to the center of the screen and round it, because there are sprites with fractional position
        # and due to rounding errors, they would appear jittery
        offset = round(pygame.Vector2(cam.topleft))
        # This doesn't seem to be the case for now, but if that's the case, use the code above.
        # offset = pygame.Vector2(cam.topleft)  # maybe for now use the fixing one

        for sprite in self.sprites():
            sprite.draw(surface, offset, dt)

    def set_target(self, target: Sprite) -> None:
        self.target = target
        self.offset = pygame.Vector2(self.target.pos)
