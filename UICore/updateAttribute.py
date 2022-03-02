import time
import traceback

from osgeo import ogr

from UICore.DataFactory import workspaceFactory
from UICore.Gv import DataType
from UICore.common import is_already_opened_in_write_mode
from UICore.log4p import Log

log = Log(__name__)


def update_attribute_value2(file_type, in_path, layer_name, right_header, rel_tables):
    # layer = dataSource.GetLayer(0)
    layer = None
    dataSource = None

    try:
        start = time.time()

        if file_type == DataType.shapefile:
            wks = workspaceFactory().get_factory(DataType.shapefile)
            dataSource = wks.openFromFile(in_path, 1)
            layer = dataSource.GetLayer(0)

        elif file_type == DataType.fileGDB:
            wks = workspaceFactory().get_factory(DataType.fileGDB)
            dataSource = wks.openFromFile(in_path, 1)
            layer = dataSource.GetLayerByName(layer_name)

        layerDefn = layer.GetLayerDefn()

        field_names = []
        for i in range(layerDefn.GetFieldCount()):
            fieldName = layerDefn.GetFieldDefn(i).GetName()
            field_names.append(fieldName)

        log.info("第一步: 判断是否需要增加新的字段...")
        for header_value in right_header:
            if header_value not in field_names:
                new_field = ogr.FieldDefn(header_value, ogr.OFTString)
                new_field.SetWidth(200)
                layer.CreateField(new_field, True)
                del new_field

        # layerDefn = layer.GetLayerDefn()
        #  重新读取新的数据
        feature = layer.GetNextFeature()

        log.info("第二步: 根据规则表更新数据...")
        icount = 0

        # for i in range(len(rel_tables)):
        #     rel = rel_tables[i]
        #     field_name = right_header[i]
        #     str = r"UPDATE {} SET {}= ".format(layer_name, field_name, )

        # str = r"SELECT DISTINCT DLBM FROM {}".format(layer_name)
        # aa = dataSource.ExecuteSQL(str)
        # print(aa)

        while feature:
            DLBM_value = feature.GetField("DLBM")
            bchecked = False

            for i in range(len(rel_tables)):
                rel = rel_tables[i]
                field_name = right_header[i]
                if DLBM_value not in rel:
                    if not bchecked:
                        log.debug("第{}个要素的地类编码在规则表中不存在，采用'无对应用地'类型匹配！".format(icount))
                        feature.SetField("GHFLDM1", "16")
                        feature.SetField("GHFLMC1", "留白用地")
                        feature.SetField("GHFLSDL", "建设用地")
                        feature.SetField("GHJGFLDM", "07")
                        feature.SetField("GHJGFLMC", "城乡建设用地")
                        feature.SetField("SFJSYD", "是")
                        bchecked = True
                else:
                    if feature.GetFieldType(field_name) == ogr.OFTString:
                        feature.SetField(field_name, str(rel[DLBM_value]))
                    elif feature.GetFieldType(field_name) == ogr.OFTInteger:
                        feature.SetField(field_name, int(rel[DLBM_value]))
                    elif feature.GetFieldType(field_name) == ogr.OFTReal:
                        feature.SetField(field_name, float(rel[DLBM_value]))
                    else:
                        log.debug("第{}个要素的字段{}是无法识别的数据类型. 字段类型只允许是整型、字符型或者浮点型，请调整原始数据!".format(icount, field_name))
                        feature.SetField(field_name, None)

            # 如果是CZCSXM是201或者202则重新赋值
            CZCSXM_index = feature.GetFieldIndex("CZCSXM")
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

        end = time.time()
        log.info("操作完成, 总共耗时:{}秒".format("{:.2f}".format(end-start)))
        return True
    except:
        log.error("无法更新数据！错误原因:\n{}".format(traceback.format_exc()))
        return False
    finally:
        del dataSource
        del layer
        del feature
        del wks


def update_attribute_value(file_type, in_path, layer_name, right_header, rel_tables, DLBM_values):
    # layer = dataSource.GetLayer(0)
    layer = None
    dataSource = None
    feature = None
    wks = None

    try:
        start = time.time()

        if file_type == DataType.shapefile:
            wks = workspaceFactory().get_factory(DataType.shapefile)
            dataSource = wks.openFromFile(in_path, 1)
            layer = dataSource.GetLayer(0)

        elif file_type == DataType.fileGDB:
            wks = workspaceFactory().get_factory(DataType.fileGDB)
            dataSource = wks.openFromFile(in_path, 1)
            layer = dataSource.GetLayerByName(layer_name)

        layerDefn = layer.GetLayerDefn()

        field_names = []
        for i in range(layerDefn.GetFieldCount()):
            fieldName = layerDefn.GetFieldDefn(i).GetName()
            field_names.append(fieldName)

        log.info("第1步: 根据规则表的DLBM右侧表头增加矢量图层{}中的相应字段...".format(layer_name))
        for header_value in right_header:
            if header_value not in field_names:
                new_field = ogr.FieldDefn(header_value, ogr.OFTString)
                new_field.SetWidth(200)
                layer.CreateField(new_field, True)
                del new_field

        # layerDefn = layer.GetLayerDefn()
        #  重新读取新的数据
        feature = layer.GetNextFeature()

        log.info("第2步: 对矢量图层{}的DLBM字段创建索引...".format(layer_name))
        # str = r"CREATE INDEX DLBM_index ON {} (DLBM)".format(layer_name)
        str = r"CREATE INDEX DLBM_index ON {} (DLBM)".format(layer_name)
        dataSource.ExecuteSQL(str)

        log.info("第3步: 计算矢量图层{}的DLBM字段的唯一值...".format(layer_name))
        str = r"SELECT DISTINCT DLBM FROM {}".format(layer_name)
        res = dataSource.ExecuteSQL(str, dialect="SQLite")

        DLBM_keys = []
        feature = res.GetNextFeature()
        while feature:
            DLBM_key = feature.GetField(0)
            DLBM_keys.append(DLBM_key)
            feature = res.GetNextFeature()

        log.info("第4步: 根据规则表计算矢量图层相应字段的值...")
        for DLBM_key in DLBM_keys:
            log.info("更新矢量图层{}字段DLBM中所有等于{}的值".format(layer_name, DLBM_key))

            if DLBM_key not in DLBM_values:
                log.warning("字段DLBM中包含规则表中不存在的编码{}".format(DLBM_key))

            for i in range(len(rel_tables)):
                rel = rel_tables[i]
                field_name = right_header[i]

                if DLBM_key in rel:
                    str = r"UPDATE {} SET {} = '{}' WHERE DLBM = '{}'".format(layer_name, field_name, rel[DLBM_key], DLBM_key)
                else:
                    str = r"UPDATE {} SET {} = NULL WHERE DLBM = '{}'".format(layer_name, field_name, DLBM_key)

                dataSource.ExecuteSQL(str)

        # for i in range(len(rel_tables)):
        #     rel = rel_tables[i]
        #     field_name = right_header[i]
        #     str = r"UPDATE {} SET {}= ".format(layer_name, field_name, )
        #
        # str = r"SELECT DISTINCT DLBM FROM {}".format(layer_name)
        # aa = dataSource.ExecuteSQL(str)
        # print(aa)

        end = time.time()
        log.info("操作完成, 总共耗时:{}秒".format("{:.2f}".format(end-start)))
        return True
    except:
        log.error("无法更新数据！错误原因:\n{}".format(traceback.format_exc()))
        return False
    finally:
        del dataSource
        del layer
        del feature
        del wks


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
