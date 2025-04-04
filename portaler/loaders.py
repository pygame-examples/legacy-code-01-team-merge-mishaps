import json

import pygame

from .assets import LEVEL_DIRECTORY, SPRITES_DIRECTORY
from .const import TILE_SIZE
from .gameplay import level
from .interfaces import Axis, Direction, PhysicsSpriteInterface, PortalColor, ThrowableType

with open(LEVEL_DIRECTORY / "tile_symbols.json") as f:
    tile_symbols = json.load(f)

tile_spritesheet: dict[str, pygame.Surface] = {}


def tile_variant_name(kind: str, neighbors: int) -> str:
    return f"{kind}#{bin(neighbors)[2:].zfill(4)}"


def load_tile_spritesheet() -> None:
    # bitmask: LEFT, TOP, RIGHT, BOTTOM
    variants = {
        (0, 0): 0b0011,
        (1, 0): 0b1011,
        (2, 0): 0b1001,
        (3, 0): 0b0001,
        (0, 1): 0b0111,
        (1, 1): 0b1111,
        (2, 1): 0b1101,
        (3, 1): 0b0101,
        (0, 2): 0b0110,
        (1, 2): 0b1110,
        (2, 2): 0b1100,
        (3, 2): 0b0100,
        (0, 3): 0b0010,
        (1, 3): 0b1010,
        (2, 3): 0b1000,
        (3, 3): 0b0000,
    }
    walls = pygame.image.load(SPRITES_DIRECTORY / "walls.png").convert_alpha()
    tile_size = 16
    for kind, kind_pos in {"wall1": (0, 0), "wall2": (1, 0), "wall3": (0, 1)}.items():
        for variant_pos, neighbors in variants.items():
            x = kind_pos[0] * 4 + variant_pos[0]
            y = kind_pos[1] * 4 + variant_pos[1]
            tile_spritesheet[tile_variant_name(kind, neighbors)] = pygame.transform.scale(
                walls.subsurface((x * tile_size, y * tile_size, tile_size, tile_size)), (TILE_SIZE, TILE_SIZE)
            )


load_tile_spritesheet()


class LevelLoader:
    def __init__(self, name: str):
        self.name = name
        with open(LEVEL_DIRECTORY / "levels" / (name + ".json")) as f:
            self.data = json.load(f)
        with open(LEVEL_DIRECTORY / "levels" / (name + ".txt")) as f:
            # json doesn't allow multiline strings, use txt instead
            self.data["raw_tilemap"] = f.read().strip()
        self.data["tilemap"] = [line.strip() for line in self.data["raw_tilemap"].split("\n")]

    def load(self, target: level.Level) -> None:
        # NOTE: order matters, for rendering
        self.load_config(target)
        self.load_sprites(target)
        self.load_tiles(target)

    def load_tiles(self, target: level.Level) -> None:
        data = self.data["tilemap"]
        symbol_tilemap: dict[tuple[int, int], str] = {}
        neighbors_map: dict[tuple[int, int], int] = {}
        offset_x, offset_y = self.data.get("tilemap_offset", [0, 0])
        for y, row in enumerate(data):
            for x, symbol in enumerate(row):
                symbol_tilemap[x + offset_x, y + offset_y] = symbol
        for pos, symbol in symbol_tilemap.items():
            # Auto-tiling
            neighbors: int = 0
            if symbol_tilemap.get((pos[0] - 1, pos[1])) == symbol:
                neighbors |= 0b1000
            if symbol_tilemap.get((pos[0], pos[1] - 1)) == symbol:
                neighbors |= 0b0100
            if symbol_tilemap.get((pos[0] + 1, pos[1])) == symbol:
                neighbors |= 0b0010
            if symbol_tilemap.get((pos[0], pos[1] + 1)) == symbol:
                neighbors |= 0b0001
            neighbors_map[pos] = neighbors
        for pos, symbol in symbol_tilemap.items():
            self.add_tile(target, symbol, pos, neighbors_map[pos])

    def add_tile(self, target: level.Level, symbol: str, pos: tuple[int, int], neighbors: int) -> None:
        try:
            tile = tile_symbols[symbol]
        except KeyError:
            print(f"Unknown tile symbol: {symbol}")
            return
        if tile is None:
            # empty tile
            return
        surface = tile_spritesheet[tile_variant_name(tile, neighbors)]
        target.spawn_wall(pos, (1, 1), surface)

    def load_sprites(self, target: level.Level) -> None:  # noqa: C901  (shush)
        data = self.data["sprites"]
        trigger_lookup: dict[str, PhysicsSpriteInterface] = {}
        # NOTE: The order in which these are loaded affects the order in which they are drawn
        if "one_way_blocks" in data:
            for i, block in enumerate(data["one_way_blocks"]):
                pos = block["pos"]
                width = block["width"]
                target.spawn_one_way_block(pos, width)
        if "player" in data:
            player_data = data["player"]
            target.spawn_player(player_data["pos"])
        if "throwables" in data:
            for i, throwable in enumerate(data["throwables"]):
                pos = throwable["pos"]
                throwable_type = ThrowableType[throwable["type"]]
                target.spawn_throwable(pos, throwable_type)
        if "portals" in data:
            for color, pair in data["portals"].items():
                portal_color = PortalColor[color]
                portal_a, portal_b = pair
                target.spawn_portal_pair(
                    portal_a["pos"],
                    Direction[portal_a["orientation"]],
                    portal_b["pos"],
                    Direction[portal_b["orientation"]],
                    portal_color,
                )
        if "finishes" in data:
            for i, finish in enumerate(data["finishes"]):
                pos = finish["pos"]
                trigger_lookup[f"finishes[{i}]"] = target.spawn_finish(pos)
        if "doors" in data:
            for i, door in enumerate(data["doors"]):
                pos = door["pos"]
                length = door["length"]
                axis = Axis[door["orientation"]]  # TODO: implement actual directions, not just axes, for door
                orientation = Direction.NORTH if axis == Axis.VERTICAL else Direction.WEST
                trigger_lookup[f"doors[{i}]"] = target.spawn_door(
                    pos, length, orientation, draw_head=door.get("draw_head", True)
                )
        if "lifters" in data:
            for i, lifter in enumerate(data["lifters"]):
                pos = lifter["pos"]
                height = lifter["height"]
                segment_count = lifter["segment_count"]
                starting_state = lifter["starting_state"]
                trigger_lookup[f"lifters[{i}]"] = target.spawn_lifter(
                    pos, height, segment_count, starting_state
                )
        if "buttons" in data:
            for i, button in enumerate(data["buttons"]):
                pos = button["pos"]
                linked_to_array = button["linked_to"]
                # NOTE: requires trigger_lookup to be complete (except later buttons)
                linked_to = [trigger_lookup[trigger] for trigger in linked_to_array]
                trigger_lookup[f"buttons[{i}]"] = target.spawn_button(pos, linked_to)
        # TODO: explode when unknown key

    def load_config(self, target: level.Level) -> None:
        data = self.data
        camera_view_tile_range = data.get("camera_view_tile_range", "fit")
        if camera_view_tile_range == "fit":
            tilemap = data["tilemap"]
            height = len(tilemap)
            width = max([len(row) for row in tilemap])
            x = y = 0
        else:
            x, y, width, height = camera_view_tile_range
        camera_view_range = pygame.FRect(x * TILE_SIZE, y * TILE_SIZE, width * TILE_SIZE, height * TILE_SIZE)
        target.camera.view_range = camera_view_range
        camera_scale = data.get("camera_scale", 1.0)
        target.camera.scale = camera_scale
