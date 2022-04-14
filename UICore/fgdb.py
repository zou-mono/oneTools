from UICore import filegdbapi
from UICore.filegdbapi import new_wstringsp, wstringsp_value, new_stringp, stringp_value, FieldDef, new_intp, \
    intp_value, EnumRows, FieldInfo, new_wstringp, wstringp_value, new_fieldtypep, fieldtypep_value, new_shortp, \
    shortp_value, new_tmp, tmp_value, new_doublep, doublep_value, new_floatp, floatp_value
from UICore.log4p import Log
import xml.etree.ElementTree as ET
from enum import Enum
from datetime import datetime

log = Log(__name__)


class FieldType(Enum):
    fieldTypeSmallInteger = 0
    fieldTypeInteger = 1
    fieldTypeSingle = 2
    fieldTypeDouble = 3
    fieldTypeString = 4
    fieldTypeDate = 5
    fieldTypeOID = 6
    fieldTypeGeometry = 7
    fieldTypeBlob = 8
    fieldTypeRaster = 9
    fieldTypeGUID = 10
    fieldTypeGlobalID = 11
    fieldTypeXML = 12


class GeoDatabase(filegdbapi.Geodatabase):
    m_layers = []

    def __init__(self):
        super(GeoDatabase, self).__init__()
        self.table = filegdbapi.Table()

    def Open(self, file):
        hr = 0
        try:
            gdb = filegdbapi.Geodatabase()
            hr = filegdbapi.OpenGeodatabase(file, gdb)
            if hr < 0:
                raise Exception("打开GDB发生错误，代码{}".format(str(hr)))
            else:
                self.datasource = gdb
                bflag, err_msg = self.__LoadLayers("\\")
                if not bflag:
                    raise Exception(err_msg)
                return True, gdb
        except Exception as e:
            return False, e

    # 按层次打开所有table和feature class
    def __LoadLayers(self, root):
        tables = new_wstringsp()
        featureclasses = new_wstringsp()
        featuredatasets = new_wstringsp()

        if self.datasource.GetChildDatasets(root, "Table", tables) < 0:
            del tables
            return False, "读取路径{}下的Table时发生错误".format(root)
        tables = wstringsp_value(tables)
        self.__OpenFGDBTables(tables)

        if self.datasource.GetChildDatasets(root, "Feature Class", featureclasses) < 0:
            del featureclasses
            return False, "读取路径{}下的Feature Class时发生错误".format(root)
        featureclasses = wstringsp_value(featureclasses)
        self.__OpenFGDBTables(featureclasses)

        if self.datasource.GetChildDatasets(root, "Feature Dataset", featuredatasets) < 0:
            del featuredatasets
            return False, "读取路径{}下的Feature Dataset时发生错误".format(root)
        featuredatasets = wstringsp_value(featuredatasets)
        for i in range(len(featuredatasets)):
            featuredataset = featuredatasets[i]
            featureclasses = new_wstringsp()
            if self.datasource.GetChildDatasets(featuredataset, "Feature Class", featureclasses) < 0:
                del featureclasses
                return False, "读取Feature Dataset{}下的Feature Class时发生错误".format(featuredataset)
            featureclasses = wstringsp_value(featureclasses)
            self.__OpenFGDBTables(featureclasses)
        return True, ""

    def __OpenFGDBTables(self, layers):
        for layer in layers:
            tbl = Table()
            hr = self.datasource.OpenTable(layer, tbl)
            if hr < 0:
                del tbl
                log.error("打开Table{}时发生错误.".format(layer))
                continue

            self.m_layers.append(tbl)

    def GetLayerByName(self, name):
        tbl = Table()
        hr = self.datasource.OpenTable(name, tbl)
        if hr < 0:
            del tbl
            log.error("打开Table{}时发生错误.".format(name))
            return None
        else:
            tbl.ResetReading()
            return tbl


class Table(filegdbapi.Table):
    def __init__(self):
        super(Table, self).__init__()
        self.m_featureDef = FeatureDefn()
        self.m_enumRows = EnumRows()
        # hr = self.Search("*", "1=1", True, rows)
        # self.m_enumRows = rows

    def ResetReading(self):
        hr = self.Search("*", "1=1", True, self.m_enumRows)

    def GetLayerDefn(self):
        tableDef = new_stringp()
        hr = self.GetDefinition(tableDef)
        # if hr < 0:
        #     del tableDef
        #     log.error("获取GDB的元数据错误")
        #     return None
        tableDef = stringp_value(tableDef)

        root = ET.fromstring(tableDef)
        if root is None:
            log.error("获取GDB的元数据错误")
            return None

        if root.tag != "DataElement":
            log.error("获取GDB的元数据错误")
            return None

        Fields = root.find("Fields")
        FieldArray = Fields.find("FieldArray")
        for field in FieldArray:
            fieldDef = FieldDefn()

            name = field.find("Name")
            if name is not None:
                fieldDef.SetName(name.text)

            alias_name = field.find("AliasName")
            if alias_name is not None:
                fieldDef.SetAlias(alias_name.text)

            type = field.find("Type")
            if type is not None:
                fieldDef.SetType(type.text)

            self.m_featureDef.append(fieldDef)

        return self.m_featureDef

    def CreateField(self, field_def, approx_ok=True):
        hr = self.AddField(field_def)
        if hr < 0:
            log.error("创建字段错误. 代码: {}".format(str(hr)))
            return False
        else:
            self.ResetReading()
            return True

    def GetFeatureCount(self):
        count = new_intp()
        hr = self.GetRowCount(count)
        if hr < 0:
            log.error("获取要素数量错误. 代码: {}".format(str(hr)))
            return -1
        else:
            return intp_value(count)

    def GetNextFeature(self):
        row = Row()
        hr = self.m_enumRows.Next(row)
        if hr < 0:
            log.error("获取要素错误. 代码:{}".format(str(hr)))
            return None
        elif hr == 0:
            return row
        elif hr == 1:
            return None

    def SetFeature(self, row):
        hr = self.Update(row)
        if hr < 0:
            log.error("更新字段错误. 代码:{}".format(str(hr)))


class Row(filegdbapi.Row):
    def __init__(self):
        super(Row, self).__init__()

    def GetFieldIndex(self, get_field_name):
        try:
            fieldInfo = FieldInfo()
            hr = self.GetFieldInformation(fieldInfo)

            if hr < 0:
                raise Exception("获取要素字段元数据错误. 代码:{}".format(str(hr)))

            field_count = new_intp()
            hr = fieldInfo.GetFieldCount(field_count)
            if hr < 0:
                raise Exception("获取要素字段元数据错误. 代码:{}".format(str(hr)))
            field_count = intp_value(field_count)

            for i in range(field_count):
                field_name = new_wstringp()
                hr = fieldInfo.GetFieldName(i, field_name)
                if hr < 0:
                    raise Exception("获取要素字段元数据错误. 代码:{}".format(str(hr)))

                field_name = wstringp_value(field_name)
                if field_name == get_field_name:
                    return i

            return -1
        except Exception as e:
            log.error(e)
            return -1

    def GetField(self, fld_index):
        if isinstance(fld_index, str):
            fld_index = self.GetFieldIndex(fld_index)
        if (fld_index < 0) or (fld_index > self.GetFieldCount()):
            raise KeyError("获取字段函数GetField()错误.")
        fld_type = self.GetFieldType(fld_index)

        if fld_type == FieldType.fieldTypeInteger.value:
            value = new_intp()
            self.GetInteger(fld_index, value)
            value = intp_value(value)
            return value

        if fld_type == FieldType.fieldTypeSmallInteger.value:
            value = new_shortp()
            self.GetShort(fld_index, value)
            value = shortp_value(value)
            return value

        if fld_type == FieldType.fieldTypeOID.value:
            value = new_intp()
            self.GetOID(value)
            value = intp_value(value)
            return value

        if fld_type == FieldType.fieldTypeDate.value:
            value = new_tmp()
            # self.GetDate(fld_index, value)
            value = filegdbapi.GetDate_string(self, fld_index, value)
            value = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            return value

        if fld_type == FieldType.fieldTypeString.value:
            value = new_wstringp()
            self.GetString(fld_index, value)
            value = wstringp_value(value)
            return value

        if fld_type == FieldType.fieldTypeDouble.value:
            value = new_doublep()
            self.GetDouble(fld_index, value)
            value = doublep_value(value)
            return value

        if fld_type == FieldType.fieldTypeSingle.value:
            value = new_floatp()
            self.GetFloat(fld_index, value)
            value = floatp_value(value)
            return value

    def SetField(self, *args):
        """
        SetField(self, int id, char value)
        SetField(self, char name, char value)
        SetField(self, int id, int value)
        SetField(self, char name, int value)
        SetField(self, int id, double value)
        SetField(self, char name, double value)
        SetField(self, int id, int year, int month, int day, int hour, int minute,
            int second, int tzflag)
        SetField(self, char name, int year, int month, int day, int hour,
            int minute, int second, int tzflag)
        """
        hr = 0

        fld_index = args[0]
        if isinstance(fld_index, str):
            fld_index = self.GetFieldIndex(fld_index)
        if (fld_index < 0) or (fld_index > self.GetFieldCount()):
            raise KeyError("获取字段函数GetField()错误.")
        fld_type = self.GetFieldType(fld_index)

        if len(args) == 2 and args[1] is None:
            hr = self.SetNull(fld_index)

        if len(args) == 2:
            if fld_type == FieldType.fieldTypeInteger.value and isinstance(args[1], int):
                hr = self.SetInteger(fld_index, args[1])

            if fld_type == FieldType.fieldTypeSmallInteger.value and isinstance(args[1], int):
                hr = self.SetShort(fld_index, args[1])

            if fld_type == FieldType.fieldTypeString.value and isinstance(args[1], str):
                hr = self.SetString(fld_index, args[1])

            if fld_type == FieldType.fieldTypeDouble.value and isinstance(args[1], float):
                hr = self.SetDouble(fld_index, args[1])

            if fld_type == FieldType.fieldTypeSingle.value and isinstance(args[1], float):
                hr = self.SetFloat(fld_index, args[1])
        else:
            vtime = "{}-{}-{} {}:{}:{}".format(str(args[1]), str(args[2]), str(args[3]), str(args[4]), str(args[5]), str(args[6]))
            hr = filegdbapi.SetDate_string(self, fld_index, vtime)

        if hr < 0:
            raise Exception("第{}个字段赋值错误.".format(str(fld_index)))

    def GetFieldType(self, fld_index):
        fieldInfo = FieldInfo()
        hr = self.GetFieldInformation(fieldInfo)
        if hr < 0:
            raise Exception("获取要素字段元数据错误. 代码:{}".format(str(hr)))

        fieldType = new_fieldtypep()
        hr = fieldInfo.GetFieldType(fld_index, fieldType)
        if hr < 0:
            raise Exception("获取要素字段元数据错误. 代码:{}".format(str(hr)))
        fieldType = fieldtypep_value(fieldType)

        return fieldType

    def GetFieldCount(self):
        fieldInfo = FieldInfo()
        hr = self.GetFieldInformation(fieldInfo)

        if hr < 0:
            raise Exception("获取要素字段元数据错误. 代码:{}".format(str(hr)))

        field_count = new_intp()
        hr = fieldInfo.GetFieldCount(field_count)
        if hr < 0:
            raise Exception("获取要素字段元数据错误. 代码:{}".format(str(hr)))
        field_count = intp_value(field_count)

        return field_count


class FeatureDefn(list):
    def __init__(self):
        super(FeatureDefn, self).__init__()

    def GetFieldDefn(self, i):
        return self[i]

    def GetFieldCount(self):
        return len(self)


class FieldDefn(filegdbapi.FieldDef):
    def __init__(self, name="t", type=4):
        self.SetType(type)
        self.SetName(name)

        super(FieldDefn, self).__init__()

    def SetType(self, type):
        self.type = type

    def GetType(self):
        return self.type

    def SetName(self, name):
        self.name = name

    def GetName(self):
        return self.name

    def SetAlias(self, alias):
        self.alias = alias

    def GetAlias(self):
        return self.alias

    def SetWidth(self, length):
        self.SetLength(length)
        self.length = length

    def GetWidth(self):
        return self.length
