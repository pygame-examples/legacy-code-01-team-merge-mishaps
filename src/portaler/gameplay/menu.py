from ..interfaces import GameStateInterface


class Menu(GameStateInterface):
    """
    Main menu (NOT IMPLEMENTED)

    Only reason this exists is for testing ATM
    """

    def __init__(self):
        raise NotImplementedError

    async def update_physics(self, dt: float):
        return super().update_physics(dt)

    async def render(self, size: tuple[int, int], dt_since_physics: float):
        # surface = pygame.Surface(size)
        pass
