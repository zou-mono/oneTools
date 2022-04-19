import time
import aiohttp
import asyncio
from UICore.log4p import Log
import urllib.request, urllib.parse
import json
import os
import math
import click
import traceback
from UICore.asyncRequest import send_http
from UICore.common import get_col_row
import encodings.idna

try_num = 5
coroutine_num = 500  # 协程数

log = Log()
failed_urls = []
lock = asyncio.Lock()  # 协程锁

@click.command()
@click.option('--url', '-u',
              help='Input url. For example, http://suplicmap.pnr.sz/dynaszmap_3/rest/services/SZMAP_DLJT_GKDL/MapServer',
              required=True)
@click.option(
    '--file-name', '-f',
    help='If need to merge tiles, should offer output name of merged image. For example, '
         '2019_image_data. If no need to merge tiles, omit.',
    required=False)
@click.option(
    '--sr', '-s',
    help='srs EPSG ID. For example, 2435',
    type=int,
    default=2435,
    required=False)
@click.option(
    '--level', '-l',
    help='tile level. For example, 8',
    type=int,
    default=0,
    required=True)
@click.option(
    '--output-path', '-o',
    help='Output folder, need the full path. For example, res/tilemaps',
    required=True)
def main(url, level, x0, y0, xmin, xmax, ymin, ymax, resolution, tile_size, output_path):
    crawl_tilemap(url, level, x0, y0, xmin, xmax, ymin, ymax, resolution, tile_size, output_path)


def crawl_tilemap(url, level, x0, y0, xmin, xmax, ymin, ymax, resolution, tile_size, output_path):
    """crawler program for tilemap data in http://suplicmap.pnr.sz."""
    start = time.time()

    if url[-1] == "/":
        url = url[:-1]

    # if not os.path.exists(output_path):
    #     os.makedirs(output_path)

    # output_path = launderPath(output_path)
    # level_path = output_path + str(level)
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # getInfo = get_json(url_json)
    # out_file = write_info_to_json(getInfo, output_path)
    # log.info('输出影像信息json文件:{}'.format(out_file))

    # tile_size = getInfo['tileInfo']['rows']  # 瓦片尺寸
    # x0 = getInfo['tileInfo']['origin']['x']  # 初始x
    # y0 = getInfo['tileInfo']['origin']['y']  # 初始y
    # xmin = getInfo['extent']['xmin']  # xmin
    # ymin = getInfo['extent']['ymin']  # ymin
    # xmax = getInfo['extent']['xmax']  # xmax
    # ymax = getInfo['extent']['ymax']  # ymax

    # lods = getInfo['tileInfo']['lods']  # lod信息
    # lod = get_lod(lods, level)
    # resolution = lod['resolution']
    min_col, min_row = get_col_row(x0, y0, xmin, ymax, tile_size, resolution)
    print(str(min_col) + " " + str(min_row))
    max_col, max_row = get_col_row(x0, y0, xmax, ymin, tile_size, resolution)
    print(str(max_col) + " " + str(max_row))

    if min_row > max_row:
        log.error("最小行号大于最大行号,请检查参数！\n")
        return False
    elif min_col > max_col:
        log.error("最小列号大于最大列号,请检查参数！\n")
        return False

    log.info('\n开始使用协程抓取...')
    # for i in range(min_row, max_row):
    #     for j in range(min_col, max_col):
    #         tile_url = f'{url}/tile/{level}/{i}/{j}'
    #         output_img(tile_url, level_path, i, j)

    tasks = []
    loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(loop)
    # loop = asyncio.get_event_loop()
    total_count = (max_row - min_row + 1) * (max_col - min_col + 1)
    try:
        iloop = 0
        for i in range(min_row, max_row + 1):
            for j in range(min_col, max_col + 1):
                iloop += 1

                if not os.path.exists(f'{output_path}/{i}'):
                    os.makedirs(f'{output_path}/{i}')

                if os.path.exists(f'{output_path}/{i}/{j}.png') and os.path.getsize(f'{output_path}/{i}/{j}.png') > 0:
                    # if os.path.getsize(f'{output_path}/{i}_{j}.png') > 0:
                    continue
                # tile_url = url + "/tile/" + str(level) + "/" + str(i) + "/" + str(j)
                tile_url = f'{url}/tile/{level}/{i}/{j}'

                if len(tasks) >= coroutine_num:
                    tasks.append(asyncio.ensure_future(output_img_asyc(tile_url, output_path, i, j)))
                    loop.run_until_complete(asyncio.wait(tasks))
                    tasks = []
                    # iloop += 1
                    log.info("{:.0%}".format(iloop / total_count))
                    continue
                else:
                    tasks.append(asyncio.ensure_future(output_img_asyc(tile_url, output_path, i, j)))

        if len(tasks) > 0:
            loop.run_until_complete(asyncio.wait(tasks))
        log.info('协程抓取完成.')

        dead_link = 0
        if len(failed_urls) > 0:
            log.info('开始用单线程抓取失败的url...')
            while len(failed_urls) > 0:
                furl = failed_urls.pop()
                if not output_img2(furl[0], output_path, furl[1], furl[2]):
                    log.error('url:{} error:{}'.format(url, traceback.format_exc()))
                    dead_link += 1
    except:
        log.error("抓取失败，请检查参数！{}".format(traceback.format_exc()))
        return False

    end = time.time()
    if lock.locked():
        lock.release()
    # log.info('爬取瓦片任务完成！瓦片存储至{}.'.format(output_path))
    log.info('爬取瓦片任务完成！总共耗时:{}秒. 死链接数目为:{}. 瓦片存储至{}.'.format("{:.2f} \n".format(end - start), dead_link, output_path))
    return True


def url_json(url):
    if url[-1] == "/":
        url = url[:-1]

    return url + "?f=pjson"

def write_info_to_json(info, path):
    out_file = path + "tile_Info.json"
    with open(out_file, "w") as out:
        json.dump(info, out)
    return out_file


def launderPath(path):
    if path[-1] == os.sep:
        return path
    else:
        return path + os.sep


def get_tile(url):
    trytime = 0
    while trytime < try_num:
        try:
            req = urllib.request.Request(url=url)
            r = urllib.request.urlopen(req)
            respData = r.read()
            if len(respData) > 0:
                return respData
            else:
                raise Exception("传回数据为空")
        except:
            # log.debug('{}请求失败！重新尝试...'.format(url))
            trytime += 1

        time.sleep(1)
        continue
    return None


def output_img(url, output_path, i, j):
    try:
        img = get_tile(url)
        with open(f'{output_path}/{i}/{j}.png', "wb") as f:
            f.write(img)
        return True
    except:
        failed_urls.append([url, i, j])
        log.error('url:{} error:{}'.format(url, traceback.format_exc()))
        return False


def output_img2(url, output_path, i, j):
    try:
        img = get_tile(url)
        if img is not None:
            with open(f'{output_path}/{i}/{j}.png', "wb") as f:
                f.write(img)
        return True
    except:
        return False


async def get_tile_async(url, output_path, i, j):
    async with aiohttp.ClientSession() as session:
        try:
            respData = await send_http(session, method="get", respond_Type="content", read_timeout=10, url=url, retries=0)
            # response = await session.post(url, data=data, headers=reqheaders)
            if len(respData) > 0:
                return respData, url, output_path, i, j
            else:
                raise Exception("传回数据为空")
        except:
            # log.error('url:{} error:{}'.format(url, traceback.format_exc()))
            return None, url, output_path, i, j


async def output_img_asyc(url, output_path, i, j):
    bSkip = False
    try:
        img, url, output_path, i, j = await get_tile_async(url, output_path, i, j)
        # log.info('任务载入完成.')
        # log.info('开始抓取...')
        if img is None:
            bSkip = True
            async with lock:
                failed_urls.append([url, i, j])
        else:
            with open(f'{output_path}/{i}/{j}.png', "wb") as f:
                f.write(img)
    except:
        # await lock.acquire()
        # failed_urls.append([url, i, j])
        # lock.release()
        async with lock:
            failed_urls.append([url, i, j])
        if not bSkip:
            log.error('url:{} error:{}'.format(url, traceback.format_exc()))


def get_lod(lods, level):
    for lod in lods:
        if lod['level'] == level:
            return lod


if __name__ == '__main__':
    main()
