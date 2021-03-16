from enum import Enum

class Dock(Enum):
    left = 0
    right = 1
    up = 2
    down = 3


class SplitterState(Enum):
    collapsed = 0
    expanded = 1

class Gv:
    defaultTilePath = ""