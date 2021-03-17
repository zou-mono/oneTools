import os
import sys
from enum import Enum

class Dock(Enum):
    left = 0
    right = 1
    up = 2
    down = 3


class SplitterState(Enum):
    collapsed = 0
    expanded = 1


def defaultTileFolderPath():
    path = os.path.join(os.getcwd(), "data", "tiles")
    if not os.path.exists(path):
        os.mkdir(path)
    return path


def defaultImageFile():
    file = os.path.join(os.getcwd(), "data", "output_img")
    return launderName(file + '.tif')


def launderName(name):
    dir = os.path.dirname(name)
    basename, suffix = os.path.splitext(name)
    if os.path.exists(name) and os.path.isfile(name):
        basename = basename + "_1"
        name = os.path.join(dir, basename + suffix)

    if not (os.path.exists(name)):
        return name
    else:
        return launderName(name)
