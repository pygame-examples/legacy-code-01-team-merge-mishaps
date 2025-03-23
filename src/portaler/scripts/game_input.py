from __future__ import annotations

from asyncio import Lock

import pygame
from pygame.typing import SequenceLike

from .const import DEFAULT_KEYBINDINGS, Actions


class InputState:
    def __init__(self, bound_keys: dict[Actions, list[int]]):
        self.lock = Lock()
        self.bound_keys = bound_keys

        # dict[key type, how many times the key was pressed]
        self.pressed: dict[Actions, int] = {}
        self.pressed_view: dict[Actions, int] = {}  # Accessed by physics step.

        self.just_pressed: dict[Actions, int] = {}
        self.just_pressed_view: dict[Actions, int] = {}

    def get(self, action: Actions):
        return self.pressed_view.get(action, 0)

    def get_just(self, action: Actions):
        return self.just_pressed_view.get(action, 0)

    async def __aenter__(self):
        async with self.lock:
            self.pressed_view.update(self.pressed)
            self.pressed.clear()
            self.just_pressed_view.update(self.just_pressed)
            self.just_pressed.clear()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.pressed_view.clear()
        self.just_pressed_view.clear()

    def _update(self, inp: SequenceLike[bool], dct: dict[Actions, int]):
        for action in self.bound_keys:
            if action not in dct:
                dct[action] = 0
            for key in self.bound_keys[action]:
                if inp[key]:
                    dct[action] += 1

    async def update_just_pressed(self, inp: SequenceLike[bool]):
        async with self.lock:
            self._update(inp, self.just_pressed)

    async def update(self):
        async with self.lock:
            self._update(pygame.key.get_pressed(), self.pressed)
            self._update(pygame.key.get_just_pressed(), self.just_pressed)


input_state = InputState(DEFAULT_KEYBINDINGS)
