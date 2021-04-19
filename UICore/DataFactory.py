import traceback

from osgeo import ogr
from UICore.log4p import Log
from UICore.Gv import DataType

log = Log()


class workspaceFactory(object):
    def __init__(self):
        self.dataset = None
        self.driver = None
        self.layers = []
        self.wks = None
        self.layer_names = []

    def get_factory(self, factory):
        if factory == DataType.shapefile:
            self.wks = shapefileWorkspaceFactory()
        elif factory == DataType.geojson:
            self.wks = geojsonWorkspaceFactory()
        elif factory == DataType.fileGDB:
            self.wks = filegdbWorkspaceFactory()

        if self.wks is None:
            log.error("不支持的空间数据格式!")

        return self.wks

    def openFromFile(self, file):
        if self.driver is None:
            log.error("缺失相应的图形文件读取引擎！", dialog=True)
            return None
        else:
            try:
                self.dataset = self.driver.Open(file, 1)
                return self.dataset
            except:
                log.error("打开文件发生错误. \n{}".format(traceback.format_exc()))
                return None

    def openLayer(self, name):
        if self.dataset is not None:
            return self.dataset.GetLayer(name)

    def getLayers(self):
        if self.dataset is not None:
            for layer_idx in range(self.dataset.GetLayerCount()):
                layer = self.dataset.GetLayerByIndex(layer_idx)
                self.layers.append(layer)
            return self.layers
        else:
            return []

    def getLayerNames(self):
        if self.dataset is not None:
            for layer_idx in range(self.dataset.GetLayerCount()):
                layer = self.dataset.GetLayerByIndex(layer_idx)
                self.layer_names.append(layer.GetName())
            return self.layer_names
        else:
            return []


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
