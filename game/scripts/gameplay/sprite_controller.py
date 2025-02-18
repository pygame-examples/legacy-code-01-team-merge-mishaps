import asyncio
import pygame
from queue import Queue
from typing import Iterator

from ..interfaces import SpriteControllerInterface, SpriteCommand
from ..const import INPUT_FPS

class InputController(SpriteControllerInterface):
    KEYBINDS: dict[str, list[int]] = {
        "jump": (pygame.K_UP, pygame.K_w),
        "left": (pygame.K_LEFT, pygame.K_a),
        "duck": (pygame.K_DOWN, pygame.K_s),
        "right": (pygame.K_RIGHT, pygame.K_d)
    }

    def __init__(self):
        self.command_queue: Queue[tuple[str, int]] = Queue()
        self.live = True

    def get_commands(self) -> Iterator[SpriteCommand]:
        while not self.command_queue.empty():
            yield self.command_queue.get()

    async def run(self):
        while self.live:
            keys = pygame.key.get_pressed()
            for command, buttons in self.KEYBINDS.items():
                for button in buttons:
                    if keys[button]:
                        self.command_queue.put(SpriteCommand(command, pygame.time.get_ticks()))
            await asyncio.sleep(1 / INPUT_FPS)