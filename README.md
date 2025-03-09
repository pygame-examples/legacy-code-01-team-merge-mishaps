## Guide to source code:

```
pytmx/  - copied source code of a library pytmx used for loading Tiled files with intention of easier tampering/implementing mising features.
    project_loader.py  – example if this "tampering"
game/  - main directory... not a lot to say here
    assets/  - ...
        levels/  - tiled levels go here
        tilemaps/  - for the levels (currently none)
        levels.tiled-project  - open this file when editing with Tiled editor
    scripts/  - most of the logic really
        gameplay/  - the most related to the game itself
            block.py, player.py, portal.py  - simple game objects
            sprite.py  - semi-abstract class
            menu.py  - empty :(
            level.py  - what you see on the screen currently
            physics.py  - a mess
        intefaces.py  - most of the abstract classes, also partially constants
        const.py  - hopefully the rest of constants
        game_input.py  - simplified interface for getting input
    main.py  - using here asynchronous, split game loop (separate "threads" for rendering, physics and input polling
```

To see what to do, might be useful reading the TODO-s.