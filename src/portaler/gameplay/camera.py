from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from ..interfaces import SpriteInterface


class Camera(pygame.sprite.LayeredUpdates):
    """
    Camera group, meant for following a specific sprite while rendering
    """

    def __init__(self) -> None:
        super().__init__()
        self.target: SpriteInterface | None = None
        self.offset = pygame.Vector2(0, 0)
        self.view_range: pygame.FRect | None = None
        self.scale: float = 1.0  # value greater than 1.0 is zoomed in

    def draw(self, surface: pygame.Surface, dt_since_physics: float) -> None:
        scale = self.scale
        drawing_surface = (
            surface
            if scale == 1.0
            else pygame.Surface((round(surface.width / scale), round(surface.height / scale)))
        )
        cam = drawing_surface.get_frect(center=self.offset)
        if self.target is not None:
            pos = self.target.interpolated_pos(dt_since_physics) - self.offset
            view_frect = drawing_surface.get_frect(center=(0, 0))
            view_frect.scale_by_ip(0.25)
            self.offset.x += min(pos.x - view_frect.left, 0) + max(pos.x - view_frect.right, 0)
            self.offset.y += min(pos.y - view_frect.top, 0) + max(pos.y - view_frect.bottom, 0)

        # Limit the camera within the boundary of the view_range
        if self.view_range is not None:
            if cam.width > self.view_range.width:
                cam.centerx = self.view_range.centerx
            else:
                cam.left = max(cam.left, self.view_range.left)
                cam.right = min(cam.right, self.view_range.right)
            if cam.height > self.view_range.height:
                cam.centery = self.view_range.centery
            else:
                cam.top = max(cam.top, self.view_range.top)
                cam.bottom = min(cam.bottom, self.view_range.bottom)

        # Offset the camera to the center of the screen and round it,
        # because there are sprites with fractional position
        # and due to rounding errors, they would appear jittery
        offset = round(pygame.Vector2(cam.topleft))
        # This doesn't seem to be the case for now, but if that's the case, use the code above.
        # offset = pygame.Vector2(cam.topleft)  # maybe for now use the fixing one

        for sprite in self.sprites():
            sprite.draw(drawing_surface, offset, dt_since_physics)
        if scale != 1.0:
            pygame.transform.scale(drawing_surface, surface.size, surface)

    def set_target(self, target: SpriteInterface) -> None:
        self.target = target
        self.offset = pygame.Vector2(self.target.pos)
