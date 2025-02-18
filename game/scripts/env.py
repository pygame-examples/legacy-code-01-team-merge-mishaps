"""
Put OS specific code in here
"""
import sys

PYGBAG: bool = sys.platform == "emscripten"

CAN_CAP_FPS: bool = not PYGBAG