import time
import traceback

import click
import os

from osgeo import ogr, osr, gdal

from UICore.DataFactory import workspaceFactory
from UICore.Gv import DataType, DataType_dict, srs_dict
from UICore.common import launderName, overwrite_cpg_file, is_already_opened_in_write_mode, \
    helmert_para_dict, get_suffix
from UICore.coordTransform_web import gcj02_to_wgs84_acc, wgs84_to_gcj02, bd09_to_wgs84_acc, wgs84_to_bd09
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
    coordTransform(inpath, inlayer, insrs, outpath, outlayer, outsrs)


def coordTransform(inpath, inlayer, insrs, outpath, outlayer, outsrs):
    if inpath[-1] == os.sep:
        inpath = inpath[:-1]
    if outpath[-1] == os.sep:
        outpath = outpath[:-1]

    in_format = get_suffix(inpath)
    in_wks = workspaceFactory().get_factory(in_format)

    if in_wks is None:
        return False

    in_wks.openFromFile(inpath)
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

    try:
        tfer = Transformer(in_format, out_format, inpath, inlayer, outpath, outlayer)
        tfer.transform(checked_insrs, checked_outsrs)
        return True, ''
    except:
        return False, traceback.format_exc()


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

    def transform(self, srcSRS, dstSRS):
        start = time.time()

        res = None
        if srcSRS == SpatialReference.sz_Local and dstSRS == SpatialReference.pcs_2000:
            res = self.sz_local_to_pcs_2000()
        elif srcSRS == SpatialReference.pcs_2000 and dstSRS == SpatialReference.sz_Local:
            res = self.pcs_2000_to_sz_local()
        elif srcSRS == SpatialReference.sz_Local and dstSRS == SpatialReference.gcs_2000:
            res = self.sz_local_to_gcs_2000()
        elif srcSRS == SpatialReference.gcs_2000 and dstSRS == SpatialReference.sz_Local:
            res = self.gcs_2000_to_sz_local()
        elif srcSRS == SpatialReference.sz_Local and dstSRS == SpatialReference.wgs84:
            res = self.sz_local_to_wgs84()
        elif srcSRS == SpatialReference.wgs84 and dstSRS == SpatialReference.sz_Local:
            res = self.wgs84_to_sz_local()
        elif srcSRS == SpatialReference.sz_Local and dstSRS == SpatialReference.pcs_2000_zone:
            res = self.sz_local_to_pcs_2000_zone(self.in_path, self.out_path, self.out_layername, self.out_format)
        elif srcSRS == SpatialReference.pcs_2000_zone and dstSRS == SpatialReference.sz_Local:
            res = self.pcs_2000_zone_to_sz_local()
        elif srcSRS == SpatialReference.wgs84 and dstSRS == SpatialReference.pcs_2000:
            res = self.wgs84_to_pcs_2000()
        elif srcSRS == SpatialReference.pcs_2000_zone and dstSRS == SpatialReference.wgs84:
            res = self.pcs_2000_zone_to_wgs84()
        elif srcSRS == SpatialReference.pcs_2000 and dstSRS == SpatialReference.wgs84:
            res = self.pcs_2000_to_wgs84()
        elif srcSRS == SpatialReference.wgs84 and dstSRS == SpatialReference.pcs_2000_zone:
            res = self.wgs84_to_pcs_2000_zone()
        elif srcSRS == SpatialReference.pcs_xian80 and dstSRS == SpatialReference.sz_Local:
            res = self.pcs_xian80_to_sz_local()
        elif srcSRS == SpatialReference.pcs_xian80 and dstSRS == SpatialReference.pcs_2000:
            res = self.pcs_xian80_to_pcs_2000()
        elif srcSRS == SpatialReference.pcs_xian80 and dstSRS == SpatialReference.gcs_2000:
            res = self.pcs_xian80_to_gcs_2000()
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
            res = self.pcs_xian80_to_wgs84()
        elif srcSRS == SpatialReference.pcs_xian80_zone and dstSRS == SpatialReference.gcs_2000:
            res = self.pcs_xian80_zone_to_gcs_2000()
        elif srcSRS == SpatialReference.pcs_xian80_zone and dstSRS == SpatialReference.wgs84:
            res = self.pcs_xian80_zone_to_wgs84()
        elif srcSRS == SpatialReference.gcj02 and dstSRS == SpatialReference.wgs84:
            res = self.gcj02_to_wgs84()
        elif srcSRS == SpatialReference.wgs84 and dstSRS == SpatialReference.gcj02:
            res = self.wgs84_gcj02()
        elif srcSRS == SpatialReference.bd09 and dstSRS == SpatialReference.wgs84:
            res = self.bd09_to_wgs84()
        elif srcSRS == SpatialReference.wgs84 and dstSRS == SpatialReference.bd09:
            res = self.wgs84_to_bd09()
        elif srcSRS == SpatialReference.gcj02 and dstSRS == SpatialReference.sz_Local:
            res = self.gcj02_to_sz_local()
        elif srcSRS == SpatialReference.bd09 and dstSRS == SpatialReference.sz_Local:
            res = self.bd09_to_sz_local()
        elif srcSRS == SpatialReference.gcj02 and dstSRS == SpatialReference.pcs_2000:
            res = self.gcj02_to_pcs_2000()
        elif srcSRS == SpatialReference.bd09 and dstSRS == SpatialReference.pcs_2000:
            res = self.bd09_to_pcs_2000()
        else:
            log.error("不支持从{}到{}的转换!".format(srs_dict[srcSRS], srs_dict[dstSRS]))
            return False

        end = time.time()

        if res is not None:
            if self.out_format == DataType.shapefile:
                out_path = os.path.dirname(self.out_path)
                out_file, suffix = os.path.splitext(os.path.basename(self.out_path))

                overwrite_cpg_file(out_path, out_file, 'GB2312')

            log.info("坐标转换完成! 共耗时{}秒. 输出数据源:{},输出图层名:{}."
                     .format("{:.2f}".format(end-start), res[0], res[1]))
        else:
            log.error("坐标转换失败!可能原因：1.输出图层数据正在被占用导致无法覆盖 2.输入图层字符编码问题")

    # 一次转换
    def transform_direct(self, srcSRS, dstSRS, inpath=None, outpath=None, outlayername=None,
                         outformat=None, layerCreationOptions=None, helmert_para=None):
        in_srs = osr.SpatialReference()
        in_srs.ImportFromEPSG(srcSRS)
        out_srs = osr.SpatialReference()
        out_srs.ImportFromEPSG(dstSRS)

        if inpath is None: inpath = self.in_path
        if outpath is None: outpath = self.out_path
        if outlayername is None: outlayername = self.out_layername
        if outformat is None: outformat = self.out_format
        if layerCreationOptions is None: layerCreationOptions = self.lco

        out_format = DataType_dict[outformat]

        if outformat == DataType.geojson:
            translateOptions = gdal.VectorTranslateOptions(format=out_format, srcSRS=in_srs, dstSRS=out_srs,
                                                           coordinateOperation=helmert_para,
                                                           layerName=outlayername)
        else:
            translateOptions = gdal.VectorTranslateOptions(format=out_format, srcSRS=in_srs, dstSRS=out_srs,
                                                           coordinateOperation=helmert_para,
                                                           accessMode="overwrite", layerName=outlayername,
                                                           layerCreationOptions=layerCreationOptions)

        if gdal.VectorTranslate(outpath, inpath, options=translateOptions):
            return [outpath, outlayername]
        else:
            return None

    # 二次转换
    def transform_bridge(self, srcSRS, midSRS, dstSRS, inpath=None, midpath=None, midlayername=None,
                         outpath=None, outlayername=None, outformat=None,
                         layerCreationOptions=None):
        if inpath is None: inpath = self.in_path
        if outpath is None: outpath = self.out_path
        if outlayername is None: outlayername = self.out_layername
        if outformat is None: outformat = self.out_format
        if layerCreationOptions is None: layerCreationOptions = self.lco

        if midpath is None:
            midpath = os.path.join(os.path.dirname(self.out_path), midlayername)
        midpath = launderLayerName(midpath)

        helmert_para = helmert_para_dict(srcSRS, midSRS)

        [out_path, out_layername] = self.transform_direct(srcSRS, midSRS, inpath=inpath, outpath=midpath,
                                                        outlayername=midlayername, outformat=DataType.geojson,
                                                        helmert_para=helmert_para,
                                                        layerCreationOptions=layerCreationOptions)

        if out_path is None or out_layername is None:
            return None

        helmert_para = helmert_para_dict(midSRS, dstSRS)

        [out_path, out_layername] = self.transform_direct(midSRS, dstSRS, midpath, outpath, outlayername, outformat,
                                                        helmert_para=helmert_para)

        return [out_path, out_layername] if out_path is not None and out_layername is not None else None

    # 关键转换，需要参数
    def sz_local_to_pcs_2000(self, inpath=None, outpath=None, outlayername=None, outformat=None):
        para_sz_to_pcs_2000 = helmert_para_dict(SpatialReference.sz_Local, SpatialReference.pcs_2000)
        [out_path, out_layername] = self.transform_direct(2435, 4547, inpath, outpath,
                                                      outlayername, outformat, helmert_para=para_sz_to_pcs_2000)

        return [out_path, out_layername] if out_path is not None and out_layername is not None else None

    # 关键转换，需要参数
    def pcs_2000_to_sz_local(self, inpath=None, outpath=None, outlayername=None, outformat=None):
        para_pcs_2000_to_sz = helmert_para_dict(SpatialReference.pcs_2000, SpatialReference.sz_Local)

        [out_path, out_layername] = self.transform_direct(4547, 2435, inpath, outpath,
                                                        outlayername, outformat, helmert_para=para_pcs_2000_to_sz)

        return [out_path, out_layername] if out_path is not None and out_layername is not None else None

    def sz_local_to_gcs_2000(self, inpath=None, outpath=None, outlayername=None, outformat=None):
        # para_sz_to_pcs_2000 = helmert_para(SpatialReference.sz_Local, SpatialReference.pcs_2000)
        # [out_path, out_layername] = self.sz_local_to_pcs_2000(inpath, outpath=outpath,
        #                                                       outlayername="temp_layer_4547.geojson", outformat=DataType.geojson)
        #
        [out_path, out_layername] = self.transform_bridge(2435, 4547, 4490, midlayername="temp_layer_4547.geojson",
                                                        inpath=inpath, outpath=outpath, outlayername=outlayername,
                                                        outformat=outformat)

        return [out_path, out_layername] if out_path is not None and out_layername is not None else None

    def gcs_2000_to_sz_local(self, inpath=None, outpath=None, outlayername=None, outformat=None):
        [out_path, out_layername] = self.transform_bridge(4490, 4547, 2435, midlayername="temp_layer_4547.geojson",
                                                        inpath=inpath, outpath=outpath, outlayername=outlayername,
                                                        outformat=outformat)

        return [out_path, out_layername] if out_path is not None and out_layername is not None else None

    def sz_local_to_wgs84(self, inpath=None, outpath=None, outlayername=None, outformat=None):
        [out_path, out_layername] = self.transform_bridge(2435, 4547, 4326, midlayername="temp_layer_4547.geojson",
                                                        inpath=inpath, outpath=outpath, outlayername=outlayername,
                                                        outformat=outformat)

        return [out_path, out_layername] if out_path is not None and out_layername is not None else None

    def wgs84_to_sz_local(self, inpath=None, outpath=None, outlayername=None, outformat=None):
        [out_path, out_layername] = self.transform_bridge(4326, 4547, 2435, midlayername="temp_layer_4547.geojson",
                                                        inpath=inpath, outpath=outpath, outlayername=outlayername,
                                                        outformat=outformat)

        return [out_path, out_layername] if out_path is not None and out_layername is not None else None

    def sz_local_to_pcs_2000_zone(self, inpath=None, outpath=None, outlayername=None, outformat=None):
        [out_path, out_layername] = self.transform_bridge(2435, 4547, 4526, midlayername="temp_layer_4547.geojson",
                                                        inpath=inpath, outpath=outpath, outlayername=outlayername,
                                                        outformat=outformat)

        return [out_path, out_layername] if out_path is not None and out_layername is not None else None

    def pcs_2000_zone_to_sz_local(self, inpath=None, outpath=None, outlayername=None, outformat=None):
        [out_path, out_layername] = self.transform_bridge(4526, 4547, 2435, midlayername="temp_layer_4547.geojson",
                                                        inpath=inpath, outpath=outpath, outlayername=outlayername,
                                                        outformat=outformat)

        return [out_path, out_layername] if out_path is not None and out_layername is not None else None

    def wgs84_to_pcs_2000(self, inpath=None, outpath=None, outlayername=None, outformat=None):
        [out_path, out_layername] = self.transform_direct(4490, 4547, inpath, outpath,
                                                        outlayername, outformat)

        return [out_path, out_layername] if out_path is not None and out_layername is not None else None

    def pcs_2000_to_wgs84(self, inpath=None, outpath=None, outlayername=None, outformat=None):
        [out_path, out_layername] = self.transform_direct(4547, 4326, inpath, outpath,
                                                        outlayername, outformat)

        return [out_path, out_layername] if out_path is not None and out_layername is not None else None

    def wgs84_to_pcs_2000_zone(self, inpath=None, outpath=None, outlayername=None, outformat=None):
        [out_path, out_layername] = self.transform_direct(4490, 4526, inpath, outpath,
                                                        outlayername, outformat)

        return [out_path, out_layername] if out_path is not None and out_layername is not None else None

    def pcs_2000_zone_to_wgs84(self, inpath=None, outpath=None, outlayername=None, outformat=None):
        [out_path, out_layername] = self.transform_direct(4526, 4326, inpath, outpath,
                                                        outlayername, outformat)

        return [out_path, out_layername] if out_path is not None and out_layername is not None else None

    # 关键转换，需要参数
    def pcs_xian80_to_sz_local(self, inpath=None, outpath=None, outlayername=None, outformat=None):
        para_pcs_xian80_to_sz = helmert_para_dict(SpatialReference.pcs_xian80, SpatialReference.sz_Local)
        [out_path, out_layername] = self.transform_direct(2383, 2435, inpath, outpath,
                                                        outlayername, outformat, helmert_para=para_pcs_xian80_to_sz)

        return [out_path, out_layername] if out_path is not None and out_layername is not None else None

    def pcs_xian80_to_pcs_2000(self, inpath=None, outpath=None, outlayername=None, outformat=None):
        [out_path, out_layername] = self.transform_bridge(2383, 2435, 4547, midlayername="temp_layer_2435.geojson",
                                                        inpath=inpath, outpath=outpath, outlayername=outlayername,
                                                        outformat=outformat)

        return [out_path, out_layername] if out_path is not None and out_layername is not None else None

    def pcs_xian80_to_gcs_2000(self, inpath=None, outpath=None, outlayername=None, outformat=None):
        tmp_outpath = os.path.join(os.path.dirname(self.out_path), "temp_layer_4547.geojson")
        [tmp_out_path, tmp_out_layername] = self.pcs_xian80_to_pcs_2000(inpath, tmp_outpath,
                                                                        "temp_layer_4547", DataType.geojson)
        [out_path, out_layername] = self.transform_direct(4547, 4490, tmp_out_path, outpath, outlayername, outformat)

        return [out_path, out_layername] if out_path is not None and out_layername is not None else None

    def pcs_xian80_to_pcs_2000_zone(self, inpath=None, outpath=None, outlayername=None, outformat=None):
        tmp_outpath = os.path.join(os.path.dirname(self.out_path), "temp_layer_2435.geojson")
        [tmp_out_path, tmp_out_layername] = self.pcs_xian80_to_sz_local(inpath, tmp_outpath,
                                                                        "temp_layer_2435", DataType.geojson)
        [out_path, out_layername] = self.sz_local_to_pcs_2000(tmp_out_path, outpath=outpath, outlayername=outlayername,
                                                              outformat=outformat)

        return [out_path, out_layername] if out_path is not None and out_layername is not None else None

    def gcs_xian80_to_sz_local(self, inpath=None, outpath=None, outlayername=None, outformat=None):
        [out_path, out_layername] = self.transform_bridge(4610, 2383, 2435, midlayername="temp_layer_2383.geojson",
                                                          inpath=inpath, outpath=outpath, outlayername=outlayername,
                                                          outformat=outformat)

        return [out_path, out_layername] if out_path is not None and out_layername is not None else None

    def gcs_xian80_to_pcs_2000(self, inpath=None, outpath=None, outlayername=None, outformat=None):
        tmp_outpath = os.path.join(os.path.dirname(self.out_path), "temp_layer_2435.geojson")
        [tmp_out_path, tmp_out_layername] = self.gcs_xian80_to_sz_local(inpath, tmp_outpath,
                                                                        "temp_layer_2435", DataType.geojson)
        [out_path, out_layername] = self.sz_local_to_pcs_2000(tmp_out_path, outpath=outpath, outlayername=outlayername,
                                                              outformat=outformat)

        return [out_path, out_layername] if out_path is not None and out_layername is not None else None

    def gcs_xian80_to_gcs_2000(self, inpath=None, outpath=None, outlayername=None, outformat=None):
        tmp_outpath = os.path.join(os.path.dirname(self.out_path), "temp_layer_4547.geojson")
        [tmp_out_path, tmp_out_layername] = self.gcs_xian80_to_pcs_2000(inpath, tmp_outpath,
                                                                        "temp_layer_4547", DataType.geojson)
        [out_path, out_layername] = self.transform_direct(4547, 4490, tmp_out_path, outpath, outlayername, outformat)

        return [out_path, out_layername] if out_path is not None and out_layername is not None else None

    def pcs_xian80_zone_to_sz_local(self, inpath=None, outpath=None, outlayername=None, outformat=None):
        tmp_outpath = os.path.join(os.path.dirname(self.out_path), "temp_layer_2383.geojson")
        [tmp_out_path, tmp_out_layername] = self.transform_direct(2362, 2383, inpath, outpath=tmp_outpath,
                                                          outlayername="temp_layer_2383", outformat=DataType.geojson)
        [out_path, out_layername] = self.pcs_xian80_to_sz_local(tmp_out_path, outpath=outpath,
                                                                outlayername=outlayername, outformat=outformat)

        return [out_path, out_layername] if out_path is not None and out_layername is not None else None

    def pcs_xian80_zone_to_pcs_2000(self, inpath=None, outpath=None, outlayername=None, outformat=None):
        tmp_outpath = os.path.join(os.path.dirname(self.out_path), "temp_layer_2383.geojson")
        [tmp_out_path, tmp_out_layername] = self.transform_direct(2362, 2383, inpath, outpath=tmp_outpath,
                                                                  outlayername="temp_layer_2383", outformat=DataType.geojson)
        [out_path, out_layername] = self.pcs_xian80_to_pcs_2000(tmp_out_path, outpath=outpath,
                                                                outlayername=outlayername, outformat=outformat)

        return [out_path, out_layername] if out_path is not None and out_layername is not None else None

    def pcs_xian80_to_wgs84(self, inpath=None, outpath=None, outlayername=None, outformat=None):
        tmp_outpath = os.path.join(os.path.dirname(self.out_path), "temp_layer_4547.geojson")
        [tmp_out_path, tmp_out_layername] = self.pcs_xian80_to_pcs_2000(inpath, tmp_outpath,
                                                                        "temp_layer_4547", DataType.geojson)
        [out_path, out_layername] = self.transform_direct(4547, 4326, tmp_out_path, outpath, outlayername, outformat)

        return [out_path, out_layername] if out_path is not None and out_layername is not None else None

    def pcs_xian80_zone_to_gcs_2000(self, inpath=None, outpath=None, outlayername=None, outformat=None):
        tmp_outpath = os.path.join(os.path.dirname(self.out_path), "temp_layer_4547.geojson")
        [tmp_out_path, tmp_out_layername] = self.pcs_xian80_zone_to_pcs_2000(inpath, tmp_outpath,
                                                                             "temp_layer_4547", DataType.geojson)
        [out_path, out_layername] = self.transform_direct(4547, 4490, tmp_out_path, outpath, outlayername, outformat)

        return [out_path, out_layername] if out_path is not None and out_layername is not None else None

    def pcs_xian80_zone_to_wgs84(self, inpath=None, outpath=None, outlayername=None, outformat=None):
        tmp_outpath = os.path.join(os.path.dirname(self.out_path), "temp_layer_4547.geojson")
        [tmp_out_path, tmp_out_layername] = self.pcs_xian80_zone_to_pcs_2000(inpath, tmp_outpath,
                                                                             "temp_layer_4547", DataType.geojson)
        [out_path, out_layername] = self.transform_direct(4547, 4326, tmp_out_path, outpath, outlayername, outformat)

        return [out_path, out_layername] if out_path is not None and out_layername is not None else None

    def gcj02_to_wgs84(self):
        return self.run_transform_pointwise(SpatialReference.wgs84, gcj02_to_wgs84_acc)

    def wgs84_gcj02(self):
        return self.run_transform_pointwise(SpatialReference.wgs84, wgs84_to_gcj02)

    def bd09_to_wgs84(self):
        return self.run_transform_pointwise(SpatialReference.wgs84, bd09_to_wgs84_acc)

    def wgs84_to_bd09(self):
        return self.run_transform_pointwise(SpatialReference.wgs84, wgs84_to_bd09)

    def gcj02_to_sz_local(self):
        tmp_outpath = os.path.join(os.path.dirname(self.out_path), "temp_layer_4326.geojson")
        tmp_path, tmp_layername = self.run_transform_pointwise(outpath=tmp_outpath, outlayername="temp_layer_4326.geojson",
                                     outSRS=SpatialReference.wgs84, outformat=DataType.geojson,
                                     transform_func=gcj02_to_wgs84_acc)
        res = self.wgs84_to_sz_local(inpath=tmp_path, outpath=self.out_path,
                                     outlayername=self.out_layername, outformat=self.out_format)

        return [self.out_path, self.out_layername] if res else None

    def bd09_to_sz_local(self):
        tmp_outpath = os.path.join(os.path.dirname(self.out_path), "temp_layer_4326.geojson")
        tmp_path, tmp_layername = self.run_transform_pointwise(outpath=tmp_outpath, outlayername="temp_layer_4326.geojson",
                                                               outSRS=SpatialReference.wgs84, outformat=DataType.geojson,
                                                               transform_func=bd09_to_wgs84_acc)
        res = self.wgs84_to_sz_local(inpath=tmp_path, outpath=self.out_path,
                                     outlayername=self.out_layername, outformat=self.out_format)

        return [self.out_path, self.out_layername] if res else None

    def gcj02_to_pcs_2000(self):
        tmp_outpath = os.path.join(os.path.dirname(self.out_path), "temp_layer_4326.geojson")
        tmp_path, tmp_layername = self.run_transform_pointwise(outpath=tmp_outpath, outlayername="temp_layer_4326.geojson",
                                                               outSRS=SpatialReference.wgs84, outformat=DataType.geojson,
                                                               transform_func=gcj02_to_wgs84_acc)
        res = self.wgs84_to_pcs_2000(inpath=tmp_path, outpath=self.out_path, outlayername=self.out_layername,
                                     outformat=self.out_format)

        return [self.out_path, self.out_layername] if res else None

    def bd09_to_pcs_2000(self):
        tmp_outpath = os.path.join(os.path.dirname(self.out_path), "temp_layer_4326.geojson")
        tmp_path, tmp_layername = self.run_transform_pointwise(outpath=tmp_outpath, outlayername="temp_layer_4326.geojson",
                                                               outSRS=SpatialReference.wgs84, outformat=DataType.geojson,
                                                               transform_func=bd09_to_wgs84_acc)
        res = self.wgs84_to_pcs_2000(inpath=tmp_path, outpath=self.out_path, outlayername=self.out_layername,
                                     outformat=self.out_format)

        return [self.out_path, self.out_layername] if res else None

    def run_transform_pointwise(self, outSRS, transform_func, inpath=None, inlayername=None,
                                outpath=None, outlayername=None, outformat=None):
        if inpath is None: inpath = self.in_path
        if inlayername is None: inlayername = self.in_layername
        if outpath is None: outpath = self.out_path
        if outlayername is None: outlayername = self.out_layername
        if outSRS is None: return None
        if outformat is None: outformat = self.out_format
        if transform_func is None: return None

        res = False
        self.in_wks.openFromFile(inpath)
        in_layer = self.in_wks.openLayer(inlayername)

        # out_DS = out_wks.openFromFile(self.out_path)
        out_wks = workspaceFactory().get_factory(outformat)
        out_path, out_layername = out_wks.cloneLayer(in_layer, outpath,
                                                          outlayername, outSRS, outformat)

        if out_path is not None:
            outDS = out_wks.openFromFile(out_path)
            out_layer = outDS.GetLayer(out_layername)
            res = self.transform_pointwise(in_layer, out_layer, transform_func)

        if res:
            return out_path, out_layername
        else:
            return None

    def transform_pointwise(self, in_Layer, out_layer, transform_func):
        icount = 0
        iprop = 1
        res = False

        total_count = in_Layer.GetFeatureCount()

        for feature in in_Layer:
            geom = feature.GetGeometryRef()

            if geom is None:
                continue

            if geom.GetGeometryName() == "POINT":
                lng, lat = transform_func(geom.GetPoint(0)[0], geom.GetPoint(0)[1])
                point = ogr.Geometry(ogr.wkbPoint)
                point.AddPoint(lng, lat)
                res = self.addFeature(feature, point, in_Layer, out_layer, icount)

            elif geom.GetGeometryName() == "MULTIPOINT":
                new_multipoint = ogr.Geometry(ogr.wkbMultiPoint)
                for part in geom:
                    lng, lat = transform_func(part.GetX(), part.GetY())
                    new_point = ogr.Geometry(ogr.wkbPoint)
                    new_point.AddPoint(lng, lat)
                    new_multipoint.AddGeometry(new_point)
                res = self.addFeature(feature, new_multipoint, in_Layer, out_layer, icount)

            elif geom.GetGeometryName() == "POLYGON":
                new_polygon = ogr.Geometry(ogr.wkbPolygon)
                for ring in geom:
                    new_ring = ogr.Geometry(ogr.wkbLinearRing)
                    for i in range(0, ring.GetPointCount()):
                        lng, lat = transform_func(ring.GetPoint(i)[0], ring.GetPoint(i)[1])
                        new_ring.AddPoint(lng, lat)
                    new_polygon.AddGeometry(new_ring)
                res = self.addFeature(feature, new_polygon, in_Layer, out_layer, icount)

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
                res = self.addFeature(feature, new_multiPolygon, in_Layer, out_layer, icount)

            elif geom.GetGeometryName() == "LINESTRING":
                new_polyline = ogr.Geometry(ogr.wkbLineString)
                for i in range(0, geom.GetPointCount()):
                    lng, lat = transform_func(geom.GetPoint(i)[0], geom.GetPoint(i)[1])
                    new_polyline.AddPoint(lng, lat)
                res = self.addFeature(feature, new_polyline, in_Layer, out_layer, icount)

            elif geom.GetGeometryName() == "MULTILINESTRING":
                new_multiPolyline = ogr.Geometry(ogr.wkbMultiLineString)
                for part in geom:
                    new_polyline = ogr.Geometry(ogr.wkbLineString)
                    for i in range(0, part.GetPointCount()):
                        lng, lat = transform_func(part.GetPoint(i)[0], part.GetPoint(i)[1])
                        new_polyline.AddPoint(lng, lat)
                    new_multiPolyline.AddGeometry(new_polyline)
                res = self.addFeature(feature, new_multiPolyline, in_Layer, out_layer, icount)

            if res < 0:
                return False

            icount = icount + 1
            if int(icount * 100 / total_count) == iprop * 20:
                log.debug("{:.0%}".format(icount / total_count))
                iprop += 1

        return True

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
            return 1
        except UnicodeEncodeError:
            log.error("错误发生在第{}个要素.\n{}".format(icount, "字符编码无法转换，请检查输入文件的字段！"))
            return -1
        except RuntimeError:
            log.error("错误发生在第{}个要素.\n{}".format(icount, "无法拷贝属性值"))
            return -2
        except:
            log.error("错误发生在第{}个要素.\n{}".format(icount, traceback.format_exc()))
            return -10000


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
