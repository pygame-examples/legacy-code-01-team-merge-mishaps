# Unofficial Pygame Community Pass-the-code Game Jam 2025
There are two teams, each creating a game. Only one person from each team works at the team's project in a given moment. Each participant has as week to work on the project. After that time is up, it's the turn for the next person. Commit to the repository regularly to avoid code loss (in your time frame).

Team two Merge Mishaps (times are in UTC):
1) @Sir Jiffbert Robbleton Monday, February 17, 2025 at 12:00 AM - Monday, February 24, 2025 at 12:00 AM
2) @Aiden jester of fates Monday, February 24, 2025 at 12:00 AM - Monday, March 3, 2025 at 12:00 AM
3) @polastyn Monday, March 3, 2025 at 12:00 AM - Monday, March 10, 2025 at 12:00 AM
4) @Lord Andrey Gramatikal Wizard Monday, March 10, 2025 at 12:00 AM - Sunday, March 17, 2025 at 12:00 AM
5) @Matiiss Monday, March 17, 2025 at 12:00 AM - Monday, March 24, 2025 at 12:00 AM
6) @nuclear pasta Monday, March 24, 2025 at 12:00 AM - Monday, March 31, 2025 at 12:00 AM

The jam has ended and the final state of the codebase for the jam is at [this tag](https://github.com/pygame-examples/legacy-code-01-team-merge-mishaps/releases/tag/game-jam-end).
Any commits after the tag are not part of the jam.

## Controls
- To move use either `<WASD>` or `<ARROW>` keys
- To jump press `SPACE`
- To slam down press `S` or `DOWN` key
- To interact (pick up or throw) press `E`
- Aim your throws by holding movement keys in the direction you want to throw
  - note: some directions might not work on certain keyboards depending on key rollover ability
- To restart the current level, press `R`
- To toggle mute, press `M`


## To run
You must have `pygame-ce` installed.
Run:
```bash
python main.py
```


## Development
Not sure what to do? Try looking for `TODO`s and do those.  
Also check out `src/portaler/assets/ideas` for some level ideas.

### Environment setup
#### With [`uv`](https://docs.astral.sh/uv/):
First run
```bash
uv sync --all-extras
```
Then activate the virutal environment (there's a space after the first `.`):
```bash
. .venv/bin/activate  # On Linux
. .venv/source/activate  # On Windows
```
And/or select the appropriate interpreter in your IDE

Also make sure to install pre-commit hooks:
```bash
uvx pre-commit install
```


### The plan / some more TODOs
- [x] make this README more beautiful
- [ ] learn how to read TODOs inside code, because someone probably left something important there
- [ ] menu
- [ ] music
- [ ] throwable sounds


### Guide to the source code
Might be slightly™ out of date
```
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
    main.py  - using here asynchronous, split game loop (separate "threads" for rendering, physics and input polling)
```
