from osgeo import ogr
import osgeo.osr as osr
from osgeo import gdal

input = r"D:\Data\深圳坐标\配准中心线（深圳坐标）.shp"
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

