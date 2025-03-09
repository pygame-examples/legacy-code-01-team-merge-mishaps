from pathlib import Path
import pytmx


from .interfaces import GameLevelInterface


class LevelLoader:
    def __init__(self, target: GameLevelInterface, levels: pytmx.TiledProject, name: str):
        self.target = target
        self.levels = levels
        self.name = name

        self.map = self.levels.get(self.name)
        self.load_configs()

    def load_configs(self):
        configs = self.map.get_layer_by_name("Config")
        for config in configs:
            if not isinstance(config, pytmx.TiledObject): continue

            if config.name == "CameraViewRange":
                self.target.set_camera_view((config.x, config.y, config.width, config.height))

            # TODO: finish
