import os
import traceback

from osgeo import ogr, osr

from UICore.common import launderName
from UICore.log4p import Log
from UICore.Gv import DataType

log = Log()


class workspaceFactory(object):
    def __init__(self):
        self.datasource = None
        self.driver = None

    def get_factory(self, factory):
        wks = None
        if factory == DataType.shapefile:
            wks = shapefileWorkspaceFactory()
        elif factory == DataType.geojson:
            wks = geojsonWorkspaceFactory()
        elif factory == DataType.fileGDB:
            wks = filegdbWorkspaceFactory()

        if wks is None:
            log.error("不支持的空间数据格式!")

        return wks

    def openFromFile(self, file):
        if self.driver is None:
            log.error("缺失相应的图形文件读取引擎！", dialog=True)
            return None
        else:
            try:
                self.datasource = self.driver.Open(file, 1)
                return self.datasource
            except:
                log.error("打开文件发生错误. \n{}".format(traceback.format_exc()))
                return None

    def openLayer(self, name):
        if self.datasource is not None:
            return self.datasource.GetLayer(name)

    def getLayers(self):
        layers = []
        if self.datasource is not None:
            for layer_idx in range(self.datasource.GetLayerCount()):
                layer = self.datasource.GetLayerByIndex(layer_idx)
                layers.append(layer)
            return layers
        else:
            return []

    def getLayerNames(self):
        layer_names = []
        if self.datasource is not None:
            for layer_idx in range(self.datasource.GetLayerCount()):
                layer = self.datasource.GetLayerByIndex(layer_idx)
                layer_names.append(layer.GetName())
            return layer_names
        else:
            return []

    def cloneLayer(self, in_layer, output_path, out_layer_name, out_srs, out_format):
        if self.driver is None:
            return None

        try:
            in_defn = in_layer.GetLayerDefn()

            if os.path.exists(output_path):
                log.info("datasource已存在，在已有datasource基础上创建图层.")

                if out_format == DataType.shapefile:
                    output_path = launderName(output_path)
                    out_layer_name, suffix = os.path.splitext(os.path.basename(output_path))
                    outDS = self.driver.CreateDataSource(output_path)
                elif out_format == DataType.fileGDB:
                    outDS = self.openFromFile(output_path)
            else:
                outDS = self.driver.CreateDataSource(output_path)

            srs = osr.SpatialReference()
            srs.ImportFromEPSG(out_srs)

            out_layer = outDS.CreateLayer(out_layer_name, srs=srs, geom_type=in_layer.GetGeomType())

            if out_layer is None:
                raise Exception("创建图层失败.")

            for i in range(in_defn.GetFieldCount()):
                fieldName = in_defn.GetFieldDefn(i).GetName()
                fieldTypeCode = in_defn.GetFieldDefn(i).GetType()
                new_field = ogr.FieldDefn(fieldName, fieldTypeCode)
                out_layer.CreateField(new_field)

            return output_path, out_layer.GetName()
        except Exception as e:
            log.error("{}\n{}".format(e, traceback.format_exc()))
            return None


class shapefileWorkspaceFactory(workspaceFactory):
    def __init__(self):
        super().__init__()
        driverName = "ESRI Shapefile"
        self.driver = ogr.GetDriverByName(driverName)


class geojsonWorkspaceFactory(workspaceFactory):
    def __init__(self):
        super().__init__()
        driverName = "GeoJSON"
        self.driver = ogr.GetDriverByName(driverName)


class filegdbWorkspaceFactory(workspaceFactory):
    def __init__(self):
        super().__init__()
        driverName = "FileGDB"
        self.driver = ogr.GetDriverByName(driverName)
