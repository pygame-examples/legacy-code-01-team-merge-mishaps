"""
This file contains the main game loop.

I tried to keep it as simple as possible.
"""
import asyncio
from collections import deque
from typing import Awaitable

import pygame

from scripts import env, const
from scripts.interfaces import GameInterface, GameStateInterface

from scripts.gameplay import level, menu


class Game(GameInterface):
    def __init__(self):
        super().__init__()
        self.running: bool = False
        self.window: pygame.Window = None
        # rightmost = top of stack
        self.state_stack: deque[GameStateInterface] = deque()
        self.render_delay: int = env.CAN_CAP_FPS * 1 / const.RENDER_FPS
        self.physics_delay: int = 1 / const.PHYSICS_FPS
        self.last_physics_update: int = 0
        self.tg: asyncio.TaskGroup = None
        self.needs_canceled: list[asyncio.Task] = []

    def quit(self) -> None:
        """Close the game window and exit"""
        self.running = False
        for task in self.needs_canceled:
            task.cancel()

    def add_task(self, task: Awaitable) -> None:
        self.needs_canceled.append(self.tg.create_task(task))

    def update_physics(self) -> None:
        self.state_stack[-1].update_physics(self.physics_delay)
        self.last_physics_update = pygame.time.get_ticks()

    async def input_loop(self) -> None:
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
            await asyncio.sleep(1 / const.INPUT_FPS)

    async def physics_loop(self) -> None:
        while self.running:
            self.update_physics()
            await asyncio.sleep(self.physics_delay)

    async def render_loop(self):
        while self.running:
            surface = self.state_stack[-1].render((pygame.time.get_ticks() - self.last_physics_update) / 1000)
            self.window.get_surface().blit(surface, (0, 0))
            self.window.flip()
            await asyncio.sleep(self.render_delay)

    async def run(self) -> None:
        self.running = True
        self.window: pygame.Window = pygame.window.Window(
            const.TITLE,
            const.WINDOW_RESOLUTION,
            resizable=True,
            maximized=True,
        )
        self.window.get_surface()

        self.state_stack.append(level.Level(self))


        async with asyncio.TaskGroup() as self.tg:
            self.state_stack[-1].init()
            self.update_physics()  # to ensure this happens before 1st render
            self.tg.create_task(self.input_loop())
            self.tg.create_task(self.physics_loop())
            self.tg.create_task(self.render_loop())



if __name__ == "__main__":
    pygame.init()
    game = Game()
    asyncio.run(game.run())