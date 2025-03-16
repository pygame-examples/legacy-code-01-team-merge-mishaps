# not to be confused with const.py
# this is basically a const.py file, but with pygame.init already called
import pygame

spritesheets = {}
sfx = {}

def get_image(path: str) -> pygame.Surface:
    if path not in spritesheets:
        spritesheets[path] = pygame.image.load(path).convert_alpha()

    return spritesheets[path]


def clear_spritesheets() -> None:  # when chaning a level, idk
    global spritesheets
    spritesheets = {}


def get_sfx(path: str) -> pygame.mixer.Sound:
    if path not in sfx:
        sfx[path] = pygame.mixer.Sound(path)
    
    return sfx[path]

