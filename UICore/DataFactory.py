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
        elif factory == DataType.cad_dwg:
            wks = dwgWorkspaceFactory()

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
                log.error("打开文件{}发生错误!\n{}".format(file, traceback.format_exc()))
                return None

    def openLayer(self, name):
        if self.datasource is not None:
            try:
                layer = self.datasource.GetLayer(name)
                if layer is None:
                    log.warning("图层{}不存在!".format(name))
                    return None
                else:
                    return layer
            except:
                log.error("读取图层{}发生错误!\n{}".format(name, traceback.format_exc()))
                return None

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

        out_DS = None
        out_layer = None
        try:
            in_defn = in_layer.GetLayerDefn()

            if os.path.exists(output_path):
                log.info("datasource已存在，在已有datasource基础上创建图层.")

                if out_format == DataType.shapefile or out_format == DataType.geojson:
                    self.driver.DeleteDataSource(output_path)

                    # 如果无法删除则再修改图层名新建一个
                    if os.path.exists(output_path):
                        output_path = launderName(output_path)
                        out_layer_name, suffix = os.path.splitext(os.path.basename(output_path))
                    out_DS = self.driver.CreateDataSource(output_path)
                elif out_format == DataType.fileGDB:
                    out_DS = self.openFromFile(output_path)
                    # out_layer = out_DS.GetLayer(out_layer_name)
                    # print(out_DS.TestCapability(ogr.ODsCDeleteLayer))
                    # if out_layer is not None:
                    #     out_DS.DeleteLayer(out_layer_name)
            else:
                out_DS = self.driver.CreateDataSource(output_path)

            srs = osr.SpatialReference()
            srs.ImportFromEPSG(out_srs)

            if out_format == DataType.shapefile:
                out_layer = out_DS.CreateLayer(out_layer_name, srs=srs, geom_type=in_layer.GetGeomType(),
                                              options=['ENCODING=GBK'])
            elif out_format == DataType.fileGDB or out_format == DataType.geojson:
                out_layer = out_DS.CreateLayer(out_layer_name, srs=srs, geom_type=in_layer.GetGeomType())

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
            return None, None
        finally:
            out_DS = None
            out_layer = None


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


class dwgWorkspaceFactory(workspaceFactory):
    def __init__(self):
        super().__init__()
        driverName = "CAD"
        self.driver = ogr.GetDriverByName(driverName)
