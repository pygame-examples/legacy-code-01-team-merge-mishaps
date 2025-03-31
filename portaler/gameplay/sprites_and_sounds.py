"""
This file aims to reduce the ammount of duplicate image loading by loading everything into the same dict
and then using it again instead of loading a new image every time we create a new instance of an object.
The same thing goes for the SFX

Just a place to store all of them.
"""

import pygame

from ..assets import SOUND_DIRECTORY, SPRITES_DIRECTORY

spritesheets: dict[str, pygame.Surface] = {}

_sounds: dict[str, pygame.Sound] = {}

mute: bool = False
"""Boolean whether to play sounds. Change this attribute on the module to mute/unmute."""


def get_image(path: str) -> pygame.Surface:
    if path not in spritesheets:
        spritesheets[path] = pygame.image.load(SPRITES_DIRECTORY / path).convert_alpha()
    return spritesheets[path]


def clear_spritesheets() -> None:  # when chaning a level, idk
    global spritesheets
    spritesheets = {}


def _get_sound(name: str) -> pygame.Sound:
    if name not in _sounds:
        _sounds[name] = pygame.Sound(SOUND_DIRECTORY / name)
    return _sounds[name]


def play_sound(
    name: str, channel_id: int | None = None, volume: float = 1.0, **kwargs
) -> pygame.Channel | None:
    """Play a sound with the given name, on the given channel.

    name is the file name in the sound directory.
    channel_id is the id of the channel to play it on. Defaults to none,
    meaning a channel is automatically used.

    If mute is True, return None instead of the channel object.
    """
    if mute:
        return None
    sound = _get_sound(name)
    sound.set_volume(volume)
    if channel_id is None:
        return sound.play(**kwargs)
    channel = pygame.Channel(channel_id)
    channel.play(sound, **kwargs)
    return channel
