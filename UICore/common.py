import base64
import json
import math
import os
import re
import time

from UICore.Gv import srs_dict, SpatialReference
from UICore.log4p import Log
import urllib.request, urllib.parse

log = Log()


def get_json(url):
    try_num = 5
    # 定义请求头
    reqheaders = {'Content-Type': 'application/x-www-form-urlencoded',
                  'Host': 'suplicmap.pnr.sz',
                  'Pragma': 'no-cache'}
    # 请求不同页面的数据
    trytime = 0
    while trytime < try_num:
        try:
            req = urllib.request.Request(url=url, headers=reqheaders)
            r = urllib.request.urlopen(req)
            respData = r.read().decode('utf-8', 'ignore')
            # return respData
            res = json.loads(respData)
            if 'error' not in res.keys():
                return res
        except:
            # log.error('HTTP请求失败！重新尝试...')
            trytime += 1

        time.sleep(2)
        continue


def get_paraInfo(url):
    http = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    res = re.match(http, string=url)
    url_json = url + "?f=pjson"
    if res is not None:
        getInfo = get_json(url_json)
        return getInfo
    else:
        return None


def defaultTileFolder(url, level):
    # url_encodeStr = str(base64.b64encode(url.encode("utf-8")), "utf-8")
    url_encodeStr = urlEncodeToFileName(url)
    path = os.path.join(os.getcwd(), "data", "tiles", url_encodeStr, str(level))
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def urlEncodeToFileName(url):
    url_encodeStr = str(base64.b64encode(url.encode("utf-8")), "utf-8")
    return url_encodeStr


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


def get_col_row(x0, y0, x, y, size, resolution):
    col = math.floor(math.fabs((x0 - x) / (size * resolution)))
    row = math.floor(math.fabs((y0 - y) / (size * resolution)))

    return col, row


def get_srs_desc_by_epsg(name: str):
    if name == "2435":
        return srs_dict[SpatialReference.sz_Local]
    elif name == "4490":
        return srs_dict[SpatialReference.gcs_2000]
    elif name == "4547":
        return srs_dict[SpatialReference.pcs_2000]
    elif name == "4526":
        return srs_dict[SpatialReference.pcs_2000_zone]
    elif name == "4326":
        return srs_dict[SpatialReference.wgs84]
    elif name == "4610":
        return srs_dict[SpatialReference.gcs_xian80]
    elif name == "2383":
        return srs_dict[SpatialReference.pcs_xian80]
    elif name == "2362":
        return srs_dict[SpatialReference.pcs_xian80_zone]


def overwrite_cpg_file(outpath, outfile, encoding):
    try:
        cpg_file = os.path.join(outpath, outfile + ".cpg")
        if not os.path.exists(cpg_file):
            os.makedirs(cpg_file)

        with open(cpg_file, "w+") as f:
            f.seek(0)
            f.truncate() #清空文件
            f.write(encoding)
    finally:
        if f:
            f.close()
