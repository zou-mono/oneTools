import time
import traceback

import click
import os

from osgeo import ogr, osr, gdal

from UICore.DataFactory import workspaceFactory
from UICore.Gv import DataType, DataType_dict, srs_dict
from UICore.common import launderName, overwrite_cpg_file, helmert_para, is_already_opened_in_write_mode
from UICore.coordTransform_web import gcj02_to_wgs84_acc
from UICore.log4p import Log
from UICore.Gv import SpatialReference

log = Log(__file__)

@click.command()
@click.option(
    '--inpath', '-i',
    help='Input path, also means the workspace of spatial data. For example, d:/res/data/ or d:/res/data.gdb',
    type=str,
    required=True)
@click.option(
    '--inlayer',
    help='input layer name.',
    type=str,
    required=True)
@click.option(
    '--insrs',
    help='Input srs. sz_Local = 2435, gcs_2000 = 4490, pcs_2000 = 4547, pcs_2000_zone = 4526, wgs84 = 4326, bd09 = -1, '
         'gcj02 = -2, gcs_xian80 = 4610, pcs_xian80 = 2383, pcs_xian80_zone = 2363. The in layer\'s srs will be used to the default',
    type=int,
    default='-99',
    required=False)
@click.option(
    '--outpath', '-o',
    help='Input path, also means the workspace of spatial data. For example, d:/res/data/ or d:/res/data.gdb',
    type=str,
    default=-1,
    required=False)
@click.option(
    '--outlayer',
    help='Output layer name, which is shown in the result workspace.',
    type=str,
    required=True)
@click.option(
    '--outsrs',
    help='Output srs. sz_Local = 0, gcs_2000 = 1, pcs_2000 = 2, pcs_2000_zone = 3, wgs84 = 4, bd09 = 5, '
         'gcj02 = 6, gcs_xian80 = 7, pcs_xian80 = 8, pcs_xian80_zone = 9.',
    type=int,
    required=True)
def main(inpath, inlayer, insrs, outpath, outlayer, outsrs):
    """spatial coordinate transformation program"""
    transform(inpath, inlayer, insrs, outpath, outlayer, outsrs)


def transform(inpath, inlayer, insrs, outpath, outlayer, outsrs):
    if inpath[-1] == os.sep:
        inpath = inpath[:-1]
    if outpath[-1] == os.sep:
        outpath = outpath[:-1]

    in_format = get_suffix(inpath)
    in_wks = workspaceFactory().get_factory(in_format)

    if in_wks is None:
        return False

    in_DS = in_wks.openFromFile(inpath)
    in_layer = in_wks.openLayer(inlayer)

    if in_layer is None:
        log.error("输入图层不存在！")
        return False

    srs_ref = in_layer.GetSpatialRef()
    # in_DS.Release()
    in_layer = None

    checked_insrs = check_srs(insrs, srs_ref)
    if checked_insrs == -2435:
        log.error("输入的空间参考在ESPG中不存在!")
        return False
    elif checked_insrs == -4547:
        log.error("不支持输入空间数据的坐标转换!")
        return False

    checked_outsrs = check_srs(outsrs, outlayer)
    if checked_outsrs == -2435:
        log.error("输出的空间参考在ESPG中不存在!")
        return False
    elif checked_outsrs == -4547:
        log.error("不支持输出空间数据的坐标转换!")
        return False

    out_format = get_suffix(outpath)

    tfer = Transformer(in_format, out_format, inpath, inlayer, outpath, outlayer)
    tfer.transform(checked_insrs, checked_outsrs)


def check_srs(srs, srs_ref):
    if srs not in SpatialReference.lst():
        return -4547

    if srs > 0 or srs == -99:
        srs_epsg = get_srs(srs_ref)
        in_srs = osr.SpatialReference()
        if srs_epsg is None:
            try:
                in_srs.ImportFromEPSG(srs)
                return srs
            except:
                return -2435
        else:
            return srs_epsg
    elif srs == -1 or srs == -2:
        return srs
    else:
        return -4547


def get_srs(srs_ref):
    try:
        if srs_ref is not None:
            srs_wkt = osr.SpatialReference(srs_ref.ExportToWkt())
            srs_epsg = srs_wkt.GetAttrValue("AUTHORITY", 1)
            return int(srs_epsg)
        else:
            return None
    except:
        return None


def get_suffix(path):
    suffix = None
    basename = os.path.basename(path)
    if basename.find('.') > 0:
        suffix = basename.split('.')[1]

    if suffix.lower() == 'shp':
        return DataType.shapefile
    elif suffix.lower() == 'geojson':
        return DataType.geojson
    elif suffix.lower() == 'gdb':
        return DataType.fileGDB
    elif suffix.lower() == 'dwg':
        return DataType.cad_dwg
    else:
        return None


class Transformer(object):
    def __init__(self, in_format, out_format, inpath, inlayername, outpath, outlayername):
        self.out_format = out_format
        self.in_format = in_format
        self.in_layername = inlayername
        self.out_layername = outlayername
        self.in_path = inpath
        self.out_path = outpath

        self.lco = []

        if out_format == DataType.shapefile:
            self.lco = ["ENCODING=GBK"]
            self.out = outpath
        elif out_format == DataType.fileGDB:
            self.lco = ["FID=FID"]
            self.out = os.path.join(outpath, outlayername)

        self.in_wks = workspaceFactory().get_factory(self.in_format)
        self.out_wks = workspaceFactory().get_factory(self.out_format)

    def transform(self, srcSRS, dstSRS):
        start = time.time()

        res =None
        if srcSRS == SpatialReference.sz_Local and dstSRS == SpatialReference.pcs_2000:
            res = self.sz_local_to_pcs_2000(self.in_path, self.out_path, self.out_layername, self.out_format)
        elif srcSRS == SpatialReference.pcs_2000 and dstSRS == SpatialReference.sz_Local:
            res = self.pcs_2000_to_sz_local(self.in_path, self.out_path, self.out_layername, self.out_format)
        elif srcSRS == SpatialReference.sz_Local and dstSRS == SpatialReference.gcs_2000:
            res = self.sz_local_to_gcs_2000(srcSRS, dstSRS)
        elif srcSRS == SpatialReference.gcs_2000 and dstSRS == SpatialReference.sz_Local:
            res = self.gcs_2000_to_sz_local(srcSRS, dstSRS)
        elif srcSRS == SpatialReference.sz_Local and dstSRS == SpatialReference.wgs84:
            res = self.sz_local_to_wgs84(srcSRS, dstSRS)
        elif srcSRS == SpatialReference.wgs84 and dstSRS == SpatialReference.sz_Local:
            res = self.wgs84_to_sz_local(srcSRS, dstSRS)
        elif srcSRS == SpatialReference.sz_Local and dstSRS == SpatialReference.pcs_2000_zone:
            res = self.sz_local_to_pcs_2000_zone(self.in_path, self.out_path, self.out_layername, self.out_format)
        elif srcSRS == SpatialReference.pcs_2000_zone and dstSRS == SpatialReference.sz_Local:
            res = self.pcs_2000_zone_to_sz_local()
        elif srcSRS == SpatialReference.wgs84 and dstSRS == SpatialReference.pcs_2000:
            res = self.wgs84_to_pcs_2000()
        elif srcSRS == SpatialReference.pcs_2000 and dstSRS == SpatialReference.wgs84:
            res = self.pcs_2000_to_wgs84()
        elif srcSRS == SpatialReference.wgs84 and dstSRS == SpatialReference.pcs_2000_zone:
            res = self.wgs84_to_pcs_2000_zone()
        elif srcSRS == SpatialReference.pcs_xian80 and dstSRS == SpatialReference.sz_Local:
            res = self.pcs_xian80_to_sz_local(self.in_path, self.out_path, self.out_layername, self.out_format)
        elif srcSRS == SpatialReference.pcs_xian80 and dstSRS == SpatialReference.pcs_2000:
            res = self.pcs_xian80_to_pcs_2000(self.in_path, self.out_path, self.out_layername, self.out_format)
        elif srcSRS == SpatialReference.pcs_xian80 and dstSRS == SpatialReference.gcs_2000:
            res = self.pcs_xian80_to_gcs_2000(srcSRS, dstSRS)
        elif srcSRS == SpatialReference.pcs_xian80 and dstSRS == SpatialReference.pcs_2000_zone:
            res = self.pcs_xian80_to_pcs_2000_zone()
        elif srcSRS == SpatialReference.gcs_xian80 and dstSRS == SpatialReference.sz_Local:
            res = self.gcs_xian80_to_sz_local()
        elif srcSRS == SpatialReference.gcs_xian80 and dstSRS == SpatialReference.pcs_2000:
            res = self.gcs_xian80_to_pcs_2000(self.in_path, self.out_path, self.out_layername, self.out_format)
        elif srcSRS == SpatialReference.gcs_xian80 and dstSRS == SpatialReference.gcs_2000:
            res = self.gcs_xian80_to_gcs_2000()
        elif srcSRS == SpatialReference.pcs_xian80_zone and dstSRS == SpatialReference.sz_Local:
            res = self.pcs_xian80_zone_to_sz_local()
        elif srcSRS == SpatialReference.pcs_xian80_zone and dstSRS == SpatialReference.pcs_2000:
            res = self.pcs_xian80_zone_to_pcs_2000()
        elif srcSRS == SpatialReference.pcs_xian80 and dstSRS == SpatialReference.wgs84:
            res = self.pcs_xian80_to_wgs84(srcSRS, dstSRS)
        elif srcSRS == SpatialReference.pcs_xian80_zone and dstSRS == SpatialReference.gcs_2000:
            res = self.pcs_xian80_zone_to_gcs_2000(srcSRS, dstSRS)
        elif srcSRS == SpatialReference.pcs_xian80_zone and dstSRS == SpatialReference.wgs84:
            res = self.pcs_xian80_zone_to_wgs84(srcSRS, dstSRS)
        elif srcSRS == SpatialReference.gcj02 and dstSRS == SpatialReference.wgs84:
            res = self.gcj02_to_wgs84()
        else:
            log.error("不支持从{}到{}的转换!".format(srs_dict[srcSRS], srs_dict[dstSRS]))
            return False

        if self.out_format == DataType.shapefile:
            out_path = os.path.dirname(self.out_path)
            out_file, suffix = os.path.splitext(os.path.basename(self.out_path))

            overwrite_cpg_file(out_path, out_file, 'GB2312')

        end = time.time()

        if res is not None:
            log.info("坐标转换完成! 共耗时{}秒. 数据存储至{}.".format("{:.2f}".format(end-start), self.out))
        else:
            log.error("坐标转换失败!可能原因：输出图层数据正在被占用导致无法覆盖，请删除后重试！")

    def sz_local_to_pcs_2000(self, inpath, outpath, outlayer, outformat):
        para_sz_to_pcs_2000 = helmert_para(SpatialReference.sz_Local, SpatialReference.pcs_2000)

        in_srs = osr.SpatialReference()
        in_srs.ImportFromEPSG(2435)
        out_srs = osr.SpatialReference()
        out_srs.ImportFromEPSG(4547)

        out_format = DataType_dict[outformat]

        if outformat == DataType.geojson:
            translateOptions = gdal.VectorTranslateOptions(format=out_format, srcSRS=in_srs, dstSRS=out_srs,
                                                           coordinateOperation=para_sz_to_pcs_2000,
                                                           layerName=outlayer)
        else:
            translateOptions = gdal.VectorTranslateOptions(format=out_format, srcSRS=in_srs, dstSRS=out_srs,
                                                           coordinateOperation=para_sz_to_pcs_2000,
                                                           accessMode="overwrite", layerName=outlayer,
                                                           layerCreationOptions=self.lco)

        return gdal.VectorTranslate(outpath, inpath, options=translateOptions)

    def pcs_2000_to_sz_local(self, inpath, outpath, outlayer, outformat):
        # order0 = get_axis_order(in_srs)

        para_pcs_2000_to_sz = helmert_para(SpatialReference.pcs_2000, SpatialReference.sz_Local)

        in_srs = osr.SpatialReference()
        in_srs.ImportFromEPSG(4547)
        out_srs = osr.SpatialReference()
        out_srs.ImportFromEPSG(2435)

        out_format = DataType_dict[outformat]

        if outformat == DataType.geojson:
            translateOptions = gdal.VectorTranslateOptions(format=out_format, srcSRS=in_srs, dstSRS=out_srs,
                                                           coordinateOperation=para_pcs_2000_to_sz,
                                                           layerName=outlayer)
        else:
            translateOptions = gdal.VectorTranslateOptions(format=out_format, srcSRS=in_srs, dstSRS=out_srs,
                                                           coordinateOperation=para_pcs_2000_to_sz,
                                                           accessMode="overwrite", layerName=self.out_layername,
                                                           layerCreationOptions=self.lco)

        return gdal.VectorTranslate(outpath, inpath, options=translateOptions)

    def sz_local_to_gcs_2000(self, srcSRS, dstSRS):
        in_srs = osr.SpatialReference()
        in_srs.ImportFromEPSG(srcSRS)
        out_srs = osr.SpatialReference()
        out_srs.ImportFromEPSG(dstSRS)
        temp_srs = osr.SpatialReference()
        temp_srs.ImportFromEPSG(4547)

        tmp_outpath = os.path.join(os.path.dirname(self.out_path), "temp_layer_4547.geojson")
        tmp_outpath = launderLayerName(tmp_outpath)
        self.sz_local_to_pcs_2000(self.in_path, tmp_outpath, "temp_layer_4547", DataType.geojson)

        out_format = DataType_dict[self.out_format]
        translateOptions = gdal.VectorTranslateOptions(format=out_format, srcSRS=temp_srs, dstSRS=out_srs,
                                                       accessMode="overwrite", layerName=self.out_layername,
                                                       layerCreationOptions=self.lco)
        return gdal.VectorTranslate(self.out_path, tmp_outpath, options=translateOptions)

    def gcs_2000_to_sz_local(self, srcSRS, dstSRS):
        in_srs = osr.SpatialReference()
        in_srs.ImportFromEPSG(srcSRS)
        out_srs = osr.SpatialReference()
        out_srs.ImportFromEPSG(dstSRS)
        temp_srs = osr.SpatialReference()
        temp_srs.ImportFromEPSG(4547)

        translateOptions = gdal.VectorTranslateOptions(format="geojson", srcSRS=in_srs, dstSRS=temp_srs,
                                                       layerName="temp_layer_4547")
        tmp_outpath = os.path.join(os.path.dirname(self.out_path), "temp_layer_4547.geojson")
        tmp_outpath = launderLayerName(tmp_outpath)
        gdal.VectorTranslate(tmp_outpath, self.in_path, options=translateOptions)

        return self.pcs_2000_to_sz_local(tmp_outpath, self.out_path, self.out_format, self.out_layername)

    def sz_local_to_wgs84(self, srcSRS, dstSRS):
        self.sz_local_to_gcs_2000(srcSRS, dstSRS)

    def wgs84_to_sz_local(self, srcSRS, dstSRS):
        self.gcs_2000_to_sz_local(srcSRS, dstSRS)

    def sz_local_to_pcs_2000_zone(self, inpath, outpath, outlayer, outformat):
        in_srs = osr.SpatialReference()
        in_srs.ImportFromEPSG(2435)
        out_srs = osr.SpatialReference()
        out_srs.ImportFromEPSG(4526)
        temp_srs = osr.SpatialReference()
        temp_srs.ImportFromEPSG(4547)

        tmp_outpath = os.path.join(os.path.dirname(outpath), "temp_layer_4547.geojson")
        tmp_outpath = launderLayerName(tmp_outpath)
        self.sz_local_to_pcs_2000(inpath, tmp_outpath, "temp_layer_4547", DataType.geojson)

        out_format = DataType_dict[outformat]
        translateOptions = gdal.VectorTranslateOptions(format=out_format, srcSRS=temp_srs, dstSRS=out_srs,
                                                       accessMode="overwrite", layerName=outlayer,
                                                       layerCreationOptions=self.lco)
        return gdal.VectorTranslate(outpath, tmp_outpath, options=translateOptions)

    def pcs_2000_zone_to_sz_local(self):
        in_srs = osr.SpatialReference()
        in_srs.ImportFromEPSG(4526)
        out_srs = osr.SpatialReference()
        out_srs.ImportFromEPSG(2435)
        temp_srs = osr.SpatialReference()
        temp_srs.ImportFromEPSG(4547)

        translateOptions = gdal.VectorTranslateOptions(format="geojson", srcSRS=in_srs, dstSRS=temp_srs,
                                                       layerName="temp_layer_4547")
        tmp_outpath = os.path.join(os.path.dirname(self.out_path), "temp_layer_4547.geojson")
        tmp_outpath = launderLayerName(tmp_outpath)
        gdal.VectorTranslate(tmp_outpath, self.in_path, options=translateOptions)

        return self.pcs_2000_to_sz_local(tmp_outpath, self.out_path, self.out_format, self.out_layername)

    def wgs84_to_pcs_2000(self):
        in_srs = osr.SpatialReference()
        in_srs.ImportFromEPSG(4490)
        out_srs = osr.SpatialReference()
        out_srs.ImportFromEPSG(4547)

        out_format = DataType_dict[self.out_format]
        translateOptions = gdal.VectorTranslateOptions(format=out_format, srcSRS=in_srs, dstSRS=out_srs,
                                                       accessMode="overwrite", layerName=self.out_layername,
                                                       layerCreationOptions=self.lco)
        return gdal.VectorTranslate(self.out_path, self.in_path, options=translateOptions)

    def pcs_2000_to_wgs84(self):
        in_srs = osr.SpatialReference()
        in_srs.ImportFromEPSG(4547)
        out_srs = osr.SpatialReference()
        out_srs.ImportFromEPSG(4326)

        out_format = DataType_dict[self.out_format]
        translateOptions = gdal.VectorTranslateOptions(format=out_format, srcSRS=in_srs, dstSRS=out_srs,
                                                       accessMode="overwrite", layerName=self.out_layername,
                                                       layerCreationOptions=self.lco)
        return gdal.VectorTranslate(self.out_path, self.in_path, options=translateOptions)

    def wgs84_to_pcs_2000_zone(self):
        in_srs = osr.SpatialReference()
        in_srs.ImportFromEPSG(4490)
        out_srs = osr.SpatialReference()
        out_srs.ImportFromEPSG(4526)

        translateOptions = gdal.VectorTranslateOptions(format=self.out_format, srcSRS=in_srs, dstSRS=out_srs,
                                                       accessMode="overwrite", layerName=self.out_layername,
                                                       layerCreationOptions=self.lco)
        return gdal.VectorTranslate(self.out_path, self.in_path, options=translateOptions)

    def pcs_2000_zone_to_wgs84(self):
        in_srs = osr.SpatialReference()
        in_srs.ImportFromEPSG(4526)
        out_srs = osr.SpatialReference()
        out_srs.ImportFromEPSG(4326)

        translateOptions = gdal.VectorTranslateOptions(format=self.out_format, srcSRS=in_srs, dstSRS=out_srs,
                                                       accessMode="overwrite", layerName=self.out_layername,
                                                       layerCreationOptions=self.lco)
        return gdal.VectorTranslate(self.out_path, self.in_path, options=translateOptions)

    def pcs_xian80_to_sz_local(self, inpath, outpath, outlayer, outformat):
        para_pcs_xian80_to_sz = helmert_para(SpatialReference.pcs_xian80, SpatialReference.sz_Local)

        in_srs = osr.SpatialReference()
        in_srs.ImportFromEPSG(2383)
        out_srs = osr.SpatialReference()
        out_srs.ImportFromEPSG(2435)

        out_format = DataType_dict[outformat]

        if outformat == DataType.geojson:
            translateOptions = gdal.VectorTranslateOptions(format=out_format, srcSRS=in_srs, dstSRS=out_srs,
                                                           coordinateOperation=para_pcs_xian80_to_sz,
                                                           layerName=outlayer)
        else:
            translateOptions = gdal.VectorTranslateOptions(format=out_format, srcSRS=in_srs, dstSRS=out_srs,
                                                           coordinateOperation=para_pcs_xian80_to_sz,
                                                           accessMode="overwrite", layerName=self.out_layername,
                                                           layerCreationOptions=self.lco)

        return gdal.VectorTranslate(outpath, inpath, options=translateOptions)

    def pcs_xian80_to_pcs_2000(self, inpath, outpath, outlayer, outformat):
        in_srs = osr.SpatialReference()
        in_srs.ImportFromEPSG(2383)
        out_srs = osr.SpatialReference()
        out_srs.ImportFromEPSG(4547)
        temp_srs = osr.SpatialReference()
        temp_srs.ImportFromEPSG(2435)

        tmp_outpath = os.path.join(os.path.dirname(self.out_path), "temp_layer_2435.geojson")
        # tmp_outpath = launderLayerName(tmp_outpath)
        self.pcs_xian80_to_sz_local(inpath, tmp_outpath, "temp_layer_2435", DataType.geojson)
        self.sz_local_to_pcs_2000(tmp_outpath, outpath, outlayer, outformat)

    def pcs_xian80_to_gcs_2000(self, srcSRS, dstSRS):
        in_srs = osr.SpatialReference()
        in_srs.ImportFromEPSG(srcSRS)
        out_srs = osr.SpatialReference()
        out_srs.ImportFromEPSG(dstSRS)
        temp_srs = osr.SpatialReference()
        temp_srs.ImportFromEPSG(4547)

        tmp_outpath = os.path.join(os.path.dirname(self.out_path), "temp_layer_4547.geojson")
        self.pcs_xian80_to_pcs_2000(self.in_path, tmp_outpath, "temp_layer_4547", DataType.geojson)

        out_format = DataType_dict[self.out_format]
        translateOptions = gdal.VectorTranslateOptions(format=out_format, srcSRS=temp_srs, dstSRS=out_srs,
                                                       accessMode="overwrite", layerName=self.out_layername,
                                                       layerCreationOptions=self.lco)
        return gdal.VectorTranslate(self.out_path, tmp_outpath, options=translateOptions)

    def pcs_xian80_to_pcs_2000_zone(self):
        in_srs = osr.SpatialReference()
        in_srs.ImportFromEPSG(2383)
        out_srs = osr.SpatialReference()
        out_srs.ImportFromEPSG(4526)
        temp_srs = osr.SpatialReference()
        temp_srs.ImportFromEPSG(2435)

        tmp_outpath = os.path.join(os.path.dirname(self.out_path), "temp_layer_2435.geojson")
        self.pcs_xian80_to_sz_local(self.in_path, tmp_outpath, "temp_layer_2435", DataType.geojson)
        self.sz_local_to_pcs_2000(tmp_outpath, self.out_path, self.out_layername, self.out_format)

    def gcs_xian80_to_sz_local(self):
        in_srs = osr.SpatialReference()
        in_srs.ImportFromEPSG(4610)
        out_srs = osr.SpatialReference()
        out_srs.ImportFromEPSG(2435)
        temp_srs = osr.SpatialReference()
        temp_srs.ImportFromEPSG(2383)

        tmp_outpath = os.path.join(os.path.dirname(self.out_path), "temp_layer_2383.geojson")
        translateOptions = gdal.VectorTranslateOptions(format="geojson", srcSRS=in_srs, dstSRS=temp_srs,
                                                       layerName="temp_layer_2383")
        gdal.VectorTranslate(tmp_outpath, self.in_path, options=translateOptions)

        self.pcs_xian80_to_sz_local(tmp_outpath, self.out_path, self.out_layername, self.out_format)

    def gcs_xian80_to_pcs_2000(self, inpath, outpath, outlayer, outformat):
        in_srs = osr.SpatialReference()
        in_srs.ImportFromEPSG(4610)
        out_srs = osr.SpatialReference()
        out_srs.ImportFromEPSG(4547)
        temp_srs = osr.SpatialReference()
        temp_srs.ImportFromEPSG(2383)

        tmp_outpath = os.path.join(os.path.dirname(self.out_path), "temp_layer_2383.geojson")
        translateOptions = gdal.VectorTranslateOptions(format="geojson", srcSRS=in_srs, dstSRS=temp_srs,
                                                       layerName="temp_layer_2383")
        gdal.VectorTranslate(tmp_outpath, inpath, options=translateOptions)

        self.pcs_xian80_to_pcs_2000(tmp_outpath, outpath, outlayer, outformat)

    def gcs_xian80_to_gcs_2000(self):
        in_srs = osr.SpatialReference()
        in_srs.ImportFromEPSG(4610)
        out_srs = osr.SpatialReference()
        out_srs.ImportFromEPSG(4490)
        temp_srs = osr.SpatialReference()
        temp_srs.ImportFromEPSG(4547)

        tmp_outpath = os.path.join(os.path.dirname(self.out_path), "temp_layer_4547.geojson")
        self.gcs_xian80_to_pcs_2000(self.in_path, tmp_outpath, self.out_layername, DataType.geojson)

        out_format = DataType_dict[self.out_format]
        translateOptions = gdal.VectorTranslateOptions(format=out_format, srcSRS=temp_srs, dstSRS=out_srs,
                                                       accessMode="overwrite", layerName=self.out_layername,
                                                       layerCreationOptions=self.lco)
        return gdal.VectorTranslate(self.out_path, tmp_outpath, options=translateOptions)

    def pcs_xian80_zone_to_sz_local(self):
        in_srs = osr.SpatialReference()
        in_srs.ImportFromEPSG(2362)
        out_srs = osr.SpatialReference()
        out_srs.ImportFromEPSG(2435)
        temp_srs = osr.SpatialReference()
        temp_srs.ImportFromEPSG(2383)

        tmp_outpath = os.path.join(os.path.dirname(self.out_path), "temp_layer_2383.geojson")
        translateOptions = gdal.VectorTranslateOptions(format="geojson", srcSRS=in_srs, dstSRS=temp_srs,
                                                       layerName="temp_layer_2383")
        gdal.VectorTranslate(tmp_outpath, self.in_path, options=translateOptions)

        self.pcs_xian80_to_sz_local(tmp_outpath, self.out_path, self.out_layername, self.out_format)

    def pcs_xian80_zone_to_pcs_2000(self):
        in_srs = osr.SpatialReference()
        in_srs.ImportFromEPSG(2362)
        out_srs = osr.SpatialReference()
        out_srs.ImportFromEPSG(4547)
        temp_srs = osr.SpatialReference()
        temp_srs.ImportFromEPSG(2383)

        tmp_outpath = os.path.join(os.path.dirname(self.out_path), "temp_layer_2383.geojson")
        translateOptions = gdal.VectorTranslateOptions(format="geojson", srcSRS=in_srs, dstSRS=temp_srs,
                                                       layerName="temp_layer_2383")
        gdal.VectorTranslate(tmp_outpath, self.in_path, options=translateOptions)

        self.pcs_xian80_to_pcs_2000(tmp_outpath, self.out_path, self.out_layername, self.out_format)

    def pcs_xian80_to_wgs84(self, srcSRS, dstSRS):
        self.pcs_xian80_to_gcs_2000(srcSRS, dstSRS)

    def pcs_xian80_zone_to_gcs_2000(self, srcSRS, dstSRS):
        in_srs = osr.SpatialReference()
        in_srs.ImportFromEPSG(srcSRS)
        out_srs = osr.SpatialReference()
        out_srs.ImportFromEPSG(dstSRS)
        temp_srs1 = osr.SpatialReference()
        temp_srs1.ImportFromEPSG(2383)

        tmp_outpath1 = os.path.join(os.path.dirname(self.out_path), "temp_layer_2383.geojson")
        translateOptions = gdal.VectorTranslateOptions(format="geojson", srcSRS=in_srs, dstSRS=temp_srs1,
                                                       layerName="temp_layer_2383")
        gdal.VectorTranslate(tmp_outpath1, self.in_path, options=translateOptions)

        tmp_outpath2 = os.path.join(os.path.dirname(self.out_path), "temp_layer_2383.geojson")
        self.pcs_xian80_to_pcs_2000(tmp_outpath2, tmp_outpath1, self.out_layername, self.out_format)

        temp_srs2 = osr.SpatialReference()
        temp_srs2.ImportFromEPSG(4547)
        out_format = DataType_dict[self.out_format]
        translateOptions = gdal.VectorTranslateOptions(format=out_format, srcSRS=temp_srs2, dstSRS=out_srs,
                                                       accessMode="overwrite", layerName=self.out_layername,
                                                       layerCreationOptions=self.lco)
        return gdal.VectorTranslate(tmp_outpath1, self.in_path, options=translateOptions)

    def pcs_xian80_zone_to_wgs84(self, srcSRS, dstSRS):
        self.pcs_xian80_to_gcs_2000(srcSRS, dstSRS)

    def gcj02_to_wgs84(self):
        self.in_wks.openFromFile(self.in_path)
        in_layer = self.in_wks.openLayer(self.in_layername)

        out_DS = self.out_wks.openFromFile(self.out_path)
        out_path, out_layername = self.out_wks.cloneLayer(in_layer, self.out_path,
                                            self.out_layername, SpatialReference.wgs84, self.out_format)

        if out_layername is not None:
            outDS = self.out_wks.openFromFile(out_path)
            out_layer = outDS.GetLayer(out_layername)
            self.transform_pointwise(in_layer, out_layer, gcj02_to_wgs84_acc)

        return out_layername

    def transform_pointwise(self, in_Layer, out_layer, transform_func):
        icount = 0
        iprop = 1

        total_count = in_Layer.GetFeatureCount()

        for feature in in_Layer:
            geom = feature.GetGeometryRef()

            if geom is None:
                continue

            if geom.GetGeometryName() == "POINT":
                lng, lat = transform_func(geom.GetPoint(0)[0], geom.GetPoint(0)[1])
                point = ogr.Geometry(ogr.wkbPoint)
                point.AddPoint(lng, lat)
                self.addFeature(feature, point, in_Layer, out_layer, icount)

            elif geom.GetGeometryName() == "MULTIPOINT":
                new_multipoint = ogr.Geometry(ogr.wkbMultiPoint)
                for part in geom:
                    lng, lat = transform_func(part.GetX(), part.GetY())
                    new_point = ogr.Geometry(ogr.wkbPoint)
                    new_point.AddPoint(lng, lat)
                    new_multipoint.AddGeometry(new_point)
                self.addFeature(feature, new_multipoint, in_Layer, out_layer, icount)

            elif geom.GetGeometryName() == "POLYGON":
                new_polygon = ogr.Geometry(ogr.wkbPolygon)
                for ring in geom:
                    new_ring = ogr.Geometry(ogr.wkbLinearRing)
                    for i in range(0, ring.GetPointCount()):
                        lng, lat = transform_func(ring.GetPoint(i)[0], ring.GetPoint(i)[1])
                        new_ring.AddPoint(lng, lat)
                    new_polygon.AddGeometry(new_ring)
                self.addFeature(feature, new_polygon, in_Layer, out_layer, icount)

            elif geom.GetGeometryName() == "MULTIPOLYGON":
                new_multiPolygon = ogr.Geometry(ogr.wkbMultiPolygon)
                for part in geom:
                    new_polygon = ogr.Geometry(ogr.wkbPolygon)
                    for ring in part:
                        new_ring = ogr.Geometry(ogr.wkbLinearRing)
                        for i in range(0, ring.GetPointCount()):
                            lng, lat = transform_func(ring.GetPoint(i)[0], ring.GetPoint(i)[1])
                            new_ring.AddPoint(lng, lat)
                        new_polygon.AddGeometry(new_ring)
                    new_multiPolygon.AddGeometry(new_polygon)
                self.addFeature(feature, new_multiPolygon, in_Layer, out_layer, icount)

            elif geom.GetGeometryName() == "LINESTRING":
                new_polyline = ogr.Geometry(ogr.wkbLineString)
                for i in range(0, geom.GetPointCount()):
                    lng, lat = transform_func(geom.GetPoint(i)[0], geom.GetPoint(i)[1])
                    new_polyline.AddPoint(lng, lat)
                self.addFeature(feature, new_polyline, in_Layer, out_layer, icount)

            elif geom.GetGeometryName() == "MULTILINESTRING":
                new_multiPolyline = ogr.Geometry(ogr.wkbMultiLineString)
                for part in geom:
                    new_polyline = ogr.Geometry(ogr.wkbLineString)
                    for i in range(0, part.GetPointCount()):
                        lng, lat = transform_func(part.GetPoint(i)[0], part.GetPoint(i)[1])
                        new_polyline.AddPoint(lng, lat)
                    new_multiPolyline.AddGeometry(new_polyline)
                self.addFeature(feature, new_multiPolyline, in_Layer, out_layer, icount)

            icount = icount + 1
            if int(icount * 100 / total_count) == iprop * 20:
                log.debug("{:.0%}".format(icount / total_count))
                iprop += 1

    def addFeature(self, in_feature, geometry, in_layer, out_layer, icount):
        try:
            defn = in_layer.GetLayerDefn()
            ofeature = ogr.Feature(in_layer.GetLayerDefn())
            ofeature.SetGeometry(geometry)

            for i in range(defn.GetFieldCount()):
                fieldName = defn.GetFieldDefn(i).GetName()
                # print(in_feature.GetField(i))
                ofeature.SetField(fieldName, in_feature.GetField(i))

            out_layer.CreateFeature(ofeature)
            ofeature.Destroy()
        except:
            log.error("错误发生在第{}个要素.\n{}".format(icount, traceback.format_exc()))


def launderLayerName(path):
    if is_already_opened_in_write_mode(path):
        return launderName(path)
    else:
        return path


# 获取axis order，先北后东还是先东后北
def get_axis_order(srs):
    srs_wkt = osr.SpatialReference(srs.ExportToWkt())
    order0 = srs_wkt.GetAttrValue("AXIS", 1)
    return order0


if __name__ == '__main__':
    main()
