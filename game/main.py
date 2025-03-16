"""
Run this file to run the game, in the same directory as this file

I tried to keep it as simple as possible.
"""
import asyncio
from collections import deque
from typing import Awaitable

import pygame

from .scripts import env, const, game_input
from .scripts.interfaces import GameInterface, GameStateInterface

from .scripts.gameplay import level, menu


class Game(GameInterface):
    window: pygame.Window  # game window
    tg: asyncio.TaskGroup  # task group for all game loops

    """Main Game.  Gets passed to Game states"""
    def __init__(self):
        super().__init__()
        self.running: bool = False  # whether the game is running the main loop
        # rightmost = top of stack
        self.state_stack: deque[GameStateInterface] = deque()  # index -1 is top of stack
        self.render_delay: float = env.CAN_CAP_FPS * 1 / const.RENDER_FPS
        self.target_render_delay: float = self.render_delay
        self.physics_delay: float = 1 / const.PHYSICS_FPS
        self.last_physics_update: int = 0  # time (in milliseconds of the last physics update)
        self.input_delay = 1 / const.INPUT_FPS
        self.needs_canceled: list[asyncio.Task] = []  # list of tasks that need canceled when the game is closed

        pygame.mixer.set_num_channels(16)
        for reserved in const.RESERVED_CHANNELS:
            pygame.mixer.set_reserved(reserved)

    def quit(self) -> None:
        """Close the game window and exit"""
        self.running = False
        for task in self.needs_canceled:
            task.cancel()

    def add_task(self, task: Awaitable) -> None:
        """Add async task to the main loop"""
        self.needs_canceled.append(self.tg.create_task(task))

    async def input_loop(self) -> None:
        """Loop that handles window-related input"""
        while self.running:
            start = pygame.time.get_ticks()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
            await game_input.input_state.update()
            end = pygame.time.get_ticks()
            await asyncio.sleep(max(self.input_delay - (end - start), 0))

    async def update_physics(self, half_steps: int = 1) -> None:
        """Update game physics. Called interally."""
        semi_step = self.physics_delay / half_steps
        async with game_input.input_state:  # Hold lock for input to avoid interference with input_loop
            for _ in range(half_steps):
                await self.state_stack[-1].update_actors(self.physics_delay)
                await self.state_stack[-1].update_physics(semi_step)
        self.last_physics_update = pygame.time.get_ticks()

    async def physics_loop(self) -> None:
        """Loop that runs physics"""
        while self.running:
            start = pygame.time.get_ticks()
            await self.update_physics(1)
            end = pygame.time.get_ticks()
            await asyncio.sleep(max(self.physics_delay - (end - start), 0))

    async def render_loop(self):
        """Loop that renders the game"""
        while self.running:
            start = pygame.time.get_ticks()
            dt_since_physics = (start - self.last_physics_update) / 1000
            surface = await self.state_stack[-1].render(const.WINDOW_RESOLUTION, dt_since_physics)
            disp = self.window.get_surface()
            output = const.fit_surface(surface, self.window.size)
            disp.blit(output, output.get_rect(center=disp.get_rect().center))
            self.window.flip()
            if dt_since_physics > self.physics_delay * 2:
                self.render_delay = min(self.render_delay + 0.05, 1 / 15)
            elif self.render_delay > self.target_render_delay:
                self.render_delay = max(self.target_render_delay, self.render_delay - 0.05)
            end = pygame.time.get_ticks()
            await asyncio.sleep(max(self.render_delay - (end - start), 0))

    async def run(self) -> None:
        """Initializes Game Window and runs all loops"""
        self.running = True
        self.window: pygame.Window = pygame.window.Window(
            const.TITLE,
            const.WINDOW_RESOLUTION,
            resizable=True,
            # maximized=True,
        )
        self.window.get_surface()

        self.state_stack.append(level.Level(self))

        async with asyncio.TaskGroup() as self.tg:
            self.state_stack[-1].init()
            await self.update_physics()  # to ensure this happens before 1st render
            self.tg.create_task(self.input_loop())
            self.tg.create_task(self.physics_loop())
            self.tg.create_task(self.render_loop())


def main():
    pygame.init()
    game = Game()
    asyncio.run(game.run())
