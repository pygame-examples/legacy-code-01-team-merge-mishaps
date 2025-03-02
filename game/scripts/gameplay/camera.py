import pygame

from .sprite import Sprite


class Camera(pygame.sprite.LayeredUpdates):
    """
    Camera group, meant for following a specific sprite while rendering

    TODO: 
        1) fix the jitteryness of the camera
        2) add a screen shake for when objects collide >:]
    """
    def __init__(self) -> None:
        super().__init__()
        self.target: Sprite = None
        self.offset = pygame.Vector2(0, 0)
        self.follow_coefficient = 1/50

    def draw(self, surface: pygame.Surface, dt: float) -> None:
        if self.target:
            pos = self.target.interpolated_pos(dt)
            self.offset += pygame.Vector2(
                    int((pos[0] - self.offset.x - surface.width//2)) * self.follow_coefficient, # sorry couldn't figure out why the smooth transition is so jittery ;-;
                    int((pos[1] - self.offset.y - surface.height//2)) * self.follow_coefficient
            )

        for sprite in self.sprites():
            sprite.draw(surface, self.offset, dt)

    def set_target(self, target: Sprite) -> None:
        self.target = target
