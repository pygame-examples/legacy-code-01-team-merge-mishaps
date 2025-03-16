"""
This file aims to reduce the ammount of duplicate image loading by loading everything into the same dict
and then using it again instead of loading a new image every time we create a new instance of an object.
The same thing goes for the SFX

Just a place to store all of them.
"""
import pygame
from ..assets import SPRITES_DIRECTORY, SFX_DIRECTORY

spritesheets = {}
sfx = {}

def get_image(path: str) -> pygame.Surface:
    if path not in spritesheets:
        spritesheets[path] = pygame.image.load(SPRITES_DIRECTORY / path).convert_alpha()

    return spritesheets[path]


def clear_spritesheets() -> None:  # when chaning a level, idk
    global spritesheets
    spritesheets = {}


def get_sfx(path: str) -> pygame.mixer.Sound:
    if path not in sfx:
        sfx[path] = pygame.mixer.Sound(SFX_DIRECTORY / path)
    
    return sfx[path]

