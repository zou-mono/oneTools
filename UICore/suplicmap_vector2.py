# -*- coding: utf-8 -*-

import json
import time
from UICore.log4p import Log
import urllib.request, urllib.parse
import os
from osgeo import ogr
import osgeo.osr as osr
from osgeo import gdal
import click
import traceback
import re
import aiohttp
import asyncio
from UICore.asyncRequest import send_http
from UICore.common import urlEncodeToFileName, check_layer_name
import encodings.idna

try_num = 5
num_return = 1000  # 返回条数
concurrence_num = 10  # 协程并发次数
# max_return = 1000000
log = Log(__file__)
failed_urls = []
lock = asyncio.Lock()

epsg = 2435
dateLst = []
OID_NAME = "OBJECTID"  # FID字段名称
m_fields = []

# 定义请求头
reqheaders = {
    'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36 Edg/81.0.416.72',
    'Content-Type': 'application/x-www-form-urlencoded',
    # 'Host': 'suplicmap.pnr.sz',
    'Pragma': 'no-cache'}


@click.command()
@click.option('--url', '-u',
              help='Input url. For example, http://suplicmap.pnr.sz/dynaszmap_3/rest/services/SZMAP_DLJT_GKDL/MapServer/10/',
              required=True)
@click.option(
    '--layer-name', '-n',
    help='Output layer name, which is shown in geodatabase. For example, 道路面',
    required=False)
@click.option(
    '--sr', '-s',
    help='srs EPSG ID. For example, 2435',
    type=int,
    default=2435,
    required=False)
@click.option(
    '--loop-pos', '-l',
    help='Start loop position, -1 means from the first ID to the end ID.',
    type=int,
    default=-1,
    required=False)
@click.option(
    '--output-path', '-o',
    help='Output file geodatabase, need the full path. For example, res/data.gdb',
    required=True)
def main(url, layer_name, sr, loop_pos, output_path):
    """crawler program for vector data in http://suplicmap.pnr.sz."""
    url_lst = url.split(r'/')
    layer_order = url_lst[-1]
    service_name = url_lst[-1]
    crawl_vector(url, service_name, layer_order, layer_name, output_path, sr, loop_pos)


def crawl_vector(url, service_name, layer_order, layer_name, output_path, sr, loop_pos=-1):
    start = time.time()

    global epsg
    epsg = sr

    if url[-1] == r"/":
        query_url = url + "query"
        url_json = url[:-1] + "?f=pjson"
    else:
        query_url = url + "/query"
        url_json = url + "?f=pjson"

    log.info("\n开始创建文件数据库...")

    gdb, out_layer, OID = createFileGDB(output_path, layer_name, url_json, service_name, layer_order)

    global OID_NAME
    OID_NAME = OID

    if out_layer is None or gdb is None:
        return False, '创建数据库失败！\n'

    log.info("文件数据库创建成功, 位置为{}, 图层名称为{}".format(os.path.abspath(output_path), out_layer.GetName()))

    log.info(f'开始使用协程抓取服务{service_name}的第{layer_order}个图层...')

    looplst, OID = getIds(query_url, loop_pos)

    if OID != OID_NAME:
        OID_NAME = OID
        log.warning('OID字段不一致.')

    if looplst is None:
        return False, '要素为空！'

    try:
        tasks = []
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)

        iloop = 0
        for i in range(0, len(looplst) - 1):
            line1 = looplst[i]
            line2 = looplst[i + 1]
            query_clause = f'{OID_NAME} >= {line1} and {OID_NAME} < {line2}'
            # query_clause = f'{OID_NAME} >= 0'

            if len(tasks) >= concurrence_num:
                tasks.append(asyncio.ensure_future(output_data_async(query_url, query_clause, out_layer, line1, line2)))
                loop.run_until_complete(asyncio.wait(tasks))
                tasks = []
                iloop += 1
                log.debug(iloop)
                continue
            else:
                tasks.append(asyncio.ensure_future(output_data_async(query_url, query_clause, out_layer, line1, line2)))

        if len(tasks) > 0:
            loop.run_until_complete(asyncio.wait(tasks))
        log.info('协程抓取完成.')

        dead_link = 0
        if len(failed_urls) > 0:
            log.info('开始用单线程抓取失败的url...')
            while len(failed_urls) > 0:
                furl = failed_urls.pop()
                if not output_data(furl[0], furl[1], out_layer):
                    for i in range(furl[2], furl[3]):
                        query_clause2 = f'{OID_NAME} = {i}'
                        if not output_data(furl[0], query_clause2, out_layer):
                            log.error('url:{} data:{} error:{}'.format(furl[0], query_clause2, traceback.format_exc()))
                            dead_link += 1
                            continue
    except:
        del gdb
        # log.error(traceback.format_exc())
        return False, traceback.format_exc()

    outdriver = None
    del gdb
    out_layer = None

    if lock.locked():
        lock.release()
    end = time.time()
    if dead_link == 0:
        log.info('成功完成抓取. 总共耗时:{}秒. 数据保存至{}.\n'.format("{:.2f}".format(end-start), output_path))
    else:
        log.info('未成功完成抓取, 死链接数目为:{}. 总共耗时{}秒. 数据存储至{}.\n'.format(dead_link, "{:.2f}".format(end-start), output_path))
    return True, ''


def crawl_vector_batch(url, key, output, paras):
    services = paras[key]['services']
    for service in services:
        if service != "*":
            new_key = url + "_" + str(service)
            sr = paras[new_key]['spatialReference']
            url_lst = url.split(r'/')
            if url_lst[-1] == "":
                service_name = url_lst[-3]
                res_url = url + str(service)
            else:
                service_name = url_lst[-2]
                res_url = url + "/" + str(service)

            layername = paras[new_key]['old_layername']

            if layername == "":
                layername = None

            crawl_vector(res_url, service_name=service_name, layer_order=service, layer_name=layername, output_path=output, sr=sr)


def getIds(query_url, loop_pos):
    # 定义请求头
    reqheaders = {'Content-Type': 'application/x-www-form-urlencoded',
                  # 'Host': 'suplicmap.pnr.sz',
                  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36 Edg/93.0.961.38',
                  'Pragma': 'no-cache'}

    # 定义post的参数
    body_value = {'where': '{}>=0'.format(OID_NAME),
                  'returnIdsOnly': 'true',
                  'f': 'pjson'}

    # 对请求参数进行编码
    data = urllib.parse.urlencode(body_value).encode(encoding='UTF8')
    # 请求不同页面的数据
    trytime = 0
    while trytime < try_num:
        try:
            req = urllib.request.Request(url=query_url, data=data, headers=reqheaders)
            r = urllib.request.urlopen(req)
            respData = r.read().decode('utf-8')
            respData = json.loads(respData)
            ids = respData['objectIds']
            OID = respData['objectIdFieldName']

            if ids is not None:
                ids.sort()
                firstId = ids[0]
                endId = ids[len(ids) - 1]

                if loop_pos > endId:
                    log.error("起始ID大于末尾ID！")
                    return False

                if loop_pos == -1:
                    if firstId == endId:
                        looplst = [endId]
                    else:
                        looplst = list(range(firstId, endId, num_return))
                else:
                    looplst = list(range(loop_pos, endId, num_return))
                if looplst[len(looplst) - 1] != endId + 1:
                    looplst.append(endId + 1)

                return looplst, OID
            else:
                # log.warning("要素为空!")
                return None, None
        except:
            log.error('HTTP请求失败！正在准备重发...')
            trytime += 1

        time.sleep(2)
        continue
    return None, None


def addField(feature, defn, OID_NAME, out_layer):
    FID = -1
    try:
        FID = feature.GetField(OID_NAME)
        ofeature = ogr.Feature(out_layer.GetLayerDefn())
        ofeature.SetGeometry(feature.GetGeometryRef())
        ofeature.SetFID(FID)

        for i in range(defn.GetFieldCount()):
            # if fieldName != "OBJECTID"  and OID_NAME != 'OBJECTID':
            #     ofeature.SetField('OBJECTID_', feature.GetField("OBJECTID"))
            fieldName = defn.GetFieldDefn(i).GetName()
            if fieldName == "OBJECTID" or fieldName == OID_NAME:
                continue

            fieldName = check_layer_name(fieldName)

            try:
                ofeature.SetField(fieldName, feature.GetField(i))
            except:
                log.warning('json中的字段不存在.')

        for dateField in dateLst:
            timeArray = time.localtime(int(feature.GetField(dateField)) / 1000)  # 1970秒数
            otherStyleTime = time.strftime("%Y-%m-%d", timeArray)
            ofeature.SetField(dateField, otherStyleTime)

        out_layer.CreateFeature(ofeature)
        ofeature.Destroy()
    except:
        log.error("错误发生在FID=" + str(FID) + "\n" + traceback.format_exc())


def createFileGDB(output_path, layer_name, url_json, service_name, layer_order):
    try:
        outdriver = ogr.GetDriverByName('FileGDB')
        if os.path.exists(output_path):
            gdb = outdriver.Open(output_path, 1)
            if gdb is not None:
                log.info("文件数据库已存在，在已有数据库基础上创建图层.")
            else:
                gdb = outdriver.CreateDataSource(output_path)
        else:
            gdb = outdriver.CreateDataSource(output_path)

        # 向服务器发送一条请求，获取数据字段信息
        respData = get_json(url_json)
        if respData is None:
            log.error('获取数据字段信息失败,无法创建数据库.')
            return

        geoObjs = json.loads(respData)
        if geoObjs['type'] != 'Feature Layer':
            log.warning('远程数据为非要素图层.')
            # return None, None, ""
        dateLst = parseDateField(geoObjs)  # 获取日期字段
        OID = parseOIDField(geoObjs)
        if OID is None:
            log.error('获取OID字段信息失败,无法创建数据库.')
            return None, None, ""

        GeoType = parseGeoTypeField(geoObjs)
        if GeoType is None:
            log.error('获取Geometry字段信息失败,无法创建数据库.')
            return None, None, ""

        if layer_name is None:
            layer_name = check_layer_name(geoObjs['name'])
        else:
            layer_name = check_layer_name(layer_name)
        layer_alias_name = f'{service_name}#{layer_order}#{layer_name}'

        srs = osr.SpatialReference()
        srs.ImportFromEPSG(epsg)

        # out_layer = gdb.CreateLayer(layer_name, srs=srs, geom_type=temp_layer.GetGeomType(),options=["LAYER_ALIAS=电动"])

        out_layer = gdb.CreateLayer(layer_name, srs=srs, geom_type=GeoType,
                                    options=[f'FEATURE_DATASET={service_name}', f'LAYER_ALIAS={layer_alias_name}'])
        # LayerDefn = out_layer.GetLayerDefn()
        global m_fields
        m_fields = []
        fields = geoObjs['fields']

        i = 0
        for field in fields:
            # fieldDefn = out_layerDefn.GetFieldDefn(i)
            if field['type'] == "esriFieldTypeOID":
                # OID_NAME = check_layer_name(field['name'])
                m_fields.append(field)
                OID = field['name']
                continue
            if field['type'] == "esriFieldTypeGeometry":
                continue

            m_fields.append(field)

            OFTtype = parseTypeField(field['type'])
            new_field = ogr.FieldDefn(check_layer_name(field['name']), OFTtype)

            if OFTtype == ogr.OFTString:
                new_field.SetWidth(field['length'])
            elif OFTtype == ogr.OFTReal:
                new_field.SetWidth(18)
                new_field.SetPrecision(10)

            if 'alias' in field:
                new_field.SetAlternativeName(field['alias'])

            # LayerDefn.AddFieldDefn(new_field)
            out_layer.CreateField(new_field, True)  # true表示会根据字段长度限制进行截短
            i += 1

        # defn = out_layer.GetLayerDefn()
        # for i in range(defn.GetFieldCount()):
        #     fieldName = defn.GetFieldDefn(i).GetName()
        #     fieldTypeCode = defn.GetFieldDefn(i).GetType()
        #     fieldType = defn.GetFieldDefn(i).GetFieldTypeName(fieldTypeCode)
        #     fieldWidth = defn.GetFieldDefn(i).GetWidth()
        #     GetPrecision = defn.GetFieldDefn(i).GetPrecision()

            # log.debug(fieldName + " - " + fieldType + " " + str(fieldWidth) + " " + str(GetPrecision))

        return gdb, out_layer, OID
    except:
        log.error("创建数据库失败.\n" + traceback.format_exc())
        return None, None, ""


def get_json(url):
    # 请求不同页面的数据
    trytime = 0
    while trytime < try_num:
        try:
            req = urllib.request.Request(url=url, headers=reqheaders)
            r = urllib.request.urlopen(req)
            respData = r.read().decode('utf-8')
            res = json.loads(respData)
            if 'error' not in res.keys():
                return respData
        except:
            log.error('HTTP请求失败！正在准备重发...')
            trytime += 1

        time.sleep(2)
        continue


#  Post参数到服务器获取geojson对象
async def get_json_by_query_async(url, query_clause):
    # 定义post的参数
    body_value = {'where': query_clause,
                  'outFields': '*',
                  'outSR': str(epsg),
                  'f': 'json'}

    async with aiohttp.ClientSession() as session:
        try:
            respData = await send_http(session, method="post", respond_Type="content", headers=reqheaders,
                                       data=body_value, read_timeout=60, url=url, retries=0)
            return respData
        except:
            log.error('url:{} data:{} error:{}'.format(url, query_clause, traceback.format_exc()))
            return None


#  Post参数到服务器获取geojson对象
def get_json_by_query(url, query_clause):
    # 定义post的参数
    body_value = {'where': query_clause,
                  'outFields': '*',
                  'outSR': str(epsg),
                  'f': 'json'}

    # 对请求参数进行编码
    data = urllib.parse.urlencode(body_value).encode(encoding='UTF8')
    # 请求不同页面的数据
    trytime = 0
    while trytime < try_num:
        try:
            req = urllib.request.Request(url=url, data=data, headers=reqheaders)
            r = urllib.request.urlopen(req)
            respData = r.read().decode('utf-8')
            return respData
        except:
            log.error('HTTP请求失败！正在准备重发...')
            trytime += 1

        time.sleep(1)
        continue
    return None


async def output_data_async(url, query_clause, out_layer, startID, endID):
    try:
        respData = await get_json_by_query_async(url, query_clause)
        if respData is not None:
            respData = respData.decode('utf-8')
            respData = json.loads(respData)
            if 'fields' not in respData:
                respData['fields'] = m_fields
            esri_json = ogr.GetDriverByName('ESRIJSON')
            # respData = str(respData, encoding='utf-8')
            respData = json.dumps(respData, ensure_ascii=False)
            # if not isinstance(respData, str):
            #     raise Exception("返回数据类型不是str！")
        else:
            raise Exception("返回数据为None！")

        geoObjs = esri_json.Open(respData, 0)
        if geoObjs is not None:
            json_Layer = geoObjs.GetLayer()

            defn = json_Layer.GetLayerDefn()
            for feature in json_Layer:  # 将json要素拷贝到gdb中
                addField(feature, defn, OID_NAME, out_layer)
        else:
            raise Exception("要素为空!")
    except Exception as err:
        await lock.acquire()
        failed_urls.append([url, query_clause, startID, endID])
        lock.release()
        # log.error('url:{} data:{} error:{}'.format(url, query_clause, err))


def output_data(url, query_clause, out_layer):
    try:
        respData = get_json_by_query(url, query_clause)
        respData = respData.decode('utf-8')
        respData = json.loads(respData)
        if 'fields' not in respData:
            respData['fields'] = m_fields
        esri_json = ogr.GetDriverByName('ESRIJSON')
        geoObjs = esri_json.Open(respData, 0)
        if geoObjs is not None:
            json_Layer = geoObjs.GetLayer()

            defn = json_Layer.GetLayerDefn()
            for feature in json_Layer:  # 将json要素拷贝到gdb中
                addField(feature, defn, OID_NAME, out_layer)
            return True
        else:
            return False
    except:
        return False


def parseDateField(fields):
    fields = fields['fields']
    if fields is None:
        return None
    order = 0
    DateFields = []
    for field in fields:
        if field['type'] == "esriFieldTypeDate":
            DateFields.append(field['name'])
        order += 1
    return DateFields


def parseOIDField(fields):
    fields = fields['fields']
    if fields is None:
        return None
    order = 0
    for field in fields:
        if field['type'] == "esriFieldTypeOID":
            return [order, field['name']]
        order += 1
    return None


def parseGeoTypeField(fields):
    GeoType = fields['geometryType']

    if GeoType == "esriGeometryPoint":
        return ogr.wkbPoint
    elif GeoType == "esriGeometryLine":
        return ogr.wkbLineString
    elif GeoType == "esriGeometryPolyline":
        return ogr.wkbMultiLineString
    elif GeoType == "esriGeometryPolygon" or "esriGeometryMultiPatch":
        return ogr.wkbMultiPolygon
    else:
        return None


def parseTypeField(FieldType):
    if FieldType == "esriFieldTypeSmallInteger":
        return ogr.OFTInteger
    elif FieldType == "esriFieldTypeInteger":
        return ogr.OFTInteger
    elif FieldType == "esriFieldTypeSingle":
        return ogr.OFTReal
    elif FieldType == "esriFieldTypeDouble":
        return ogr.OFTReal
    elif FieldType == "esriFieldTypeGUID" or FieldType == "esriFieldTypeGlobalID" or \
            FieldType == "esriFieldTypeXML" or FieldType == "esriFieldTypeString":
        return ogr.OFTString
    elif FieldType == "esriFieldTypeDate":
        return ogr.OFTDateTime
    elif FieldType == "esriFieldTypeBlob":
        return ogr.OFTBinary
    else:
        return None


if __name__ == '__main__':
    ogr.UseExceptions()
    main()
