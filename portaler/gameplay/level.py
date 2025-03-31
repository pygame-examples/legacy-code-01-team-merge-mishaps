from typing import Coroutine

import pygame
from pygame import FRect

from ..const import TILE_SIZE, Actions
from ..game_input import input_state
from ..interfaces import (
    Axis,
    Direction,
    GameInterface,
    GameLevelInterface,
    PortalColor,
    SpriteInitData,
    ThrowableType,
)
from .block import Block, OneWayBlock, ThrowableBlock
from .button import Button, FinishButton
from .camera import Camera
from .door import Door
from .player import Player
from .portal import Portal


class Level(GameLevelInterface):
    """
    Game state for gameplay

    This thing probably needs a camera(implemented[kinda]) as well as some map loading code.
    I didn't want to decide nor spend the time on a map loading stack this early.
    """

    def __init__(self, game: GameInterface):
        self.groups: dict[str, pygame.sprite.AbstractGroup] = {
            "render": Camera(),
            "physics": pygame.sprite.Group(),
            "static-physics": pygame.sprite.Group(),
            "dynamic-physics": pygame.sprite.Group(),
            "trigger-physics": pygame.sprite.Group(),
            "portal-physics": pygame.sprite.Group(),
            "actors": pygame.sprite.Group(),
        }
        self.game: GameInterface = game

        # 0 for test map
        self.level_count = 1

        # Currently the only thing overwritten by the level loader
        self.camera.view_range = pygame.FRect(0, 0, 1088, 320)

    def init(self):
        """
        Spawn all sprites. Also, anything that needs to wait a frame or so before happening.

        I would put map loading here.
        """

        from .. import loaders  # TODO: fix ridiculous circular dependency

        if self.level_count > 6:
            self.level_count = 1  # TODO: win screen

        loaders.LevelLoader(str(self.level_count)).load(self)

    def restart(self):
        """
        Restart level.
        """
        self.empty_all()
        self.init()

    def add_task(self, task: Coroutine) -> None:
        """Adds task to main game loop"""
        self.game.add_task(task)

    def spawn_player(self, pos):
        player = self.spawn(
            Player,
            SpriteInitData(
                rect=pygame.FRect(pos[0] * TILE_SIZE, pos[1] * TILE_SIZE, TILE_SIZE, TILE_SIZE),
                level=self,
            ),
            True,
        )
        return player

    def spawn_portal_pair(
        self,
        pos1,
        orientation1: Direction,
        pos2,
        orientation2: Direction,
        portal_color: PortalColor,
    ):
        portal_w = 3 * TILE_SIZE
        portal_h = TILE_SIZE

        rect1 = FRect(
            (pos1[0] * TILE_SIZE, pos1[1] * TILE_SIZE, portal_w, portal_h)
            if orientation1 in [Direction.NORTH, Direction.SOUTH]
            else (pos1[0] * TILE_SIZE, pos1[1] * TILE_SIZE, portal_h, portal_w)
        )
        portal1 = self.spawn(
            Portal,
            SpriteInitData(
                rect=rect1,
                level=self,
                properties={
                    "orientation": orientation1,
                    "tunnel_id": str(portal_color.value),
                    # it's important to keep this as a string, because...
                    # uhh.. idk, something about Rob's wrath or whatever
                },
            ),
        )

        rect2 = FRect(
            (pos2[0] * TILE_SIZE, pos2[1] * TILE_SIZE, portal_w, portal_h)
            if orientation2 in [Direction.NORTH, Direction.SOUTH]
            else (pos2[0] * TILE_SIZE, pos2[1] * TILE_SIZE, portal_h, portal_w)
        )
        portal2 = self.spawn(
            Portal,
            SpriteInitData(
                rect=rect2,
                level=self,
                properties={
                    "orientation": orientation2,
                    "tunnel_id": str(portal_color.value),
                },
            ),
        )

        return portal1, portal2

    def spawn_button(self, pos, linked_to):
        button = self.spawn(
            Button,
            SpriteInitData(
                rect=FRect(
                    pos[0] * TILE_SIZE,
                    pos[1] * TILE_SIZE,
                    2 * TILE_SIZE,
                    TILE_SIZE,
                ),  # the button will always stay on the ground looking up unless someone wants to change that
                level=self,
                properties={"linked-to": linked_to},
            ),
        )

        return button

    def spawn_wall(self, pos, size, surface: pygame.Surface):
        wall = self.spawn(
            Block,
            SpriteInitData(
                rect=FRect(
                    pos[0] * TILE_SIZE,
                    pos[1] * TILE_SIZE,
                    size[0] * TILE_SIZE,
                    size[1] * TILE_SIZE,
                ),
                level=self,
                properties={"surface": surface},
            ),
        )
        return wall

    def spawn_throwable(self, pos, throwable_type: ThrowableType):
        throwable = self.spawn(
            ThrowableBlock,
            SpriteInitData(
                rect=FRect(pos[0] * TILE_SIZE, pos[1] * TILE_SIZE, TILE_SIZE, TILE_SIZE),
                level=self,
                properties={"id": throwable_type.value},
            ),
        )

        return throwable

    def spawn_one_way_block(self, pos, width: int):
        block = self.spawn(
            OneWayBlock,
            SpriteInitData(
                rect=FRect(
                    pos[0] * TILE_SIZE,
                    pos[1] * TILE_SIZE,
                    width * TILE_SIZE,
                    0.0001 * TILE_SIZE,  # Height/depth/thickness of platform (thinner than one tile)
                ),  # can be arbitrarily thin because we have platform anti-tunneling
                level=self,
            ),
        )
        return block

    def spawn_door(self, pos, length: int, orientation: Axis, *, draw_head: bool = True):
        rect = FRect(
            (pos[0] * TILE_SIZE, pos[1] * TILE_SIZE, 2 * TILE_SIZE, length * TILE_SIZE)
            if orientation is not Axis.HORIZONTAL
            else (
                pos[0] * TILE_SIZE,
                pos[1] * TILE_SIZE,
                length * TILE_SIZE,
                2 * TILE_SIZE,
            )
        )
        door = self.spawn(
            Door,
            SpriteInitData(rect=rect, level=self, properties={"orientation": orientation}),
        )
        door.draw_head = draw_head
        return door

    def spawn_finish(self, pos):
        return self.spawn(
            FinishButton,
            SpriteInitData(
                rect=FRect(pos[0] * TILE_SIZE, pos[1] * TILE_SIZE, TILE_SIZE, TILE_SIZE), level=self
            ),
        )

    def handle_input(self, dt: float) -> None:
        if input_state.get_just(Actions.RESTART):
            self.restart()
