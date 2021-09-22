import os
from osgeo import gdal
from UICore.log4p import Log
import time
import click
import math
import traceback
from UICore.common import get_col_row
import asyncio

log = Log(__name__)
try_num = 10

@click.command()
@click.option(
    '--input-folder', '-f',
    help='Tiles folder. For example, D:/tilemap/8',
    required=True)
# @click.option(
#     '--url', '-u',
#     help='Input url. For example, http://suplicmap.pnr.sz/dynaszmap_3/rest/services/SZMAP_DLJT_GKDL/MapServer',
#     required=False)
# @click.option(
#     '--level', '-l',
#     help='tile level. For example, 8',
#     type=int,
#     default=0,
#     required=True)
@click.option(
    '--scope', '-s', type=(float, float, float, float),
    help='The geographical range of map, [min_row, max_row, min_col, max_col]. '
         'For example, 80574.81260346594 176816.21260346594 1012.1329692534127 56528.33296925342]. If url is set, will ignore this value. ',
    # default = [113.71108739900001, 114.64969729900001, 22.437257323, 22.872570623],
    # default=[80574.81260346594, 176816.21260346594, 1012.1329692534127, 56528.33296925342],
    default=[None, None, None, None],
    required=True)
@click.option(
    '--origin', type=(float, float),
    help='The origin x and y of tiles. For example, -5123300 10002300. If url is set, will ignore this value.',
    # default=[-180.0, 90.0],
    default=[None, None],
    required=True)
@click.option(
    '--resolution',
    help='The tile resolution. For example, 13.229193125052918. If url is set, will ignore this value.',
    type=float,
    # default=0.0013732910156250004, # level 0
    required=True)
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
def main(input_folder, scope, origin, resolution, tilesize, merged_file):
    merge_tiles(input_folder, scope, origin, resolution, tilesize, merged_file)


def merge_tiles(input_folder, scope, origin, resolution, tilesize, merged_file):
    originX = origin[0]
    originY = origin[1]
    minX = scope[0]
    maxX = scope[1]
    minY = scope[2]
    maxY = scope[3]

    d = gdal.Open(r"D:\Codes\oneTools\data\tiles\out5_1.tif")
    print(d.GetGeoTransform())

    min_col, min_row = get_col_row(originX, originY, minX, maxY, tilesize, resolution)
    max_col, max_row = get_col_row(originX, originY, maxX, minY, tilesize, resolution)

    tilewidth = max_col - min_col + 1
    tileheight = max_row - min_row + 1

    name = os.path.basename(merged_file).split('.')[0]
    suffix = os.path.splitext(merged_file)[1]
    if suffix == "":
        suffix = "tif"
        merged_file = merged_file + "." + suffix
    cur_path = os.path.dirname(merged_file)
    if not os.path.exists(os.path.join(cur_path, "tmp")):
        os.makedirs(os.path.join(cur_path, "tmp"))
    temp_file = os.path.join(cur_path, "tmp", name + "_temp" + "." + suffix)    # 纠偏后的临时文件
    temp_origin_file = os.path.join(cur_path, "tmp", name + "_origin_temp" + "." + suffix)    # 没有纠偏的临时文件

    start = time.time()

    if os.path.exists(temp_file):
        os.remove(temp_file)
    if os.path.exists(temp_origin_file):
        os.remove(temp_origin_file)

    log.info("创建输出文件...")
    out_ds = create_merge_file(merged_file, tilewidth, tileheight, tilesize)

    if out_ds is None:
        log.error("输出文件创建失败!")
        return
    log.info("输出文件创建成功！")

    log.info("开始影像纠偏...")
    # gcp_x0 = math.floor(((minX - originX) - min_col * (resolution * tilesize)) / resolution)
    # gcp_y0 = math.floor(((originY - maxY) - min_row * (resolution * tilesize)) / resolution)
    # gcp_x1 = tilewidth * tilesize - (tilesize - math.floor(((maxX - originX) - max_col * (resolution * tilesize)) / resolution))
    # gcp_y1 = tileheight * tilesize - (tilesize - math.floor(((originY - minY) - max_row * (resolution * tilesize)) / resolution))
    ulx = originX + min_col * tilesize * resolution
    uly = originY - min_row * tilesize * resolution

    geotransform = [ulx, resolution, 0, uly, 0, -resolution]
    out_ds.SetGeoTransform(geotransform)

    # gcp_list = [gdal.GCP(minX, maxY, 0, gcp_x0, gcp_y0),
    #             gdal.GCP(maxX, maxY, 0, gcp_x1, gcp_y0),
    #             gdal.GCP(minX, minY, 0, gcp_x0, gcp_y1),
    #             gdal.GCP(maxX, minY, 0, gcp_x1, gcp_y1)]

    # # gdal的config放在creationOptions参数里面
    # translateOptions = gdal.TranslateOptions(format='GTiff', creationOptions=["BIGTIFF=YES", "COMPRESS=NONE"], GCPs=gcp_list, callback=progress_callback)
    # gdal.Translate(merged_file, out_ds, options=translateOptions)
    log.info("影像纠偏完成.")
    out_ds = None

    # if os.path.exists(temp_origin_file):
    #     os.remove(temp_origin_file)

    log.info('开始拼接...')
    out_ds = gdal.Open(merged_file, 1)
    out_r = out_ds.GetRasterBand(1)
    out_g = out_ds.GetRasterBand(2)
    out_b = out_ds.GetRasterBand(3)

    icount = 0
    iprop = 1
    total_count = tilewidth * tileheight
    tasks = []
    loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(loop)

    for root, subDir, files in os.walk(input_folder):  # e:/8_res E:/Source code/TrafficDataAnalysis/Spider/res/tilemap/5
        for filename in files:
            input_file = os.path.join(root, filename)
            name = os.path.splitext(filename)[0]
            y = int(name.split('_')[0])
            x = int(name.split('_')[1])

            icount += 1

            if icount >= 5000:
                tasks.append(asyncio.ensure_future(merge_one_tile(input_file, out_ds, tilesize, x, y, min_col, min_row)))
                loop.run_until_complete(asyncio.wait(tasks))

                if int(icount * 100 / total_count) == iprop * 20:
                    log.debug("{:.0%}".format(icount / total_count))
                    iprop += 1
            else:
                tasks.append(asyncio.ensure_future(merge_one_tile(input_file, out_ds, tilesize, x, y, min_col, min_row)))

    if len(tasks) > 0:
        loop.run_until_complete(asyncio.wait(tasks))

    out_ds = None
    dr = None

    if icount != total_count:
        log.error("拼接存在错误，请检查参数或者瓦片的完整性！")
        return
    else:
        log.info('拼接完成.')

    # log.info("开始压缩...")
    # translateOptions = gdal.TranslateOptions(format='GTiff', creationOptions=["BIGTIFF=YES", "COMPRESS=LZW"], callback=progress_callback)
    # gdal.Translate("tmp.tiff", temp_file, options=translateOptions)
    # log.info("压缩完成...")

    log.info("开始构建影像金字塔...")
    out_ds = gdal.OpenEx(merged_file, gdal.OF_RASTER | gdal.OF_READONLY)
    gdal.SetConfigOption('COMPRESS_OVERVIEW', 'LZW')
    out_ds.BuildOverviews("nearest", range(2, 16, 2), callback=progress_callback)  # 第二个参数表示建立多少级金字塔, QGIS里面默认是2,4,8,16
    out_ds=None
    log.info("影像金字塔构建成功.")

    end = time.time()
    log.info("合并瓦片任务完成! 总共耗时{}秒. 影像存储至{}.\n".format("{:.2f}".format(end - start), merged_file))


async def merge_one_tile(input_file, out_ds, tilesize, x, y, min_col, min_row):
    ds = gdal.Open(input_file)

    out_r = out_ds.GetRasterBand(1)
    out_g = out_ds.GetRasterBand(2)
    out_b = out_ds.GetRasterBand(3)

    r, g, b = await read_raster(ds, 0, 0, tilesize, tilesize, gdal.GDT_Int16)

    await write_raster(out_ds, x, y, min_col, min_row, tilesize, tilesize, r, g, b)
    # out_r.WriteRaster((x - min_col) * tilesize, (y - min_row) * tilesize, tilesize, tilesize, r, tilesize, tilesize)
    # out_g.WriteRaster((x - min_col) * tilesize, (y - min_row) * tilesize, tilesize, tilesize, g, tilesize, tilesize)
    # out_b.WriteRaster((x - min_col) * tilesize, (y - min_row) * tilesize, tilesize, tilesize, b, tilesize, tilesize)

    ds = None


async def read_raster(ds, x0, y0, tilesize_x, tilesize_y, type):
    redBand = ds.GetRasterBand(1)
    greenBand = ds.GetRasterBand(2)
    blueBand = ds.GetRasterBand(3)

    r = redBand.ReadRaster(x0, y0, tilesize_x, tilesize_y, tilesize_x, tilesize_y, type)
    g = greenBand.ReadRaster(x0, y0, tilesize_x, tilesize_y, tilesize_x, tilesize_y, type)
    b = blueBand.ReadRaster(x0, y0, tilesize_x, tilesize_y, tilesize_x, tilesize_y, type)

    return r, g, b


async def write_raster(out_ds, x, y, min_col, min_row, tilesize_x, tilesize_y, r, g, b):
    out_r = out_ds.GetRasterBand(1)
    out_g = out_ds.GetRasterBand(2)
    out_b = out_ds.GetRasterBand(3)

    out_r.WriteRaster((x - min_col) * tilesize_x, (y - min_row) * tilesize_y, tilesize_x, tilesize_y, r, tilesize_x, tilesize_y)
    out_g.WriteRaster((x - min_col) * tilesize_x, (y - min_row) * tilesize_y, tilesize_x, tilesize_y, g, tilesize_x, tilesize_y)
    out_b.WriteRaster((x - min_col) * tilesize_x, (y - min_row) * tilesize_y, tilesize_x, tilesize_y, b, tilesize_x, tilesize_y)


def progress_callback(complete, message, unknown):
    # Calculate percent by integer values (1, 2, ..., 100)
    if int(complete * 100) % 20 == 0:
        percent = int(complete * 100)
        log.debug("{}%".format(percent))
    return 1


def create_merge_file(temp_file, tilewidth, tileheight, tilesize):
    try:
        # log.info('开始创建merged_file...')
        dr = gdal.GetDriverByName("GTiff")
        out_ds = dr.Create(temp_file, tilewidth * tilesize, tileheight * tilesize, 3, gdal.GDT_Int16, options=["BIGTIFF=YES", "COMPRESS=NONE", "TILED=YES", "INTERLEAVE=PIXEL"])
        # log.info('创建成功.')
        return out_ds
    except:
        log.error('创建影像文件失败!' + traceback.format_exc())
        return None


def get_lod(lods, level):
    for lod in lods:
        if lod['level'] == level:
            return lod


if __name__ == '__main__':
    gdal.UseExceptions()
    main()
