from typing import Awaitable

import pygame
from pygame.typing import RectLike

from ..const import TILE_SIZE
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
        self.groups["render"].view_range = pygame.FRect(0, 0, 1088, 320)

    def init(self):
        """
        Spawn all sprites. Also, anything that needs to wait a frame or so before happening.

        I would put map loading here.
        """

        # TODO: implement level loading. Remember the note above
        # TODO: i left some spritesheets for tiles in sprites folder

        from .. import loaders  # TODO: fix ridiculous circular dependency

        loaders.LevelLoader("1").load(self)
        return

        if self.level_count == 0:  # look how tidy it is in here, better not ruin it 😊
            self.spawn_player(pos=(3, 5))
            # ---------------------- walls/floors ----------------------
            self.spawn_wall((1, 8), (32, 1))
            self.spawn_wall((1, 1), (1, 8))
            self.spawn_wall((1, 1), (32, 1))

            # ---------------------- platforms ----------------------
            self.spawn_one_way_block((10, 5), 4)

            # ---------------------- blocks ----------------------
            self.spawn_throwable((8, 4), ThrowableType.GOLD)
            self.spawn_throwable((8, 3), ThrowableType.IRON)
            self.spawn_throwable((8, 2), ThrowableType.WOOD)

            # ---------------------- activateable ----------------------
            door1 = self.spawn_door((26, 2), 6, Axis.VERTICAL)

            # ---------------------- portals -----------------------
            self.spawn_portal_pair((8, 0), Direction.NORTH, (8, 2), Direction.SOUTH, PortalColor.YELLOW)
            self.spawn_portal_pair((2, 5), Direction.EAST, (32, 5), Direction.WEST, PortalColor.GREEN)
            self.spawn_portal_pair((14, 7), Direction.NORTH, (7, 7), Direction.NORTH, PortalColor.RED)
            self.spawn_portal_pair((19, 2), Direction.SOUTH, (19, 7), Direction.NORTH, PortalColor.CYAN)

            # ---------------------- triggerable ----------------------
            self.spawn_button((23, 7), [door1])

        # uhhh, yk, this should probably be done through a level editor, but...
        elif self.level_count == 1:
            # based on assets/ideas/idea1.png

            self.groups["render"].view_range = pygame.FRect(0, 0, 640, 320)

            self.spawn_player(pos=(3, 4))

            self.spawn_throwable((1, 2), ThrowableType.WOOD)
            self.spawn_wall((1, 3), (1, 1))

            self.spawn_wall((0, 6), (20, 1))
            self.spawn_wall((0, -1), (1, 7))
            self.spawn_wall((0, -1), (20, 1))
            self.spawn_wall((19, -1), (1, 7))

            self.spawn_wall((4, 6), (1, 5))
            self.spawn_wall((14, 6), (1, 5))
            self.spawn_wall((4, 11), (11, 1))

            self.spawn_portal_pair((7, 0), Direction.SOUTH, (5, 8), Direction.EAST, PortalColor.GREEN)

            door = self.spawn_door((13, 0), 6, Axis.VERTICAL)
            self.spawn_button((12, 10), [door])

            self.spawn_finish((18, 5))

        elif self.level_count == 2:
            # based on assets/ideas/idea4.png
            # slightly modified though

            self.groups["render"].view_range = pygame.FRect(0, 0, 1024 - 32 * 2, 672)

            self.spawn_player(pos=(1, 3))

            self.spawn_wall((0, 0), (30, 1))
            self.spawn_wall((0, 20), (30, 1))
            self.spawn_wall((0, 0), (1, 20))
            self.spawn_wall((29, 0), (1, 20))

            self.spawn_wall((1, 4), (1, 1))
            self.spawn_wall((2, 5), (1, 1))
            # self.spawn_wall((3, 6), (1, 1))
            # self.spawn_wall((4, 7), (1, 1))
            # self.spawn_wall((5, 8), (1, 1))
            # self.spawn_wall((6, 9), (1, 1))
            # self.spawn_wall((7, 10), (1, 1))
            # self.spawn_wall((8, 11), (1, 1))
            self.spawn_wall((9, 12), (1, 1))

            self.spawn_wall((13, 12), (1, 1))
            self.spawn_wall((13, 13), (1, 1))
            self.spawn_wall((13, 14), (1, 1))
            self.spawn_wall((13, 15), (1, 1))
            self.spawn_wall((13, 16), (1, 1))
            self.spawn_wall((14, 17), (1, 1))
            self.spawn_wall((15, 18), (1, 1))
            self.spawn_wall((16, 19), (1, 1))

            self.spawn_wall((17, 10), (3, 2))
            self.spawn_wall((20, 0), (1, 12))
            self.spawn_wall((16, 0), (1, 12))

            self.spawn_wall((26, 3), (3, 1))

            self.spawn_portal_pair((21, 19), Direction.NORTH, (17, 9), Direction.NORTH, PortalColor.GREEN)

            self.spawn_finish((28, 2))

        else:
            raise NotImplementedError(f"Level {self.level_count} not implemented")

    def set_camera_view(self, view: RectLike):
        self.groups["render"].view_range = pygame.FRect(view)

    def add_task(self, task: Awaitable) -> None:
        """Adds task to main game loop"""
        self.game.add_task(task)

    def spawn_player(self, pos):
        player = self.spawn(
            Player,
            SpriteInitData(
                rect=(pos[0] * TILE_SIZE, pos[1] * TILE_SIZE, TILE_SIZE, TILE_SIZE),
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

        rect1 = (
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

        rect2 = (
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
                rect=(
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
                rect=(
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
                rect=(pos[0] * TILE_SIZE, pos[1] * TILE_SIZE, TILE_SIZE, TILE_SIZE),
                level=self,
                properties={"id": throwable_type.value},
            ),
        )

        return throwable

    def spawn_one_way_block(self, pos, width: int):
        block = self.spawn(
            OneWayBlock,
            SpriteInitData(
                rect=(
                    pos[0] * TILE_SIZE,
                    pos[1] * TILE_SIZE,
                    width * TILE_SIZE,
                    TILE_SIZE,
                ),
                level=self,
            ),
        )
        return block

    def spawn_door(self, pos, length: int, orientation: Axis):
        rect = (
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

        return door

    def spawn_finish(self, pos):
        return self.spawn(
            FinishButton,
            SpriteInitData(rect=(pos[0] * TILE_SIZE, pos[1] * TILE_SIZE, TILE_SIZE, TILE_SIZE), level=self),
        )
