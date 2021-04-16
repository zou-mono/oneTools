from PyQt5.QtCore import QRect, Qt, QPersistentModelIndex, QItemSelectionModel, QModelIndex, QThread, QObject
from PyQt5.QtGui import QDoubleValidator, QIntValidator, QPalette
from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox, QErrorMessage, QDialogButtonBox, QStyleFactory, \
    QAbstractItemView, QHeaderView, QComboBox, QAbstractButton, QFileDialog
from PyQt5 import QtWidgets, QtGui, QtCore
from osgeo import osr

import UI.UICoordTransform
import UI.listview_dialog
import sys
import json
import os

from UICore.DataFactory import workspaceFactory
from UICore.Gv import SplitterState, Dock, DataType, srs_dict, srs_list
from UICore.common import defaultImageFile, defaultTileFolder, urlEncodeToFileName, get_paraInfo, get_srs_by_epsg
from widgets.mTable import TableModel, mTableStyle, layernameDelegate, srsDelegate, outputPathDelegate
from UICore.log4p import Log

Slot = QtCore.pyqtSlot

log = Log()

# class myFileSelect(QFileDialog):
#     def __init__(self):
#         super().__init__()

class Ui_Window(QtWidgets.QDialog, UI.UICoordTransform.Ui_Dialog):
    def __init__(self):
        super(Ui_Window, self).__init__()
        self.setupUi(self)

        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.button(QDialogButtonBox.Ok).setFont(font)
        self.buttonBox.button(QDialogButtonBox.Ok).setText("确定")
        self.buttonBox.button(QDialogButtonBox.Cancel).setFont(font)
        self.buttonBox.button(QDialogButtonBox.Cancel).setText("取消")

        vlayout = QtWidgets.QVBoxLayout(self)
        vlayout.addWidget(self.splitter)
        vlayout.setContentsMargins(0, 0, 10, 10)
        self.splitter.setGeometry(0, 0, self.width(), self.height())

        self.splitter.setOrientation(Qt.Horizontal)
        self.splitter.setProperty("Stretch", SplitterState.collapsed)
        self.splitter.setProperty("Dock", Dock.right)
        self.splitter.setProperty("WidgetToHide", self.txt_log)
        self.splitter.setProperty("ExpandParentForm", True)

        self.splitter.setSizes([600, self.splitter.width() - 590])
        self.resize(self.splitter.width(), self.splitter.height())

        self.paras = {}  # 存储参数信息
        self.selIndex = QModelIndex()
        self.table_init()

        log.setLogViewer(parent=self, logViewer=self.txt_log)
        self.txt_log.setReadOnly(True)

        self.btn_addressFile.clicked.connect(self.open_addressFile)
        self.btn_addRow.clicked.connect(self.btn_addRow_clicked)
        self.btn_removeRow.clicked.connect(self.btn_removeBtn_clicked)
        self.btn_saveMetaFile.clicked.connect(self.btn_saveMetaFile_clicked)

    def showEvent(self, a0: QtGui.QShowEvent) -> None:
        self.rbtn_file.click()
        self.table_layout()

    def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
        self.table_layout()

    def table_layout(self):
        self.tbl_address.setColumnWidth(0, self.tbl_address.width() * 0.16)
        self.tbl_address.setColumnWidth(1, self.tbl_address.width() * 0.16)
        self.tbl_address.setColumnWidth(2, self.tbl_address.width() * 0.18)
        self.tbl_address.setColumnWidth(3, self.tbl_address.width() * 0.18)
        self.tbl_address.setColumnWidth(4, self.tbl_address.width() * 0.16)
        self.tbl_address.setColumnWidth(5, self.tbl_address.width() * 0.15)

    @Slot()
    def btn_addRow_clicked(self):
        if self.rbtn_file.isChecked():
            fileNames, fileType = QFileDialog.getOpenFileNames(
                self, "选择需要转换的图形文件", os.getcwd(),
                "ESRI Shapefile(*.shp);;GeoJson(*.geojson);;CAD drawing(*.dwg)")
            if len(fileNames) == 0:
                return

            wks = None
            for fileName in fileNames:
                if fileType == 'ESRI Shapefile(*.shp)':
                    wks = workspaceFactory().get_factory(DataType.shapefile)
                elif fileType == 'GeoJson(*.geojson)':
                    wks = workspaceFactory().get_factory(DataType.geojson)
                elif fileType == 'CAD drawing(*.dwg)':
                    print('dwg')

                dataset = wks.openFromFile(fileName)
                layer_name = wks.getLayerNames()[0]

                if dataset is not None:
                    in_layer = dataset.GetLayer()
                    self.add_layer_to_row(in_layer, fileName, layer_name)

                    dataset.Release()
                    dataset = None
                    in_layer = None

        elif self.rbtn_filedb.isChecked():
            fileName = QtWidgets.QFileDialog.getExistingDirectory(self, "选择需要转换的GDB数据库",
                                                                  os.getcwd(), QFileDialog.ShowDirsOnly)
            wks = workspaceFactory().get_factory(DataType.fileGDB)
            dataset = wks.openFromFile(fileName)

            if dataset is not None:
                lst_names = wks.getLayerNames()
                selected_names = nameListDialog().openListDialog(lst_names)

                if selected_names is not None:
                    for selected_name in selected_names:
                        layer = wks.openLayer(selected_name)
                        self.add_layer_to_row(layer, fileName, selected_name)

    def add_layer_to_row(self, in_layer, fileName, layer_name):
        in_srs = in_layer.GetSpatialRef()
        if in_srs is not None:
            in_srs = osr.SpatialReference(in_srs.ExportToWkt())
            srs_epsg = in_srs.GetAttrValue("AUTHORITY", 1)
            srs_desc = get_srs_by_epsg(srs_epsg)
        else:
            srs_desc = None

        row = self.model.rowCount(QModelIndex())
        self.model.addEmptyRow(row, 1, 0)
        url_index = self.tbl_address.model().index(row, self.url_no)
        in_layername_index = self.tbl_address.model().index(row, self.in_layername_no)
        in_srs_index = self.tbl_address.model().index(row, self.in_srs_no)

        self.tbl_address.model().setData(url_index, fileName)
        self.tbl_address.model().setData(in_layername_index, layer_name)
        self.tbl_address.model().setData(in_srs_index, srs_desc)

        self.add_delegate_to_row(row, fileName, layer_name)

    def add_delegate_to_row(self, row, fileName, layer_name):
        in_layername_index = self.tbl_address.model().index(row, self.in_layername_no)
        in_srs_index = self.tbl_address.model().index(row, self.in_srs_no)
        out_srs_index = self.tbl_address.model().index(row, self.out_srs_no)

        editor_delegate = self.tbl_address.itemDelegate(in_layername_index)
        # if isinstance(editor_delegate, layernameDelegate):
        #     levelData = [layer_name]
        #     self.model.setLevelData(fileName, levelData)
        if isinstance(editor_delegate, layernameDelegate):
            if 'layer_names' not in self.model.levels:
                levelData = {
                    'layer_names': [layer_name]
                }
            else:
                levelData = self.model.levels['layer_names']
                levelData.append(layer_name)

            self.model.setLevelData(fileName, levelData)
        #
        # in_srs_delegate = self.tbl_address.itemDelegate(in_srs_index)
        # out_srs_delegate = self.tbl_address.itemDelegate(out_srs_index)
        # if isinstance(in_srs_delegate, srsDelegate) or isinstance(in_srs_delegate, out_srs_delegate):
        #     if 'in_srs' not in self.model.levels:
        #         levelData = {
        #             'in_srs': [layer_name]
        #         }
        #     else:
        #         levelData = self.model.levels['layer_names']
        #         levelData.append(layer_name)
        #
        #     self.model.setLevelData(fileName, levelData)

    @Slot()
    def open_addressFile(self):
        fileName, fileType = QtWidgets.QFileDialog.getOpenFileName(self, "选择坐标转换参数文件", os.getcwd(),
                                                                   "All Files(*)")
        self.txt_addressFile.setText(fileName)

        if fileName == "":
            return

        try:
            with open(fileName, 'r', encoding='utf-8') as f:
                self.paras = json.load(f)

            self.add_address_rows_from_paras()
        except:
            log.error("读取参数文件失败！", dialog=True)

    def add_address_rows_from_paras(self):
        imps = self.paras['exports']
        for imp in imps:
            row = self.model.rowCount(QModelIndex())
            self.model.addEmptyRow(self.model.rowCount(QModelIndex()), 1, 0)

            # self.model.setLevelData(imp['in_path'], )

            self.tbl_address.model().setData(self.tbl_address.model().index(row, 0), imp['in_path'])
            self.tbl_address.model().setData(self.tbl_address.model().index(row, 1), imp['in_layer'])
            self.tbl_address.model().setData(self.tbl_address.model().index(row, 2), imp['in_srs'])
            self.tbl_address.model().setData(self.tbl_address.model().index(row, 3), imp['out_srs'])
            self.tbl_address.model().setData(self.tbl_address.model().index(row, 4), imp['out_path'])
            self.tbl_address.model().setData(self.tbl_address.model().index(row, 5), imp['out_layer'])

    @Slot()
    def btn_saveMetaFile_clicked(self):
        fileName, fileType = QFileDialog.getSaveFileName(self, "请选择保存的参数文件", os.getcwd(),
                                                         "json file(*.json)")

        datas = self.tbl_address.model().datas
        levels = self.tbl_address.model().levelData()
        logicRows = range(0, len(datas))

        results = []

        for logicRow in logicRows:
            key = datas[logicRow][0]
            row_data = {
                'in_path': datas[logicRow][0],
                'in_layer': datas[logicRow][1],
                'in_srs': datas[logicRow][2],
                'out_srs': datas[logicRow][3],
                'out_path': datas[logicRow][4],
                'out_layer': datas[logicRow][5],
                # 'layer_names': levels[key]
                # 'in_srs_list':
                # 'out_srs_list':
            }
            results.append(row_data)

        res = {
            'exports': results
        }

        try:
            if fileName != '':
                with open(fileName, 'w', encoding='UTF-8') as f:
                    json.dump(res, f, ensure_ascii=False)
        except:
            log.error("文件存储路径错误，无法保存！", parent=self, dialog=True)

    def table_init(self):
        self.tbl_address.setStyle(mTableStyle())

        self.tbl_address.horizontalHeader().setStretchLastSection(True)
        self.tbl_address.verticalHeader().setDefaultSectionSize(20)
        self.tbl_address.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)  # 行高固定

        color = self.palette().color(QPalette.Button)
        self.tbl_address.horizontalHeader().setStyleSheet(
            "QHeaderView::section {{ background-color: {}}}".format(color.name()))
        self.tbl_address.verticalHeader().setStyleSheet(
            "QHeaderView::section {{ background-color: {}}}".format(color.name()))
        self.tbl_address.setStyleSheet(
            "QTableCornerButton::section {{ color: {}; border: 1px solid; border-color: {}}}".format(color.name(),
                                                                                                     color.name()))

        self.tbl_address.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tbl_address.setEditTriggers(QAbstractItemView.SelectedClicked | QAbstractItemView.DoubleClicked)
        # self.tbl_address.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl_address.DragDropMode(QAbstractItemView.InternalMove)
        self.tbl_address.setSelectionBehavior(QAbstractItemView.SelectRows | QAbstractItemView.SelectItems)
        self.tbl_address.setDefaultDropAction(Qt.MoveAction)

        self.tbl_address.horizontalHeader().setSectionsMovable(False)
        self.tbl_address.setDragEnabled(True)
        self.tbl_address.setAcceptDrops(True)

        self.url_no = 0  # 输入路径字段的序号
        self.in_layername_no = 1  # 输入图层的序号
        self.out_layername_no = 5 # 输出图层的序号
        self.in_srs_no = 2
        self.out_srs_no = 3 # 输出坐标系的序号

        self.model = TableModel()

        self.model.setHeaderData(0, Qt.Horizontal, "输入路径", Qt.DisplayRole)
        self.model.setHeaderData(1, Qt.Horizontal, "输入图层", Qt.DisplayRole)
        self.model.setHeaderData(2, Qt.Horizontal, "输入坐标系", Qt.DisplayRole)
        self.model.setHeaderData(3, Qt.Horizontal, "输出坐标系", Qt.DisplayRole)
        self.model.setHeaderData(4, Qt.Horizontal, "输出路径", Qt.DisplayRole)
        self.model.setHeaderData(5, Qt.Horizontal, "输出图层", Qt.DisplayRole)
        self.tbl_address.setModel(self.model)

        layername_delegate = layernameDelegate(self, {'type': 'c'})
        self.tbl_address.setItemDelegateForColumn(1, layername_delegate)
        srs_delegate = srsDelegate(self, srs_list)
        self.tbl_address.setItemDelegateForColumn(2, srs_delegate)
        self.tbl_address.setItemDelegateForColumn(3, srs_delegate)
        outputpath_delegate = outputPathDelegate(self, {'type': 'd'})
        self.tbl_address.setItemDelegateForColumn(4, outputpath_delegate)

    @Slot()
    def btn_removeBtn_clicked(self):
        index_list = []
        selModel = self.tbl_address.selectionModel()
        if selModel is None:
            return
        for model_index in selModel.selectedRows():
            index = QPersistentModelIndex(model_index)
            index_list.append(index)

        for index in index_list:
            self.model.removeRows(index.row(), 1, 0)

        next_index = self.model.index(self.model.rowCount(QModelIndex()) - 1, 0)
        selModel.select(next_index, QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)
        self.tbl_address.setFocus()

    def return_url_and_layername(self, logicRow):
        url_index = self.tbl_address.model().index(logicRow, self.url_no)
        layername_index = self.tbl_address.model().index(logicRow, self.in_layername_no)
        url = self.tbl_address.model().data(url_index, Qt.DisplayRole)
        layername = self.tbl_address.model().data(layername_index, Qt.DisplayRole)
        return url_index, layername_index, url, layername

    def update_outlayername(self, index: QModelIndex, text):
        if index.column() == self.out_srs_no:
            in_layername_index = self.tbl_address.model().index(index.row(), self.in_layername_no)
            out_srs_index = self.tbl_address.model().index(index.row(), self.out_srs_no)
            out_layername_index = self.tbl_address.model().index(index.row(), self.out_layername_no)
            layer_name = self.tbl_address.model().data(in_layername_index, Qt.DisplayRole)
            self.tbl_address.model().setData(out_srs_index, text)
            self.tbl_address.model().setData(out_layername_index, "{}_{}".format(layer_name, text))


class nameListDialog(QtWidgets.QDialog, UI.listview_dialog.Ui_Dialog):
    def __init__(self):
        super(nameListDialog, self).__init__()
        self.setupUi(self)
        self.pushButton.clicked.connect(self.pushButton_clicked)
        self.select_names = []

    def openListDialog(self, lst_names):
        for name in lst_names:
            self.lv_name.addItem(name)

        result = self.exec_()

        if result == 1:
            return self.select_names

    def pushButton_clicked(self):
        sel_items = self.lv_name.selectedItems()
        for item in sel_items:
            self.select_names.append(item.text())
        self.done(1)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    style = QStyleFactory.create("windows")
    app.setStyle(style)
    MainWindow = QDialog()
    window = Ui_Window()
    window.show()
    sys.exit(app.exec_())