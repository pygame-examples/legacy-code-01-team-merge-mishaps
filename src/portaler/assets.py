from pathlib import Path

from pytmx import load_project

ASSETS_DIRECTORY = Path(__file__).parent / "assets"
SPRITES_DIRECTORY = ASSETS_DIRECTORY / "sprites"
SFX_DIRECTORY = ASSETS_DIRECTORY / "sfx"
LEVELS_PATH = ASSETS_DIRECTORY / "levels.tiled-project"
LEVELS = load_project(LEVELS_PATH)
