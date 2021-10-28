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
    '--pixeltype', '-p',
    help='The pixel type, the default is U16.',
    type=str,
    default='U16',
    required=False)
@click.option(
    '--compression', '-c',
    help='If or not compress data, the default is false.',
    type=bool,
    default=False,
    required=False)
@click.option(
    '--merged-file', '-o',
    help='The name of merged file. For example, res/2019_image_data.tif.',
    required=True)
def main(input_folder, scope, origin, resolution, tilesize, pixeltype, compression, merged_file):
    merge_tiles(input_folder, scope, origin, resolution, tilesize, pixeltype, compression, merged_file)


def merge_tiles(input_folder, scope, origin, resolution, tilesize, pixeltype, compression, merged_file):
    originX = origin[0]
    originY = origin[1]
    minX = scope[0]
    maxX = scope[1]
    minY = scope[2]
    maxY = scope[3]

    min_col, min_row = get_col_row(originX, originY, minX, maxY, tilesize, resolution)
    max_col, max_row = get_col_row(originX, originY, maxX, minY, tilesize, resolution)

    tilewidth = max_col - min_col + 1
    tileheight = max_row - min_row + 1

    if pixeltype == 'U8':
        gdal_pixel_type = gdal.GDT_Byte
    elif pixeltype == 'S8':
        gdal_pixel_type = gdal.GDT_Byte
    elif pixeltype == 'U16':
        gdal_pixel_type = gdal.GDT_UInt16
    elif pixeltype == 'S16':
        gdal_pixel_type = gdal.GDT_Int16
    elif pixeltype == 'U32':
        gdal_pixel_type = gdal.GDT_UInt32
    elif pixeltype == 'S32':
        gdal_pixel_type = gdal.GDT_Int32
    elif pixeltype == 'F32':
        gdal_pixel_type = gdal.GDT_Float32
    elif pixeltype == 'F64':
        gdal_pixel_type = gdal.GDT_Float64
    else:
        log.warning('未知的像素类型，使用默认值64位浮点型.')
        gdal_pixel_type = gdal.GDT_Float64

    suffix = os.path.splitext(merged_file)[1]
    if suffix == "":
        suffix = "tif"
        merged_file = merged_file + "." + suffix

    start = time.time()

    log.info("创建输出文件...")
    out_ds = create_merge_file(merged_file, tilewidth, tileheight, tilesize, gdal_pixel_type)

    if out_ds is None:
        log.error("输出文件创建失败!")
        return
    log.info("输出文件创建成功！")

    log.info("开始影像纠偏...")

    ulx = originX + min_col * tilesize * resolution
    uly = originY - min_row * tilesize * resolution

    geotransform = [ulx, resolution, 0, uly, 0, -resolution]
    out_ds.SetGeoTransform(geotransform)

    log.info("影像纠偏完成.")
    out_ds = None

    # if os.path.exists(temp_origin_file):
    #     os.remove(temp_origin_file)

    out_ds = gdal.Open(merged_file, 1)

    log.info('开始拼接...')
    try:
        icount = 0
        total_count = tilewidth * tileheight
        tasks = []
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)

        for root, subDirs, files in os.walk(input_folder):  # e:/8_res E:/Source code/TrafficDataAnalysis/Spider/res/tilemap/5
            for subDir in subDirs:
                y = int(subDir)
                for root2, subDirs2, files2 in os.walk(os.path.join(root, subDir)):
                # input_file = os.path.join(root, filename)
                #
                # name = os.path.splitext(filename)[0]
                    for filename in files2:
                        x = int(os.path.splitext(filename)[0])
                        input_file = os.path.join(root, subDir, filename)

                        icount += 1

                        if len(tasks) >= 5000:
                            tasks.append(asyncio.ensure_future(merge_one_tile(input_file, out_ds, gdal_pixel_type, tilesize, x, y, min_col, min_row)))
                            loop.run_until_complete(asyncio.wait(tasks))

                            tasks = []

                            log.debug("{:.0%}".format(icount / total_count))
                            continue
                        else:
                            tasks.append(asyncio.ensure_future(merge_one_tile(input_file, out_ds, gdal_pixel_type, tilesize, x, y, min_col, min_row)))

        if len(tasks) > 0:
            loop.run_until_complete(asyncio.wait(tasks))

    except:
        log.error("拼接失败，请检查输入文件！{}".format(traceback.format_exc()))
        return

    out_ds = None
    dr = None

    if icount != total_count:
        log.error("拼接存在错误，请检查参数或者瓦片的完整性！")
        return
    else:
        log.info('拼接完成.')

    if compression:
        log.info("开始压缩...")
        filename = os.path.splitext(merged_file)[0]
        suffix = os.path.splitext(merged_file)[1]
        compression_file = filename + "_compression" + suffix
        translateOptions = gdal.TranslateOptions(format='GTiff', creationOptions=["BIGTIFF=YES", "COMPRESS=LZW"], callback=progress_callback)
        gdal.Translate(compression_file, merged_file, options=translateOptions)
        log.info("压缩完成...")
        merged_file = compression_file

    log.info("开始构建影像金字塔...")
    out_ds = gdal.OpenEx(merged_file, gdal.OF_RASTER | gdal.OF_READONLY)
    gdal.SetConfigOption('COMPRESS_OVERVIEW', 'LZW')
    out_ds.BuildOverviews("nearest", range(2, 16, 2), callback=progress_callback)  # 第二个参数表示建立多少级金字塔, QGIS里面默认是2,4,8,16
    out_ds=None
    log.info("影像金字塔构建成功.")

    end = time.time()
    log.info("合并瓦片任务完成! 总共耗时{}秒. 影像存储至{}.\n".format("{:.2f}".format(end - start), merged_file))


async def merge_one_tile(input_file, out_ds, gdal_pixel_type, tilesize, x, y, min_col, min_row):
    ds = gdal.Open(input_file)

    r, g, b = await read_raster(ds, 0, 0, tilesize, tilesize, gdal_pixel_type)

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


def create_merge_file(temp_file, tilewidth, tileheight, tilesize, gdal_pixel_type):
    try:
        # log.info('开始创建merged_file...')
        dr = gdal.GetDriverByName("GTiff")
        out_ds = dr.Create(temp_file, tilewidth * tilesize, tileheight * tilesize, 3, gdal_pixel_type, options=["BIGTIFF=YES", "TILED=YES", "INTERLEAVE=PIXEL"])
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
