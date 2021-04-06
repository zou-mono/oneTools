import base64
import json
import math
import os
import re
import sys
import time
from enum import Enum


class Dock(Enum):
    left = 0
    right = 1
    up = 2
    down = 3


class SplitterState(Enum):
    collapsed = 0
    expanded = 1


def singleton(cls):
    instances = {}

    def _singleton(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return _singleton
