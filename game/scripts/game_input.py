from asyncio import Lock

import pygame

from .const import Actions, DEFAULT_KEYBINDINGS


class InputState:
    def __init__(self, bound_keys: dict[Actions, list[int]]):
        self.lock = Lock()
        self.bound_keys = bound_keys

        # dict[key type, how many times the key was pressed]
        self.pressed: dict[Actions, int] = {}
        self.pressed_view: dict[Actions, int] = {}  # Accessed by physics step.

    def get(self, action: Actions):
        return self.pressed_view.get(action, 0)

    async def __aenter__(self):
        async with self.lock:
            self.pressed_view.update(self.pressed)
            self.pressed.clear()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.pressed_view.clear()

    async def update(self):
        async with self.lock:
            pressed = pygame.key.get_pressed()
            for action in self.bound_keys:
                if action not in self.pressed:
                    self.pressed[action] = 0
                for key in self.bound_keys[action]:
                    if pressed[key]:
                        self.pressed[action] += 1


input_state = InputState(DEFAULT_KEYBINDINGS)
