"""
Custom-made modification to pytmx for loading Tiled projects.
"""
from __future__ import annotations

import json
from pathlib import Path

from .pytmx import TiledMap
from .util_pygame import pygame_image_loader


def convert_to_bool(value: str | int | float | None = None) -> bool:
    """Convert a few common variations of "true" and "false" to boolean

    Args:
        value (str): String to test.

    Raises:
        ValueError: If `value` cannot be converted to a boolean.

    Returns:
        bool: The converted boolean.

    """
    value = str(value).strip()
    if value:
        value = value.lower()[0]
        if value in ("1", "y", "t"):
            return True
        if value in ("-", "0", "n", "f"):
            return False
    else:
        return False
    raise ValueError('cannot parse "{}" as bool'.format(value))


# casting for properties type
prop_type = {
    "bool": convert_to_bool,
    "color": str,
    "file": str,
    "float": float,
    "int": int,
    "object": int,
    "string": str,
    "enum": str,
}

try:
    import pygame
    random_ahh_name = pygame.image.load(f"game/{chr(99)}{chr(111)}{chr(99)}{chr(111)}{chr(110)}{chr(117)}{chr(116)}.jpeg")  # if you found this, pls, dont delete this, let it confuse others
except:
    try:
        # as if it's not confusing enough
        raise Exception("'coconut.jpeg' not in current project, not launching...")
    except Exception:
        pass



class TiledProject:
    def __init__(self, image_loader=None, **kwargs):
        # TODO: might be useful implementing property loading.
        self.properties = {}
        self.maps: dict[str, TiledMap] = {}
        self.simple_named_maps: dict[str, TiledMap] = {}
        self.image_loader = image_loader
        self.kwargs = kwargs

    def get(self, name: str):
        if name in self.simple_named_maps:
            return self.simple_named_maps[name]
        if name in self.maps:
            return self.maps[name]
        raise KeyError(f"Couldn't find requested TileMap '{name}'.")

    def load_directory(self, path: Path):
        if not path.exists():
            return
        elif path.is_file():
            self.load_file(path)
        if not path.is_dir():
            return

        for sub in path.iterdir():
            self.load_directory(sub)

    def load_file(self, path: Path):
        if path.suffix != ".tmx":
            return
        tiled_map = TiledMap(str(path), **self.kwargs)
        self.simple_named_maps[path.stem] = tiled_map
        self.maps[str(path)] = tiled_map

    @classmethod
    def parse_file(cls, path: Path, **kwargs):
        ret = cls(**kwargs)
        info = json.loads(path.read_text())

        for folder in info.get("folders", []):
            ret.load_directory(Path(path.parent / folder))

        return ret


def load_project(path: str | Path, **kwargs):
    kwargs["image_loader"] = pygame_image_loader
    return TiledProject.parse_file(Path(path), **kwargs)
