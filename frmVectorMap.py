import json
import os
import sys

from PyQt5.QtGui import QFont, QPalette, QShowEvent
from UI.UIVectorMap import Ui_Dialog
from PyQt5.QtWidgets import QApplication, QDialog, QStyleFactory, QVBoxLayout, QDialogButtonBox, QFileDialog, \
    QHeaderView, QAbstractItemView
from PyQt5.QtCore import Qt, QItemSelectionModel, QModelIndex, QPersistentModelIndex
from PyQt5 import QtCore
from UICore.Gv import SplitterState, Dock
from UICore.common import get_paraInfo, urlEncodeToFileName
from UICore.log4p import Log
from widgets.mTable import mTableStyle, TableModel, vectorTableDelegate

Slot = QtCore.pyqtSlot

log = Log()

class Ui_Window(QDialog, Ui_Dialog):
    def __init__(self):
        super(Ui_Window, self).__init__()
        self.setupUi(self)

        font = QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.button(QDialogButtonBox.Ok).setFont(font)
        self.buttonBox.button(QDialogButtonBox.Ok).setText("确定")
        self.buttonBox.button(QDialogButtonBox.Cancel).setFont(font)
        self.buttonBox.button(QDialogButtonBox.Cancel).setText("取消")

        vlayout = QVBoxLayout(self)
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

        self.btn_addRow.clicked.connect(self.btn_addRow_Clicked)
        self.btn_removeRow.clicked.connect(self.removeBtn_clicked)
        self.btn_obtainMeta.clicked.connect(self.btn_obtainMeta_clicked)

        self.tbl_address.clicked.connect(self.table_index_clicked)
        self.tbl_address.verticalHeader().sectionClicked.connect(self.table_section_clicked)

    def showEvent(self, a0: QShowEvent) -> None:
        self.tbl_address.setColumnWidth(0, self.tbl_address.width() * 0.4)
        self.tbl_address.setColumnWidth(1, self.tbl_address.width() * 0.2)
        self.tbl_address.setColumnWidth(2, self.tbl_address.width() * 0.2)
        self.tbl_address.setColumnWidth(3, self.tbl_address.width() * 0.2)

    @Slot(int)
    def table_section_clicked(self, section):
        self.row_clicked(section)

    @Slot(QModelIndex)
    def table_index_clicked(self, index):
        self.row_clicked(index.row())

    @Slot()
    def btn_addRow_Clicked(self):
        selModel = self.tbl_address.selectionModel()
        if selModel is None:
            return
        if len(selModel.selectedIndexes()) == 0:
            self.model.addEmptyRow(self.model.rowCount(QModelIndex()), 1, 0)
            next_index = self.model.index(self.model.rowCount(QModelIndex()) - 1, 0)
        elif len(selModel.selectedRows()) == 1:
            next_row = selModel.selectedRows()[0].row() + 1
            self.model.addEmptyRow(next_row, 1, 0)
            next_index = self.model.index(next_row, 0)

        selModel.select(next_index, QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)
        self.tbl_address.setFocus()

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

    @Slot()
    def open_addressFile(self):
        fileName, fileType = QFileDialog.getOpenFileName(self, "选择矢量服务参数文件", os.getcwd(),
                                                                   "All Files(*)")
        self.txt_addressFile.setText(fileName)

        if fileName == "":
            return

        try:
            with open(fileName, 'r') as f:
                self.paras = json.load(f)

            self.add_address_rows_from_paras()
        except:
            log.error("读取参数文件失败！", dialog=True)

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
        self.tbl_address.DragDropMode(QAbstractItemView.InternalMove)
        self.tbl_address.setSelectionBehavior(QAbstractItemView.SelectRows | QAbstractItemView.SelectItems)
        self.tbl_address.setDefaultDropAction(Qt.MoveAction)

        self.tbl_address.horizontalHeader().setSectionsMovable(False)
        self.tbl_address.setDragEnabled(True)
        self.tbl_address.setAcceptDrops(True)

        self.service_no = 1  # 服务名字段的序号
        self.url_no = 0  # url地址的序号

        self.model = TableModel()

        self.model.setHeaderData(0, Qt.Horizontal, "地址", Qt.DisplayRole)
        self.model.setHeaderData(1, Qt.Horizontal, "服务", Qt.DisplayRole)
        self.model.setHeaderData(2, Qt.Horizontal, "输出图层名", Qt.DisplayRole)
        self.model.setHeaderData(3, Qt.Horizontal, "输出路径", Qt.DisplayRole)

        delegate = vectorTableDelegate(self, [None, {'type': 'c'}, None,
                                              {'text': "请选择或创建文件数据库", 'type': "d"}])
        self.tbl_address.setModel(self.model)
        self.tbl_address.setItemDelegate(delegate)

    @Slot()
    def btn_obtainMeta_clicked(self):
        selModel = self.tbl_address.selectionModel()

        if selModel is None:
            return

        indexes = selModel.selectedIndexes()

        ## 如果有被选中的行，则只获取被选中行的信息
        if len(indexes) > 0:
            rows = sorted(set(index.row() for index in
                              self.tbl_address.selectedIndexes()))
        else:
            rows = range(0, self.tbl_address.model().rowCount(QModelIndex()))

        for row in rows:
            url_index, service_index, url, service = self.return_url_and_level(row)
            editor_delegate = self.tbl_address.itemDelegate(service_index)
            key = url + "_" + service

            if url == "": continue

            getInfo = get_paraInfo(url)
            if getInfo is None:
                log.error(url + "无法获取远程参数信息，请检查地址是否正确以及网络是否连通！")
                continue
            else:
                log.info(url + "参数信息获取成功！")

            self.setParaToMemory(url, service, getInfo)

            # print("test")
            services = self.paras[key]['ids']

            if isinstance(editor_delegate, vectorTableDelegate):
                self.model.setLevelData(service_index, services)

    def setParaToMemory(self, url, service, getInfo):
        xmin = xmax = ymin = ymax = sp = id = layername = ""

        key = url + "_" + service

        ids = ["*"]
        if 'layers' in getInfo.keys():
            layers = getInfo['layers']
            for layer in layers:
                if 'parentLayerId' in layer:
                    if layer['parentLayerId'] == -1:
                        if 'id' in layer:
                            id = layer['id']
                            ids.append(id)
                        if 'name' in layer:
                            layername = layer['name']
        elif 'id' in getInfo.keys():
            id = getInfo['id']
            ids.append(id)
            if 'name' in getInfo.keys():
                layername = getInfo['name']

        if id == "": return

        if 'fullExtent' in getInfo.keys():
            if 'xmin' in getInfo['fullExtent']:
                xmin = getInfo['fullExtent']['xmin']
            if 'xmax' in getInfo['fullExtent']:
                xmax = getInfo['fullExtent']['xmax']
            if 'ymin' in getInfo['fullExtent']:
                ymin = getInfo['fullExtent']['ymin']
            if 'ymax' in getInfo['fullExtent']:
                ymax = getInfo['fullExtent']['ymax']

        if 'extent' in getInfo.keys():
            if 'xmin' in getInfo['extent']:
                xmin = getInfo['extent']['xmin']
            if 'xmax' in getInfo['extent']:
                xmax = getInfo['extent']['xmax']
            if 'ymin' in getInfo['extent']:
                ymin = getInfo['extent']['ymin']
            if 'ymax' in getInfo['extent']:
                ymax = getInfo['extent']['ymax']

        if 'spatialReference' in getInfo.keys():
            if 'wkid' in getInfo['spatialReference']:
                sp = getInfo['spatialReference']['wkid']

        paras = {}
        paras[id] = {
            'id': id,
            'layername': layername,
            'xmin': xmin,
            'xmax': xmax,
            'ymin': ymin,
            'ymax': ymax,
            'spatialReference': sp,
            'layer_name': "",
            'output': ""
        }

        url_encodeStr = urlEncodeToFileName(url)
        self.paras[key] = {
            'code': url_encodeStr,
            'ids': ids,
            'paras': paras
        }
        print(self.paras)

    def row_clicked(self, logicRow):
        sel_index = self.tbl_address.model().index(logicRow, 0, QModelIndex())
        self.update_txt_info(sel_index)
        self.selIndex = sel_index

    def return_url_and_level(self, logicRow):
        url_index = self.tbl_address.model().index(logicRow, self.url_no)
        level_index = self.tbl_address.model().index(logicRow, self.service_no)
        url = self.tbl_address.model().data(url_index, Qt.DisplayRole)
        level = self.tbl_address.model().data(level_index, Qt.DisplayRole)

        return url_index, level_index, url, level

    def update_all_paras_value(self, oldValue, newValue):
        pass

    def update_txt_info(self, index: QModelIndex, level=-1):
        key1_index = self.tbl_address.model().index(index.row(), 0)
        key1 = self.tbl_address.model().data(key1_index, Qt.DisplayRole)
        key2_index = self.tbl_address.model().index(index.row(), 1)
        key2 = self.tbl_address.model().data(key2_index, Qt.DisplayRole)

        self.txt_xmin.setText("")
        self.txt_xmax.setText("")
        self.txt_ymin.setText("")
        self.txt_ymax.setText("")
        self.txt_spatialReference.setText("")

        bUpdate = False
        key = key1 + "_" + key2
        if key in self.paras:
            getInfo = self.paras[key]
            bUpdate = True

        if bUpdate:
            if 'layername' in getInfo:
                self.lbl_layer.setText(str(getInfo['layername']))
            if 'xmin' in getInfo:
                self.txt_xmin.setText(str(getInfo['xmin']))
                self.txt_xmin.home(False)
            if 'xmax' in getInfo:
                self.txt_xmax.setText(str(getInfo['xmax']))
                self.txt_xmax.home(False)
            if 'ymin' in getInfo:
                self.txt_ymin.setText(str(getInfo['ymin']))
                self.txt_ymin.home(False)
            if 'ymax' in getInfo:
                self.txt_ymax.setText(str(getInfo['ymax']))
                self.txt_ymax.home(False)
            if 'spatialReference' in getInfo:
                self.txt_spatialReference.setText(str(getInfo['spatialReference']))
                self.txt_spatialReference.home(False)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    style = QStyleFactory.create("windows")
    app.setStyle(style)
    MainWindow = QDialog()
    window = Ui_Window()
    window.show()
    sys.exit(app.exec_())