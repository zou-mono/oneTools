from osgeo import ogr
import osgeo.osr as osr
from osgeo import gdal
import os
import csv

from osgeo.ogr import Geometry
import UICore.coordTransform_table

UICore.coordTransform_table.coordTransform(r"D:\Codes\oneTools\data\基准数据\station_wgs84.csv",
                                           "ascii", False, 0, 1, 4326, 2435, r"D:\Codes\oneTools\res\station_sz_test.csv", "gb2312")

with open("www.csv", "w", newline="") as f:
    writer = csv.writer(f)
    for i in range(10):
        writer.writerow([i, "xr,22", "www.yyy"])

sourceSRS = osr.SpatialReference()
sourceSRS.ImportFromEPSG(2435)
in_pt = [96070.547, 53474.857]
point = ogr.CreateGeometryFromWkt("POINT({} {})".format(in_pt[0], in_pt[1]))
para = "+proj=helmert +convention=position_vector +x={} +y={} +s={} +theta={}".format(
    391090.578943, 2472660.600279, 0.999997415382, -3518.95267316)
opt = osr.CoordinateTransformationOptions()
opt.SetOperation(para)
tr = osr.CreateCoordinateTransformation(sourceSRS, None, opt)
point.Transform(tr)
print(point)


a = r"D:\Data\深圳坐标\配准中心线（深圳坐标）.shp"
b = r"D:\Data\深圳坐标\配准中心线（深圳坐标）.gdb"
c = r"D:\Data\深圳坐标\配准中心线（深圳坐标）"
print([os.path.dirname(a), os.path.dirname(b), os.path.dirname(c)])
print([os.path.basename(a), os.path.basename(b), os.path.basename(c)])
if os.path.basename(c).find('.') > 0:
    print("yes")
else:
    print("no")

input = r"D:\Data\信息中心_深圳_2016building.shp"
shp_driver = ogr.GetDriverByName("ESRI Shapefile")
inDs = shp_driver.Open(input, 1)
print(inDs.GetLayerCount())

layer = inDs.GetLayer()
spatialRef = layer.GetSpatialRef()
print(spatialRef)

srs = osr.SpatialReference(spatialRef.ExportToWkt())
print(srs)

tmp_output = r"D:\Data\深圳坐标\test\配准中心线_bj54.geojson"
# geojson_driver = ogr.GetDriverByName("ESRI Shapefile")
# outDs = driver.CreateDataSource(output)

translateOptions = gdal.VectorTranslateOptions(format="geojson",
                                               coordinateOperation="+proj=helmert +convention=position_vector +x=2472704.709219 +y=391088.722412 +s=1.000014426327 +theta=3518.94103818")
gdal.VectorTranslate(tmp_output, input, options=translateOptions)

in_srs = osr.SpatialReference()
in_srs.ImportFromEPSG(2435)
out_srs = osr.SpatialReference()
out_srs.ImportFromEPSG(4547)

output = r"D:\Data\深圳坐标\test\配准中心线_2000.shp"
translateOptions = gdal.VectorTranslateOptions(format="ESRI Shapefile", srcSRS=in_srs, dstSRS=out_srs,
                                               layerCreationOptions=["ENCODING=GBK"])
gdal.VectorTranslate(output, tmp_output, options=translateOptions)

print("ok")

