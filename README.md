## Guide to source code:

```
pytmx/  - copied source code of a library pytmx used for loading Tiled files with intention of easier tampering/implementing mising features.    
    project_loader.py  – example of this "tampering"
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
            physics.py  - a mess    (another teamate: can confirm)
        intefaces.py  - most of the abstract classes, also partially constants
        const.py  - hopefully the rest of constants
        game_input.py  - simplified interface for getting input
    main.py  - using here asynchronous, split game loop (separate "threads" for rendering, physics and input polling
```

To see what to do, might be useful reading the TODO-s.

======= GAMEPLAY =======
To move press either WASD or arrow keys
To jump press SPACE
To interact (pick up or throw) press E
To slam down double press DOWN (S or down arrow)

------- plan -------
make this README more beautiful
implement some cool levels, most probably puzzles (definatelly not a ripoff of portal 2, noooooo)
learn how to read TODOs inside code, because someone probably left something important there

Add buttons to the game
Add something buttons can activate (portals, doors, one-way-platforms, whatever)
Make easier level creation with Tiled (probably, that's what polastyn was hinting at using, but i personally dont know)