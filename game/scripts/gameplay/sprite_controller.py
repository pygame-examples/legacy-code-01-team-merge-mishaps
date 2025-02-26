"""
These actually control sprites!

You can make ones that control with keyboard input (player) or AI (replays, enemies, etc)
"""


import asyncio
import pygame
from queue import Queue
from typing import Iterator

from ..interfaces import SpriteControllerInterface, SpriteCommand
from ..const import INPUT_FPS

class InputController(SpriteControllerInterface):
    """Uses WASD or Arrow Keys to move a sprite"""
    KEYBINDS: dict[str, list[int]] = {
        "jump": [pygame.K_UP, pygame.K_w],
        "left": [pygame.K_LEFT, pygame.K_a],
        "duck": [pygame.K_DOWN, pygame.K_s],
        "right": [pygame.K_RIGHT, pygame.K_d],
        "pick_up_or_throw": [pygame.K_z]
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


class GoLeftController(SpriteControllerInterface):
    """Goes Left always"""

    def get_commands(self) -> Iterator[SpriteCommand]:
        # uses multiple and back a little bc that's needed for portals for some reason
        # <shrug>
        yield SpriteCommand("left", pygame.time.get_ticks() - 2)
        yield SpriteCommand("left", pygame.time.get_ticks() - 2)

    async def run(self):
        # doesn't need any logic
        return 0
