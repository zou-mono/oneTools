from osgeo import ogr

from UICore.DataFactory import workspaceFactory
from UICore.Gv import DataType
from UICore.log4p import Log

log = Log(__file__)


def update_attribute_value(file_type, in_path, layer_name, header, rel_tables):
    # layer = dataSource.GetLayer(0)
    try:
        layer = None
        if file_type == DataType.shapefile:
            wks = workspaceFactory().get_factory(DataType.shapefile)
            datasource = wks.openFromFile(in_path, 1)
            layer = datasource.GetLayer(0)
        elif file_type == DataType.fileGDB:
            wks = workspaceFactory().get_factory(DataType.fileGDB)
            datasource = wks.openFromFile(in_path, 1)
            layer = datasource.GetLayerByName(layer_name)

        layerDefn = layer.GetLayerDefn()

        field_names = []
        for i in range(layerDefn.GetFieldCount()):
            fieldName = layerDefn.GetFieldDefn(i).GetName()
            field_names.append(fieldName)

        for header_value in header:
            if header_value not in field_names:
                new_field = ogr.FieldDefn(header_value, ogr.OFTString)
                new_field.SetWidth(200)
                layer.CreateField(new_field, True)

        for rel in rel_tables:
            print("rel")

        return True
    except:
        log.error("无法更新数据！可能原因：1.输入矢量图层数据正在被占用 2.输入矢量图层无法读取")
        return False
    finally:
        layer = None
