import time

import click
import os

from osgeo import ogr, osr, gdal

from UICore.DataFactory import workspaceFactory
from UICore.Gv import DataType, DataType_dict
from UICore.common import launderName, overwrite_cpg_file, helmert_para
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
    default = '-1',
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

    if inpath[-1] == os.sep:
        inpath = inpath[:-1]
    if outpath[-1] == os.sep:
        outpath = outpath[:-1]

    in_format = get_suffix(inpath)
    in_wks = workspaceFactory().get_factory(in_format)

    if in_wks is None:
        return False
    # in_dataset = in_wks.openFromFile(inpath)
    in_layer = in_wks.openLayer(inlayer)

    if insrs > 0:
        srs_epsg = get_srs(in_layer)
        in_srs = osr.SpatialReference()
        if srs_epsg is not None:
            in_srs.ImportFromEPSG(srs_epsg)
        else:
            try:
                in_srs.ImportFromEPSG(insrs)
            except:
                log.error("指定空间参考在ESPG中不存在!")
                return False
    elif insrs == -1 or insrs == -2:
        pass
    else:
        log.error("不支持输入空间数据的坐标转换!")
        return False

    out_srs = osr.SpatialReference()
    out_srs.ImportFromEPSG(outsrs)

    out_format = get_suffix(outpath)

    tfer = Transformer(out_format, inpath, outpath, outlayer)
    tfer.transform(insrs, outsrs, in_srs, out_srs)

    print("ok")


def get_srs(layer):
    try:
        srs = layer.GetSpatialRef()
        if srs is not None:
            srs_wkt = osr.SpatialReference(srs.ExportToWkt())
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
    def __init__(self, out_format, inpath, outpath, outlayername):
        self.out_format = out_format
        self.lco = []

        if out_format == DataType.shapefile:
            self.lco = ["ENCODING=GBK"]
            self.out = outpath
        elif out_format == DataType.fileGDB:
            self.lco = ["FID=FID"]
            self.out = os.path.join(outpath, outlayername)

        self.inpath = inpath
        self.outpath = outpath
        self.outlayername = outlayername

    def transform(self, srcSRS, dstSRS, in_srs, out_srs):
        start = time.time()

        if srcSRS == SpatialReference.sz_Local and dstSRS == SpatialReference.pcs_2000:
            self.sz_local_to_pcs_2000(in_srs, out_srs)
        elif srcSRS == SpatialReference.pcs_2000 and dstSRS == SpatialReference.sz_Local:
            self.pcs_2000_to_sz_local(in_srs, out_srs)
        elif srcSRS == SpatialReference.sz_Local and dstSRS == SpatialReference.gcs_2000:
            self.sz_local_to_gcs_2000(in_srs, out_srs)
        elif srcSRS == SpatialReference.gcs_2000 and dstSRS == SpatialReference.sz_Local:
            self.gcs_2000_to_sz_local(in_srs, out_srs)

        if self.out_format == DataType.shapefile:
            out_path = os.path.dirname(self.outpath)
            out_file, suffix = os.path.splitext(os.path.basename(self.outpath))

            overwrite_cpg_file(out_path, out_file, 'GB2312')

        end = time.time()

        log.info("坐标转换完成! 共耗时{}秒. 数据存储至{}.".format("{:.2f}".format(end-start), self.out))

    def sz_local_to_pcs_2000(self, in_srs, out_srs):
        in_srs_wkt = osr.SpatialReference(in_srs.ExportToWkt())
        order0 = in_srs_wkt.GetAttrValue("AXIS", 1)

        para_sz_to_pcs_2000 = helmert_para(SpatialReference.sz_Local, SpatialReference.pcs_2000, order0)

        out_format = DataType_dict[self.out_format]
        translateOptions = gdal.VectorTranslateOptions(format=out_format, srcSRS=in_srs, dstSRS=out_srs,
                                                       coordinateOperation=para_sz_to_pcs_2000,
                                                       accessMode="overwrite", layerName=self.outlayername,
                                                       layerCreationOptions=self.lco)

        gdal.VectorTranslate(self.outpath, self.inpath, options=translateOptions)

    def pcs_2000_to_sz_local(self, in_srs, out_srs):
        order0 = get_axis_order(in_srs)

        para_pcs_2000_to_sz = helmert_para(SpatialReference.pcs_2000, SpatialReference.sz_Local, order0)

        out_format = DataType_dict[self.out_format]
        translateOptions = gdal.VectorTranslateOptions(format=out_format, srcSRS=in_srs, dstSRS=out_srs,
                                                       coordinateOperation=para_pcs_2000_to_sz,
                                                       accessMode="overwrite", layerName=self.outlayername,
                                                       layerCreationOptions=self.lco)

        gdal.VectorTranslate(self.outpath, self.inpath, options=translateOptions)

    def sz_local_to_gcs_2000(self, in_srs, out_srs):
        order0 = get_axis_order(in_srs)

        para_sz_to_pcs_2000 = helmert_para(SpatialReference.sz_Local, SpatialReference.pcs_2000, order0)

        temp_srs = osr.SpatialReference()
        temp_srs.ImportFromEPSG(4547)
        out_format = DataType_dict[self.out_format]
        translateOptions = gdal.VectorTranslateOptions(format="geojson", srcSRS=in_srs, dstSRS=temp_srs,
                                                       coordinateOperation=para_sz_to_pcs_2000,
                                                       layerName="temp_layer")
        tmp_outpath = os.path.join(os.path.dirname(self.outpath), "temp_layer.geojson")
        gdal.VectorTranslate(tmp_outpath, self.inpath, options=translateOptions)

        translateOptions = gdal.VectorTranslateOptions(format=out_format, srcSRS=temp_srs, dstSRS=out_srs,
                                                       accessMode="overwrite", layerName=self.outlayername,
                                                       layerCreationOptions=self.lco)
        gdal.VectorTranslate(self.outpath, tmp_outpath, options=translateOptions)

    def gcs_2000_to_sz_local(self, in_srs, out_srs):
        temp_srs = osr.SpatialReference()
        temp_srs.ImportFromEPSG(4547)

        translateOptions = gdal.VectorTranslateOptions(format="geojson", srcSRS=in_srs, dstSRS=temp_srs,
                                                       layerName="temp_layer")
        tmp_outpath = os.path.join(os.path.dirname(self.outpath), "temp_layer.geojson")
        gdal.VectorTranslate(tmp_outpath, self.inpath, options=translateOptions)

        para_pcs_2000_to_sz = helmert_para(SpatialReference.pcs_2000, SpatialReference.sz_Local)

        out_format = DataType_dict[self.out_format]
        translateOptions = gdal.VectorTranslateOptions(format=out_format, srcSRS=temp_srs, dstSRS=out_srs,
                                                       coordinateOperation=para_pcs_2000_to_sz,
                                                       accessMode="overwrite", layerName=self.outlayername,
                                                       layerCreationOptions=self.lco)
        gdal.VectorTranslate(self.outpath, tmp_outpath, options=translateOptions)


# 获取axis order，先北后东还是先东后北
def get_axis_order(srs):
    srs_wkt = osr.SpatialReference(srs.ExportToWkt())
    order0 = srs_wkt.GetAttrValue("AXIS", 1)
    return order0

if __name__ == '__main__':
    main()
