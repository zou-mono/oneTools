import time
import aiohttp
import asyncio

import requests

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

api_token = ''
subscription_token = ''

# 定义请求头
reqheaders = {
    'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36 Edg/100.0.1185.39',
    # 'Content-Type': 'application/x-www-form-urlencoded',
    'Connection': 'keep-alive',
    'Pragma': 'no-cache'}


log = Log(__name__)
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
def main(url, level, x0, y0, xmin, xmax, ymin, ymax, resolution, tile_size, api_token, subscription_token, output_path):
    crawl_tilemap(url, level, x0, y0, xmin, xmax, ymin, ymax, resolution, tile_size, api_token, subscription_token, output_path)


def crawl_tilemap(url, level, x0, y0, xmin, xmax, ymin, ymax, resolution, tile_size,
                  _api_token, _subscription_token, output_path, logClass=None):
    """crawler program for tilemap data in http://suplicmap.pnr.sz."""
    start = time.time()

    global log
    if logClass is not None:
        log = logClass

    dead_link = 0

    if url[-1] == "/":
        url = url[:-1]

    try:
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

        if _subscription_token != '':
            global reqheaders
            reqheaders['X-OPENAPI-SubscriptionToken'] = _subscription_token

        if _api_token != '':
            global api_token
            api_token = _api_token

        log.info('\n开始使用协程抓取{}, 行数：{}, 列数:{}...'.format(url, max_col - min_col + 1, max_row - min_row + 1))
        # for i in range(min_row, max_row):
        #     for j in range(min_col, max_col):
        #         tile_url = f'{url}/tile/{level}/{i}/{j}'
        #         output_img(tile_url, level_path, i, j)

        tasks = []
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)
        # loop = asyncio.get_event_loop()
        total_count = (max_row - min_row) * (max_col - min_col)
        iprogress = 0
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
                    # log.info("{:.0%}".format(iloop / total_count))
                    if int(iloop * 100 / total_count) != iprogress:
                        log.info("{}%已处理完成...".format(int(iloop * 100 / total_count)))
                        iprogress = int(iloop * 100 / total_count)
                else:
                    tasks.append(asyncio.ensure_future(output_img_asyc(tile_url, output_path, i, j)))

        if len(tasks) > 0:
            loop.run_until_complete(asyncio.wait(tasks))
        loop.close()
        log.info('协程抓取完成.')

        failed_count = len(failed_urls)
        if failed_count > 0:
            log.info('开始用协程重新抓取失败的url, 总计{}条...'.format(str(failed_count)))
            # 比较前后两次抓取成功的数量，如果等于0，则说明协程途径行不通，考虑单线程抓取
            time.sleep(1)

            start_failed_count = failed_count
            delta_count = failed_count
            tasks = []
            iloop = total_count - len(failed_urls)
            loop = asyncio.ProactorEventLoop()
            asyncio.set_event_loop(loop)

            while len(failed_urls) > 0 and delta_count > 0:
                iloop += 1

                furl = failed_urls.pop()
                if len(tasks) >= coroutine_num:
                    tasks.append(asyncio.ensure_future(output_img_asyc(furl[0], output_path, furl[1], furl[2])))
                    loop.run_until_complete(asyncio.wait(tasks))
                    tasks = []
                    if int(iloop * 100 / total_count) != iprogress:
                        log.info("{}%...".format(int(iloop * 100 / total_count)))
                        iprogress = int(iloop * 100 / total_count)
                    # log.info("{:.0%}".format(iloop / total_count))
                    delta_count = start_failed_count - len(failed_urls)
                    start_failed_count = len(failed_urls)
                    iloop = total_count - len(failed_urls)
                    continue
                else:
                    tasks.append(asyncio.ensure_future(output_img_asyc(furl[0], output_path, furl[1], furl[2])))

            if len(tasks) > 0:
                loop.run_until_complete(asyncio.wait(tasks))
            loop.close()

            if len(failed_urls) > 0.1 * total_count:
                log.error("抓取失败的url数量太多，请检查网络状态并重新抓取.")
                if lock.locked():
                    lock.release()
                return False

            log.info('开始用单线程抓取失败的url...')
            while len(failed_urls) > 0:
                furl = failed_urls.pop()
                if not output_img2(furl[0], output_path, furl[1], furl[2]):
                    log.debug('url:{} error:{}'.format(furl[0], traceback.format_exc()))
                    dead_link += 1

        end = time.time()
        if lock.locked():
            lock.release()
        # log.info('爬取瓦片任务完成！瓦片存储至{}.'.format(output_path))
        log.info('爬取瓦片任务完成！总共耗时:{}秒. 死链接数目为:{}. 瓦片存储至{}.'.format("{:.2f} \n".format(end - start), dead_link, output_path))
        return True

    except:
        log.error("抓取失败，请检查参数！{}".format(traceback.format_exc()))
        return False

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


def get_tile(url, reqheaders=None):
    trytime = 0
    status_code = -10000
    while trytime < try_num:
        try:
            # req = urllib.request.Request(url=url)
            # r = urllib.request.urlopen(req)
            # respData = r.read()
            req = requests.get(url, headers=reqheaders)
            status_code = req.status_code
            respData = req.content
            if status_code == 200 or status_code == 404:
                return respData, status_code
            else:
                raise Exception("传回数据为空")
        except:
            # log.debug('{}请求失败！重新尝试...'.format(url))
            trytime += 1

        time.sleep(0.2)
        continue
    return None, status_code


def output_img(url, output_path, i, j):
    try:
        img = get_tile(url)
        if img is None:
            failed_urls.append([url, i, j])
            return False
        else:
            with open(f'{output_path}/{i}/{j}.png', "wb") as f:
                f.write(img)
            return True
    except:
        failed_urls.append([url, i, j])
        log.error('url:{} error:{}'.format(url, traceback.format_exc()))
        return False


def output_img2(url, output_path, i, j):
    try:
        img, status_code = get_tile(url)
        if img is None and status_code != 404:
            return False
        elif img is not None and status_code == 200:
            with open(f'{output_path}/{i}/{j}.png', "wb") as f:
                f.write(img)
            return True
        elif status_code == 404:
            return True
        else:
            return False
    except:
        return False

async def get_tile_async(url, output_path, i, j):
    status_code = -10000
    async with aiohttp.ClientSession() as session:
        try:
            respData, status_code = await send_http(session, method="get", headers=reqheaders,
                                                   respond_Type="content", read_timeout=10, url=url, retries=0)
            # response = await session.post(url, data=data, headers=reqheaders)
            if len(respData) > 0:
                return respData, 200, url, output_path, i, j
            else:
                # return None, status_code, url, output_path, i, j
                raise Exception("传回数据为空")
        except:
            # log.error('url:{} error:{}'.format(url, traceback.format_exc()))
            return None, status_code, url, output_path, i, j


async def output_img_asyc(url, output_path, i, j):
    bSkip = False
    try:
        img, status_code, url, output_path, i, j = await get_tile_async(url, output_path, i, j)
        # log.info('任务载入完成.')
        # log.info('开始抓取...')
        if img is None and status_code != 404:
            bSkip = True
            async with lock:
                failed_urls.append([url, i, j])
        elif img is not None and status_code == 200:
            with open(f'{output_path}/{i}/{j}.png', "wb") as f:
                f.write(img)
    except:
        # await lock.acquire()
        # failed_urls.append([url, i, j])
        # lock.release()
        async with lock:
            failed_urls.append([url, i, j])
        # if not bSkip:
        #     log.debug('url:{} error:{}'.format(url, traceback.format_exc()))


def get_lod(lods, level):
    for lod in lods:
        if lod['level'] == level:
            return lod


if __name__ == '__main__':
    main()
