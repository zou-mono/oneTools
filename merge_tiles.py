import os
from osgeo import gdal
from UICore.log4p import Log
import time
import click
import math
import traceback
import urllib.request, urllib.parse
import json

log = Log(__file__)
try_num = 10

@click.command()
@click.option(
    '--input-folder', '-f',
    help='Tiles folder. For example, D:/tilemap/8',
    required=True)
@click.option(
    '--url', '-u',
    help='Input url. For example, http://suplicmap.pnr.sz/dynaszmap_3/rest/services/SZMAP_DLJT_GKDL/MapServer',
    required=False)
@click.option(
    '--level', '-l',
    help='tile level. For example, 8',
    type=int,
    default=0,
    required=True)
@click.option(
    '--scope', '-s', type=(float, float, float, float),
    help='The geographical range of map, [min_row, max_row, min_col, max_col]. '
         'For example, 80574.81260346594 176816.21260346594 1012.1329692534127 56528.33296925342]. If url is set, will ignore this value. ',
    # default = [113.71108739900001, 114.64969729900001, 22.437257323, 22.872570623],
    # default=[80574.81260346594, 176816.21260346594, 1012.1329692534127, 56528.33296925342],
    default = [None, None, None, None],
    required=False)
@click.option(
    '--origin', type=(float, float),
    help='The origin x and y of tiles. For example, -5123300 10002300. If url is set, will ignore this value.',
    # default=[-180.0, 90.0],
    default = [None, None],
    required=False)
@click.option(
    '--resolution',
    help='The tile resolution. For example, 13.229193125052918. If url is set, will ignore this value.',
    type=float,
    # default=0.0013732910156250004, # level 0
    required=False)
@click.option(
    '--tilesize', '-t',
    help='The tile size, the default is 256.',
    type=int,
    default=256,
    required=False)
@click.option(
    '--merged-file', '-o',
    help='The name of merged file. For example, res/2019_image_data.tif.',
    required=True)
def main(input_folder, url, level, scope, origin, resolution, tilesize, merged_file):
    merge_tiles(input_folder, url, level, scope, origin, resolution, tilesize, merged_file)


def merge_tiles(input_folder, url, level, scope, origin, resolution, tilesize, merged_file):
    if url is not None:
        if url[-1] == r"/":
            url = url[:-1]

        url_json = url + "?f=pjson"
        getInfo = get_json(url_json)

        tilesize = getInfo['tileInfo']['rows']  # 瓦片尺寸
        originX = getInfo['tileInfo']['origin']['x']  # 初始x
        originY = getInfo['tileInfo']['origin']['y']  # 初始y
        minX = getInfo['extent']['xmin']  # xmin
        minY = getInfo['extent']['ymin']  # ymin
        maxX = getInfo['extent']['xmax']  # xmax
        maxY = getInfo['extent']['ymax']  # ymax

        lods = getInfo['tileInfo']['lods']  # lod信息
        lod = get_lod(lods, level)
        resolution = lod['resolution']

    else:
        if origin is None:
            log.error("missing origin!")
            return
        if scope is None:
            log.error("missing scope!")
            return
        if resolution is None:
            log.error("missing resolution!")
            return

        originX = origin[0]
        originY = origin[1]
        minX = scope[0]
        maxX = scope[1]
        minY = scope[2]
        maxY = scope[3]

    min_col, min_row = get_col_row(originX, originY, minX, maxY, tilesize, resolution)
    max_col, max_row =  get_col_row(originX, originY, maxX, minY, tilesize, resolution)

    tilewidth = max_col - min_col + 1
    tileheight = max_row - min_row + 1

    name = os.path.basename(merged_file).split('.')[0]
    suffix = os.path.splitext(merged_file)[1]
    if suffix == "":
        suffix = "tif"
        merged_file = merged_file + "." + suffix
    cur_path = os.path.dirname(merged_file)
    temp_file = os.path.join(cur_path, name + "_temp" + "." + suffix)    # 没有纠偏的临时文件

    start = time.time()

    if os.path.exists(temp_file):
        os.remove(temp_file)

    out_ds = create_merge_file(temp_file, tilewidth, tileheight, tilesize)

    if out_ds is None:
        return

    out_r = out_ds.GetRasterBand(1)
    out_g = out_ds.GetRasterBand(2)
    out_b = out_ds.GetRasterBand(3)

    log.info('开始拼接')
    icount = 0
    for root, subDir, files in os.walk(input_folder):  # e:/8_res E:/Source code/TrafficDataAnalysis/Spider/res/tilemap/5
        for filename in files:
            ds = gdal.Open(os.path.join(root, filename))
            redBand = ds.GetRasterBand(1)
            greenBand = ds.GetRasterBand(2)
            blueBand = ds.GetRasterBand(3)
            r = redBand.ReadRaster(0, 0, tilesize, tilesize, tilesize, tilesize, gdal.GDT_Int16)
            g = greenBand.ReadRaster(0, 0, tilesize, tilesize, tilesize, tilesize, gdal.GDT_Int16)
            b = blueBand.ReadRaster(0, 0, tilesize, tilesize, tilesize, tilesize, gdal.GDT_Int16)

            name = os.path.splitext(filename)[0]
            y = int(name.split('_')[0])
            x = int(name.split('_')[1])
            out_r.WriteRaster((x - min_col) * tilesize, (y - min_row) * tilesize, tilesize, tilesize, r, tilesize, tilesize)
            out_g.WriteRaster((x - min_col) * tilesize, (y - min_row) * tilesize, tilesize, tilesize, g, tilesize, tilesize)
            out_b.WriteRaster((x - min_col) * tilesize, (y - min_row) * tilesize, tilesize, tilesize, b, tilesize, tilesize)

            # out_r.FlushCache()
            # out_g.FlushCache()
            # out_b.FlushCache()

            icount += 1
            # print(icount)
            if icount % 1000 == 0:
                log.debug(icount)
    log.info('拼接完成.')
    out_ds = None
    dr = None

    log.info("开始影像纠偏...")
    gcp_x0 = math.floor(((minX - originX) - min_col * (resolution * tilesize)) / resolution)
    gcp_y0 = math.floor(((originY - maxY) - min_row * (resolution * tilesize)) / resolution)
    gcp_x1 = tilewidth * tilesize - (tilesize - math.floor(((maxX - originX) - max_col * (resolution * tilesize)) / resolution))
    gcp_y1 = tileheight * tilesize - (tilesize - math.floor(((originY - minY) - max_row * (resolution * tilesize)) / resolution))

    gcp_list = [gdal.GCP(minX, maxY, 0, gcp_x0, gcp_y0),
                gdal.GCP(maxX, maxY, 0, gcp_x1, gcp_y0),
                gdal.GCP(minX, minY, 0, gcp_x0, gcp_y1),
                gdal.GCP(maxX, minY, 0, gcp_x1, gcp_y1)]

    tmp_ds = gdal.Open(temp_file, 1)
    # gdal的config放在creationOptions参数里面
    translateOptions = gdal.TranslateOptions(format='GTiff', creationOptions=["BIGTIFF=YES", "COMPRESS=LZW"], GCPs=gcp_list)
    gdal.Translate(merged_file, tmp_ds, options=translateOptions)
    tmp_ds = None
    log.info("影像纠偏完成.")

    log.info("开始构建影像金字塔...")
    out_ds = gdal.OpenEx(merged_file, gdal.OF_RASTER | gdal.OF_READONLY)
    gdal.SetConfigOption('COMPRESS_OVERVIEW', 'LZW')
    out_ds.BuildOverviews("nearest", range(2, 16, 2))  # 第二个参数表示建立多少级金字塔, QGIS里面默认是2,4,8,16
    out_ds=None
    log.info("影像金字塔构建成功.")

    end = time.time()
    log.info("所有操作OK!耗时" + str(end - start))


def create_merge_file(temp_file, tilewidth, tileheight, tilesize):
    try:
        log.info('开始创建merged_file...')
        dr = gdal.GetDriverByName("GTiff")
        out_ds = dr.Create(temp_file, tilewidth * tilesize, tileheight * tilesize, 3, gdal.GDT_Int16, options=["BIGTIFF=YES", "COMPRESS=LZW", "TILED=YES", "INTERLEAVE=PIXEL"])
        log.info('创建成功.')
        return out_ds
    except:
        log.error('创建失败!' + traceback.format_exc())
        return None


def get_col_row(x0, y0, x, y, size, resolution):
    col = math.floor(math.fabs((x0 - x) / (size * resolution)))
    row = math.floor(math.fabs((y0 - y) / (size * resolution)))

    return col, row


def get_json(url):
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
            respData = r.read().decode('utf-8')
            # return respData
            res = json.loads(respData)
            if 'error' not in res.keys():
                return res
        except:
            # log.error('HTTP请求失败！重新尝试...')
            trytime += 1

        time.sleep(2)
        continue


def get_lod(lods, level):
    for lod in lods:
        if lod['level'] == level:
            return lod


if __name__ == '__main__':
    gdal.UseExceptions()
    main()
