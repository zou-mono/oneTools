import csv
import time
import traceback

import click
import os

from osgeo import ogr, osr, gdal
import pyproj

from UICore.DataFactory import workspaceFactory
from UICore.Gv import DataType, DataType_dict, srs_dict
from UICore.common import launderName, overwrite_cpg_file, is_already_opened_in_write_mode, \
    helmert_para_dict, get_suffix, is_number, text_line_count
from UICore.coordTransform_dwg import transform_dwg
from UICore.coordTransform_web import gcj02_to_wgs84_acc, wgs84_to_gcj02, bd09_to_wgs84_acc, wgs84_to_bd09
from UICore.log4p import Log
from UICore.Gv import SpatialReference

log = Log(__file__)

@click.command()
@click.option(
    '--inpath', '-i',
    help='Input table file. For example, d:/res/data/xxx.csv',
    type=str,
    required=True)
@click.option(
    '--inencode',
    help='Input encoding. The default is utf-8',
    type=str,
    default='utf-8',
    required=False)
@click.option(
    '--xfield', '-x',
    help='The order of x field.',
    type=int,
    required=True)
@click.option(
    '--yfield', '-y',
    help='The order of y field.',
    type=int,
    required=True)
@click.option(
    '--insrs',
    help='Input srs. sz_Local = 2435, gcs_2000 = 4490, pcs_2000 = 4547, pcs_2000_zone = 4526, wgs84 = 4326, bd09 = -1, '
         'gcj02 = -2, gcs_xian80 = 4610, pcs_xian80 = 2383, pcs_xian80_zone = 2363. The in layer\'s srs will be used to the default',
    type=int,
    default='-99',
    required=False)
@click.option(
    '--outsrs',
    help='Output srs. sz_Local = 0, gcs_2000 = 1, pcs_2000 = 2, pcs_2000_zone = 3, wgs84 = 4, bd09 = 5, '
         'gcj02 = 6, gcs_xian80 = 7, pcs_xian80 = 8, pcs_xian80_zone = 9.',
    type=int,
    required=True)
@click.option(
    '--outpath', '-o',
    help='Output table file. For example, d:/res/data/xxx.csv',
    type=str,
    required=True)
@click.option(
    '--outencode',
    help='Output encoding. For example, d:/res/data/xxx.csv',
    type=str,
    default='utf-8',
    required=False)
def main(inpath, inencode, xfield, yfield, insrs, outsrs, outpath, outencode):
    """spatial coordinate transformation program"""
    coordTransform(inpath, inencode, xfield, yfield, insrs, outsrs, outpath, outencode)


def coordTransform(inpath, inencode, xfield, yfield, insrs, outsrs, outpath, outencode):
    if inpath[-1] == os.sep:
        inpath = inpath[:-1]
    if outpath[-1] == os.sep:
        outpath = outpath[:-1]

    in_format = get_suffix(inpath)
    out_format = get_suffix(outpath)

    try:
        tfer = Transformer(in_format, out_format, inpath, inencode, xfield, yfield, outpath, outencode)
        tfer.transform(insrs, outsrs)
        return True, ''
    except:
        return False, traceback.format_exc()


class Transformer(object):
    def __init__(self, informat, outformat, inpath, inencode, x, y, outpath, outencode):
        self.out_format = outformat
        self.in_format = informat
        self.in_path = inpath
        self.in_encode = inencode
        self.out_encode = outencode
        self.out_path = outpath
        self.x = x
        self.y = y

    def transform(self, srcSRS, dstSRS):
        log.info("启动从{}到{}的转换...".format(self.in_path, self.out_path))

        start = time.time()

        res = None
        if srcSRS == SpatialReference.sz_Local and dstSRS == SpatialReference.pcs_2000:
            res = self.export_to_file(self.sz_local_to_pcs_2000)
        elif srcSRS == SpatialReference.pcs_2000 and dstSRS == SpatialReference.sz_Local:
            res = self.export_to_file(self.pcs_2000_to_sz_local)
        elif srcSRS == SpatialReference.sz_Local and dstSRS == SpatialReference.gcs_2000:
            res = self.export_to_file(self.sz_local_to_gcs_2000)
        elif srcSRS == SpatialReference.gcs_2000 and dstSRS == SpatialReference.sz_Local:
            res = self.gcs_2000_to_sz_local()
        elif srcSRS == SpatialReference.sz_Local and dstSRS == SpatialReference.wgs84:
            res = self.sz_local_to_wgs84()
        elif srcSRS == SpatialReference.wgs84 and dstSRS == SpatialReference.sz_Local:
            res = self.wgs84_to_sz_local()
        elif srcSRS == SpatialReference.sz_Local and dstSRS == SpatialReference.pcs_2000_zone:
            res = self.sz_local_to_pcs_2000_zone()
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

        if res is None:
            log.info("坐标转换完成! 共耗时{}秒. 输出路径:{}"
                     .format("{:.2f}".format(end-start), self.out_path))
        else:
            log.error("坐标转换失败!{}".format(res))

    def export_to_file(self, transform_method):
        try:
            # with open(self.in_path, "r", encoding=self.in_encode) as f:
            #     total_count = sum(1 for row in f)
            total_count = text_line_count(self.in_path, self.in_encode)

            with open(self.in_path, "r", encoding=self.in_encode) as f:
                reader = csv.reader(f)

                iprop = 1
                with open(self.out_path, 'w+', encoding=self.out_encode, newline='') as o:
                    writer = csv.writer(o)
                    icount = 1
                    points = []
                    for row in reader:
                        if not is_number(row[self.x]) or not is_number(row[self.y]):
                            log.warning("第{}行的坐标包含非数字字段，无法转换!".format(icount))
                            writer.writerow([])
                            continue

                        if icount % 1000 == 0 or icount > total_count - 1000:
                            points = transform_method(points)
                            writer.writerows(points)

                        points.append([float(row[0]), float(row[1])])

                        # writer.writerow([point.GetX(), point.GetY()])
                        # writer.writerow([point[0], point[1]])
                        icount += 1

                        # print(icount)
                        if int(icount * 100 / total_count) == iprop * 20:
                            log.debug("{:.0%}".format(icount / total_count))
                            iprop += 1

            return None
        except:
            return traceback.format_exc()

    # 关键转换，需要参数
    def sz_local_to_pcs_2000(self, points):
        helmert_para = helmert_para_dict(2435, 4547, "EAST")
        opt = osr.CoordinateTransformationOptions()
        opt.SetOperation(helmert_para)
        sourceSRS = osr.SpatialReference()
        sourceSRS.ImportFromEPSG(2435)
        tr = osr.CreateCoordinateTransformation(sourceSRS, None, opt)
        points = osr.CoordinateTransformation.TransformPoints(tr, points)
        # point.Transform(tr)
        return points

    # 关键转换，需要参数
    def pcs_2000_to_sz_local(self, points):
        helmert_para = helmert_para_dict(4547, 2435, "EAST")
        opt = osr.CoordinateTransformationOptions()
        opt.SetOperation(helmert_para)
        sourceSRS = osr.SpatialReference()
        sourceSRS.ImportFromEPSG(4547)
        tr = osr.CreateCoordinateTransformation(sourceSRS, None, opt)
        osr.CoordinateTransformation.TransformPoints(tr, points)
        # point.Transform(tr)
        return points

    def sz_local_to_gcs_2000(self, points):
        start = time.time()
        points = self.sz_local_to_pcs_2000(points)
        end = time.time()
        print(end - start)

        start = time.time()
        sourceSRS = osr.SpatialReference()
        sourceSRS.ImportFromEPSG(4547)
        destinationSRS = osr.SpatialReference()
        destinationSRS.ImportFromEPSG(4490)
        tr = osr.CreateCoordinateTransformation(sourceSRS, destinationSRS)
        # pt = osr.CoordinateTransformation.TransformPoints(tr, [[434431.2239, 431392.0434], [431392.0434, 2607747.97677669]])
        # [434431.2239, 431392.0434, 431408.4703, 412476.2589, 412535.6403],
        #                              [2612265.488, 2607747.97677669, 2607774.43119491, 2592367.01357008, 2592864.81664873]
        # point.Transform(tr)
        points = osr.CoordinateTransformation.TransformPoints(tr, points)


        # transformer = pyproj.Transformer.from_crs("epsg:4547", "epsg:4490", always_xy=True)
        # point = transformer.transform(point.GetX(), point.GetY())

        end = time.time()
        print(end - start)
        return points

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

    def wgs84_to_pcs_2000(self, inpath=None, outpath=None, outformat=None):
        pass

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
    ogr.UseExceptions()
    gdal.SetConfigOption("OGR_CT_FORCE_TRADITIONAL_GIS_ORDER", "YES")
    main()
