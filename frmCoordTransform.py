from PyQt5.QtCore import QRect, Qt, QPersistentModelIndex, QItemSelectionModel, QModelIndex, QThread, QObject
from PyQt5.QtGui import QDoubleValidator, QIntValidator, QPalette
from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox, QErrorMessage, QDialogButtonBox, QStyleFactory, \
    QAbstractItemView, QHeaderView, QComboBox, QAbstractButton, QFileDialog, QWidget, QListView, QTreeView
from PyQt5 import QtWidgets, QtGui, QtCore
from osgeo import osr

# from UI.UICoordTransform import Ui_Dialog
# from UI.listview_dialog import Ui_Dialog
import UI.UICoordTransform
import UI.listview_dialog
import sys
import json
import os
import re

from UICore.DataFactory import workspaceFactory
from UICore.Gv import SplitterState, Dock, DataType, srs_dict, srs_list
from UICore.common import defaultImageFile, defaultTileFolder, urlEncodeToFileName, get_paraInfo, get_srs_by_epsg
from widgets.mTable import TableModel, mTableStyle, addressTableDelegate, layernameDelegate, srsDelegate, \
    outputPathDelegate
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
        self.btn_removeRow.clicked.connect(self.removeBtn_clicked)

    def showEvent(self, a0: QtGui.QShowEvent) -> None:
        self.rbtn_file.click()

        self.tbl_address.setColumnWidth(0, self.tbl_address.width() * 0.16)
        self.tbl_address.setColumnWidth(1, self.tbl_address.width() * 0.16)
        self.tbl_address.setColumnWidth(2, self.tbl_address.width() * 0.18)
        self.tbl_address.setColumnWidth(3, self.tbl_address.width() * 0.18)
        self.tbl_address.setColumnWidth(4, self.tbl_address.width() * 0.16)
        self.tbl_address.setColumnWidth(5, self.tbl_address.width() * 0.15)

    def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
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
                    self.add_file_to_row(in_layer, fileName, layer_name)

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

                for selected_name in selected_names:
                    layer = wks.openLayer(selected_name)
                    self.add_file_to_row(layer, fileName, selected_name)

    def add_file_to_row(self, in_layer, fileName, layer_name):
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
        in_srs_index = self.tbl_address.model().index(row, 2)

        self.tbl_address.model().setData(url_index, fileName)
        self.tbl_address.model().setData(in_layername_index, layer_name)
        self.tbl_address.model().setData(in_srs_index, srs_desc)

        editor_delegate = self.tbl_address.itemDelegate(in_layername_index)
        if isinstance(editor_delegate, layernameDelegate):
            levelData = [layer_name]
            self.model.setLevelData(fileName, levelData)

    @Slot()
    def open_addressFile(self):
        pass

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
        srs_delegate = srsDelegate(self, {'type': 'c'})
        self.tbl_address.setItemDelegateForColumn(2, srs_delegate)
        self.tbl_address.setItemDelegateForColumn(3, srs_delegate)
        outputpath_delegate = outputPathDelegate(self, {'type': 'd'})
        self.tbl_address.setItemDelegateForColumn(4, outputpath_delegate)

    @Slot()
    def removeBtn_clicked(self):
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