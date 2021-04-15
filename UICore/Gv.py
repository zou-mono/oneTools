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


class SpatialReference(Enum):
    sz_Local = 0
    gcs_2000 = 1
    pcs_2000 = 2
    pcs_2000_zone = 3
    wgs84 = 4
    bd09 = 5
    gcj02 = 6
    gcs_xian80 = 7
    pcs_xian80 = 8
    pcs_xian80_zone = 9


class DataType(Enum):
    shapefile = 0
    geojson = 1
    cad_dwg = 2
    fileGDB = 3
    csv = 4


def singleton(cls):
    instances = {}

    def _singleton(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return _singleton

srs_dict = {
    SpatialReference.sz_Local: "深圳独立",
    SpatialReference.gcs_2000: "CGCS2000地理",
    SpatialReference.pcs_2000: "CGCS2000投影",
    SpatialReference.pcs_2000_zone: "CGCS2000投影(包含带号)",
    SpatialReference.wgs84: "WGS84",
    SpatialReference.bd09: "百度地理",
    SpatialReference.gcj02: "火星",
    SpatialReference.gcs_xian80: "西安80地理",
    SpatialReference.pcs_xian80: "西安80投影",
    SpatialReference.pcs_xian80_zone: "西安80投影(包含带号)"
}

srs_list = ["深圳独立", "CGCS2000投影", "WGS84", "百度地理", "火星", "CGCS2000地理",
            "CGCS2000投影(包含带号)", "西安80地理", "西安80投影", "西安80投影(包含带号)"]


