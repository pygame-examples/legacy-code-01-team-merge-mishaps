from __future__ import annotations

from asyncio import Lock

import pygame
from pygame.typing import SequenceLike

from .const import DEFAULT_KEYBINDINGS, Actions


class InputState:
    def __init__(self, bound_keys: dict[Actions, list[int]]):
        self.lock = Lock()
        self.bound_keys = bound_keys

        actions_map = dict.fromkeys(Actions, False)
        # dict[key type, how many times the key was pressed]
        self.pressed: dict[Actions, bool] = dict(actions_map)
        self.pressed_view: dict[Actions, bool] = dict(actions_map)  # Accessed by physics step.

        self.just_pressed: dict[Actions, bool] = dict(actions_map)
        self.just_pressed_view: dict[Actions, bool] = dict(actions_map)
        self.updated: bool = False

    def get(self, action: Actions) -> bool:
        return self.pressed_view.get(action, False)

    def get_just(self, action: Actions) -> bool:
        return self.just_pressed_view.get(action, False)

    async def __aenter__(self):
        async with self.lock:
            self.pressed_view.update(self.pressed)
            self.just_pressed_view.update(self.just_pressed)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.clear()
        self.updated = False

    def _update(self, inp: SequenceLike[bool], dct: dict[Actions, int]):
        for action in self.bound_keys:
            if not dct[action]:
                dct[action] = any(inp[key] for key in self.bound_keys[action])

    async def update_just_pressed(self, inp: SequenceLike[bool]):
        async with self.lock:
            self._update(inp, self.just_pressed)

    async def update(self):
        async with self.lock:
            self.updated = True
            self._update(pygame.key.get_pressed(), self.pressed)
            self._update(pygame.key.get_just_pressed(), self.just_pressed)

    def clear(self):
        self.pressed.update(dict.fromkeys(Actions, False))
        self.just_pressed.update(dict.fromkeys(Actions, False))


input_state = InputState(DEFAULT_KEYBINDINGS)
