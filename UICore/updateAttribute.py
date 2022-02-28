import traceback

from osgeo import ogr

from UICore.DataFactory import workspaceFactory
from UICore.Gv import DataType
from UICore.log4p import Log

log = Log(__file__)


def update_attribute_value(file_type, in_path, layer_name, header, rel_tables):
    # layer = dataSource.GetLayer(0)
    layer = None
    dataSource = None
    try:
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

        right_header = []  # 只处理DLBM右边的字段
        bDLBM = False
        bGHFLDM1 = False
        bGHFLMC1 = False
        bGHFLSDL = False
        bGHJGFLDM =False
        bGHJGFLMC = False
        bSFJSYD = False
        CZCSXM_index = -1
        for i in range(len(header)):
            if bDLBM:
                right_header.append(header[i])

            if header[i].upper() == 'DLBM':
                bDLBM = True
            if header[i].upper() == 'CZCSXM':
                CZCSXM_index = i
            # if header[i].upper() == 'GHFLDM1':
            #     bGHFLDM1 = True
            # if header[i].upper() == 'GHFLMC1':
            #     bGHFLMC1 = True
            # if header[i].upper() == 'GHFLSDL':
            #     bGHFLSDL = True
            # if header[i].upper() == 'GHJGFLDM':
            #     bGHJGFLDM = True
            # if header[i].upper() == 'GHJGFLMC':
            #     bGHJGFLMC = True
            # if header[i].upper() == 'SFJSYD':
            #     bSFJSYD = True

        for header_value in right_header:
            if header_value not in field_names:
                new_field = ogr.FieldDefn(header_value, ogr.OFTString)
                new_field.SetWidth(200)
                layer.CreateField(new_field, True)
                new_field.Destroy()

        #  重新读取新的数据
        feature = layer.GetNextFeature()

        icount = 0
        while feature:
            DLBM_value = feature.GetField("DLBM")
            # feature.SetField("DLMC", "1")
            # feature.SetField("XZFLSDL", "我们")

            bchecked = False
            for i in range(len(rel_tables)):
                rel = rel_tables[i]
                field_name = right_header[i]
                if DLBM_value not in rel:
                    if not bchecked:
                        log.warning("第{}个要素的地类编码在规则表中不存在，采用'无对应用地'类型匹配！".format(icount))
                        feature.SetField("GHFLDM1", "16")
                        feature.SetField("GHFLMC1", "留白用地")
                        feature.SetField("GHFLSDL", "建设用地")
                        feature.SetField("GHJGFLDM", "07")
                        feature.SetField("GHJGFLMC", "城乡建设用地")
                        feature.SetField("SFJSYD", "是")
                        bchecked = True
                    # else:
                    #     layer.SetFeature(feature)
                    #     feature = layer.GetNextFeature()
                    #     continue
                else:
                    feature.SetField(field_name, str(rel[DLBM_value]))

            # 如果是CZCSXM是201或者202则重新赋值
            if CZCSXM_index > 0:
                CZCSXM_value = feature.GetField(CZCSXM_index)
                if str(CZCSXM_value).strip() == '201' or str(CZCSXM_value).strip() == '202':
                    feature.SetField(CZCSXM_index, "农用地/未利用地")
                    feature.SetField("GHJGFLDM", "07")
                    feature.SetField("GHJGFLMC", "城乡建设用地")
                    feature.SetField("SFJSYD", "是")

            layer.SetFeature(feature)
            feature = layer.GetNextFeature()

            icount += 1
            print(icount)

        return True
    except:
        print(traceback.format_exc())
        # log.error("无法更新数据！可能原因：1.输入矢量图层数据正在被占用 2.输入矢量图层无法读取")
        return False
    finally:
        if dataSource is not None:
            dataSource.Destroy()
        layer = None
        datasource = None

def readSpatialData(file_type, in_path, layer_name):
    if file_type == DataType.shapefile:
        wks = workspaceFactory().get_factory(DataType.shapefile)
        datasource = wks.openFromFile(in_path, 1)
        layer = datasource.GetLayer(0)

    elif file_type == DataType.fileGDB:
        wks = workspaceFactory().get_factory(DataType.fileGDB)
        datasource = wks.openFromFile(in_path, 1)
        layer = datasource.GetLayerByName(layer_name)

    return layer
