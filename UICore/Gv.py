import base64
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


def defaultTileFolder(url, level):
    url_encodeStr = str(base64.b64encode(url.encode("utf-8")), "utf-8")
    path = os.path.join(os.getcwd(), "data", "tiles", url_encodeStr, str(level))
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def defaultImageFile(url, level):
    url_encodeStr = str(base64.b64encode(url.encode("utf-8")), "utf-8")
    if not os.path.exists(os.path.join(os.getcwd(), "data")):
        os.makedirs(os.path.join(os.getcwd(), "data"))
    file = os.path.join(os.getcwd(), "data", "{}_{}".format(url_encodeStr, str(level)))
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
