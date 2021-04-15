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

        return self.wks

    def openFromFile(self, file):
        if self.driver is None:
            log.error("缺失相应的图形文件读取引擎！", dialog=True)
            return None
        else:
            self.dataset = self.driver.Open(file, 1)
            return self.dataset

    def openLayer(self, name):
        pass

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
        driverName = "ESRI Shapefile"
        self.driver = ogr.GetDriverByName(driverName)
        self.featsClassList = []
        self.dataset = None
        self.layer_names = []


class geojsonWorkspaceFactory(workspaceFactory):
    def __init__(self):
        driverName = "GeoJSON"
        self.driver = ogr.GetDriverByName(driverName)
        self.featsClassList = []
        self.dataset = None
        self.layer_names = []


class filegdbWorkspaceFactory(workspaceFactory):
    def __init__(self):
        driverName = "FileGDB"
        self.driver = ogr.GetDriverByName(driverName)
        self.featsClassList = []
        self.dataset = None
        self.layer_names = []
