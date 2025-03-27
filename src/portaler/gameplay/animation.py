import pygame

from .sprites_and_sounds import get_image


class ANIMATIONMYWAY:
    def __init__(
        self,
        spritesheet_path: str,
        fps: int,
        single_frame_rect: pygame.typing.RectLike = (0, 0, -1, -1),
        frame_count: int = -1,
        loop_type="wrap",
        scale_factor: int = 1,
        rotation: int = 0,
    ):
        """
        YEAAH, FINALLY SOMETHING I UNDERSTAND IN THIS WHOLE CODEBASE
        seriously though, just a primitive animation class
        """
        self.frames = self._get_animation(
            spritesheet_path, single_frame_rect, frame_count, scale_factor, rotation
        )
        self.time_since_last_framce_change = 0
        self.current_time = 0
        self.fps = fps
        self.spf = 1 / self.fps
        self.current_frame_idx = 0
        self.loop_type = loop_type

    def _get_animation(
        self,
        spritesheet_path: str,
        frame_rect: pygame.typing.RectLike,
        frame_count: int,
        scale_factor: int,
        rotation: int,
    ):
        spritesheet = get_image(spritesheet_path)
        frame_rect = pygame.Rect(frame_rect)

        if frame_count == -1 and frame_rect == pygame.Rect(0, 0, -1, -1):
            raise Exception(
                "invalid animation information! specify either a single frame rect or a number of frames!"
            )

        if frame_count == -1:  # if no frame count was given, iterate through the whole spritesheet
            frame_count = spritesheet.height // frame_rect.height
        elif frame_rect == pygame.Rect(
            0,
            0,
            -1,
            -1,
        ):  # if no rect was given, calculate it using the number of frames
            frame_rect = pygame.Rect(0, 0, spritesheet.width, spritesheet.height // frame_count)

        frames = []

        for i in range(frame_count):
            frame = spritesheet.subsurface(
                (
                    frame_rect.x,
                    frame_rect.height * i,
                    frame_rect.width,
                    frame_rect.height,
                )
            )
            frame = pygame.transform.scale_by(frame, scale_factor)
            frame = pygame.transform.rotate(frame, rotation)
            frames.append(frame)

        return frames

    def update(self, dt):
        self.current_time += dt
        while self.current_time - self.time_since_last_framce_change > self.spf:
            self.time_since_last_framce_change += self.spf
            self.current_frame_idx += 1

        if self.loop_type == "wrap":
            self.current_frame_idx = self.current_frame_idx % len(self.frames)

    def get_frame(self):  # not used (yet)
        return self.frames[self.current_frame_idx]
