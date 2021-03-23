from PyQt5.QtCore import QRect, Qt, QPersistentModelIndex, QItemSelectionModel, QModelIndex
from PyQt5.QtGui import QDoubleValidator, QIntValidator, QPalette
from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox, QErrorMessage, QDialogButtonBox, QStyleFactory, \
    QAbstractItemView, QHeaderView, QComboBox, QAbstractButton, QFileDialog
from PyQt5 import QtWidgets, QtGui
from UI.UITileMap import Ui_Dialog
from suplicmap_tilemap import get_json
import sys
import json
import os
import re
import base64
from UICore.Gv import SplitterState, Dock, defaultImageFile, defaultTileFolder
from widgets.mTable import TableModel, mTableStyle, addressTableDelegate
from UICore.log4p import Log

log = Log(__file__)


class Ui_Window(QtWidgets.QDialog, Ui_Dialog):
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

        self.btn_addRow.clicked.connect(self.btn_addRow_Clicked)
        self.btn_addressFile.clicked.connect(self.open_addressFile)
        self.btn_removeRow.clicked.connect(self.removeBtn_clicked)

        self.rbtn_onlySpider.clicked.connect(self.rbtn_toggled)
        self.rbtn_onlyHandle.clicked.connect(self.rbtn_toggled)
        self.rbtn_spiderAndHandle.clicked.connect(self.rbtn_toggled)
        self.tbl_address.verticalHeader().sectionClicked.connect(self.table_section_clicked)
        self.btn_obtainMeta.clicked.connect(self.btn_obtainMeta_clicked)
        self.buttonBox.clicked.connect(self.buttonBox_clicked)
        self.btn_saveMetaFile.clicked.connect(self.btn_saveMetaFile_clicked)

        self.validateValue()

        self.paras = {}  # 存储参数信息
        self.table_init()

    def btn_saveMetaFile_clicked(self):
        datas = self.tbl_address.model().datas

        bHasData = False
        for i in datas:
            for j in i:
                if j != '':
                    bHasData = True
                    break
            else:
                continue
            break

        if bHasData and bool(self.paras):
            fileName, fileType = QFileDialog.getSaveFileName(self, "请选择保存的参数文件", os.getcwd(),
                                                             "json file(*.json)")
            rows = range(0, self.tbl_address.model().rowCount())

            for v in self.paras.values():
                v['exports'] = []

            for row in rows:
                url = datas[row][self.url_no]

                if url in self.paras.keys():
                    paras = self.paras[url]['paras']
                    level = datas[row][self.level_no]

                    if level in paras:
                        if self.rbtn_spiderAndHandle.isChecked():
                            self.paras[url]['exports'].append({
                                'level': level,
                                'tileFolder': datas[row][2],
                                'imageFile': datas[row][3]
                            })
                        elif self.rbtn_onlySpider.isChecked():
                            self.paras[url]['exports'].append({
                                'level': level,
                                'tileFolder': datas[row][2],
                                'imageFile': ''
                            })
            try:
                with open(fileName, 'w+') as f:
                    json.dump(self.paras, f)
            except:
                log.error("文件存储路径错误，无法保存！", parent=self, dialog=True)

    def buttonBox_clicked(self, button: QAbstractButton):
        if button == self.buttonBox.button(QDialogButtonBox.Ok):
            print(self.paras),
        elif button == self.buttonBox.button(QDialogButtonBox.Cancel):
            self.close()

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

        self.level_no = 1  # 等级字段的序号
        self.url_no = 0  # url地址的序号

        # self.rbtn_spiderAndHandle.setChecked(True)

    def showEvent(self, a0: QtGui.QShowEvent) -> None:
        self.rbtn_spiderAndHandle.click()

    # self.tbl_address.show()

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
        # self.tableView.setCurrentIndex(next_index)
        selModel.select(next_index, QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)
        self.tbl_address.setFocus()

    def validateValue(self):
        doubleValidator = QDoubleValidator()
        doubleValidator.setNotation(QDoubleValidator.StandardNotation)
        self.txt_originX.setValidator(doubleValidator)
        self.txt_originY.setValidator(doubleValidator)
        self.txt_xmin.setValidator(doubleValidator)
        self.txt_xmax.setValidator(doubleValidator)
        self.txt_ymin.setValidator(doubleValidator)
        self.txt_ymax.setValidator(doubleValidator)
        self.txt_tilesize.setValidator(doubleValidator)
        self.txt_resolution.setValidator(doubleValidator)

        integerValidator = QIntValidator(0, 99)
        self.txt_level.setValidator(integerValidator)

    def rbtn_toggled(self, btn):
        self.model = TableModel()

        self.txt_originX.setText("")
        self.txt_originY.setText("")
        self.txt_xmin.setText("")
        self.txt_xmax.setText("")
        self.txt_ymin.setText("")
        self.txt_ymax.setText("")
        self.txt_tilesize.setText("")
        self.txt_resolution.setText("")
        self.txt_level.setText("")

        if self.rbtn_onlyHandle.isChecked():
            self.txt_addressFile.setEnabled(False)
            self.btn_addressFile.setEnabled(False)

            self.txt_tileInfoFile.setEnabled(True)
            self.btn_tileInfoDialog.setEnabled(True)

            self.txt_originX.setEnabled(True)
            self.txt_originY.setEnabled(True)
            self.txt_resolution.setEnabled(True)
            self.txt_tilesize.setEnabled(True)

            self.txt_level.setEnabled(True)

            self.model.setHeaderData(0, Qt.Horizontal, "输入瓦片文件夹", Qt.DisplayRole)
            # self.model.setHeaderData(1, Qt.Horizontal, "参数文件", Qt.DisplayRole)
            self.model.setHeaderData(1, Qt.Horizontal, "输出影像文件", Qt.DisplayRole)
            delegate = addressTableDelegate(self, [{'text': "请选择瓦片文件夹", 'type': "d"},
                                                   {'text': "请选择输出影像文件", 'type': "f"}])
            self.tbl_address.setModel(self.model)
            self.tbl_address.setItemDelegate(delegate)
            self.tbl_address.setColumnWidth(0, self.tbl_address.width() / 2)
            self.tbl_address.setColumnWidth(1, self.tbl_address.width() / 2)
        else:
            self.txt_addressFile.setEnabled(True)
            self.btn_addressFile.setEnabled(True)

            self.txt_tileInfoFile.setEnabled(False)
            self.btn_tileInfoDialog.setEnabled(False)

            self.txt_originX.setEnabled(False)
            self.txt_originY.setEnabled(False)
            self.txt_resolution.setEnabled(False)
            self.txt_tilesize.setEnabled(False)

            self.txt_level.setEnabled(False)

            # self.model.setHeaderData(0, Qt.Horizontal, "ID", Qt.DisplayRole)
            self.model.setHeaderData(0, Qt.Horizontal, "地址", Qt.DisplayRole)

            if self.rbtn_onlySpider.isChecked():
                self.model.setHeaderData(1, Qt.Horizontal, "等级", Qt.DisplayRole)
                self.model.setHeaderData(2, Qt.Horizontal, "瓦片文件夹", Qt.DisplayRole)

                delegate = addressTableDelegate(self, [None, {'type': 'c'},
                                                       {'text': "请选择输出瓦片文件夹", 'type': "d"}])
                self.tbl_address.setModel(self.model)
                self.tbl_address.setItemDelegate(delegate)
                self.tbl_address.setColumnWidth(0, self.tbl_address.width() * 0.4)
                self.tbl_address.setColumnWidth(1, self.tbl_address.width() * 0.2)
                self.tbl_address.setColumnWidth(2, self.tbl_address.width() * 0.4)

            elif self.rbtn_spiderAndHandle.isChecked():
                self.model.setHeaderData(1, Qt.Horizontal, "等级", Qt.DisplayRole)
                self.model.setHeaderData(2, Qt.Horizontal, "瓦片文件夹", Qt.DisplayRole)
                self.model.setHeaderData(3, Qt.Horizontal, "输出影像文件", Qt.DisplayRole)

                delegate = addressTableDelegate(self, [None, {'type': 'c'},
                                                       {'text': "请选择输出瓦片文件夹", 'type': "d"},
                                                       {'text': "请选择输出影像文件", 'type': "f"}])
                self.tbl_address.setModel(self.model)
                self.tbl_address.setItemDelegate(delegate)
                self.tbl_address.setColumnWidth(0, self.tbl_address.width() * 0.4)
                self.tbl_address.setColumnWidth(1, self.tbl_address.width() * 0.2)
                self.tbl_address.setColumnWidth(2, self.tbl_address.width() * 0.2)
                self.tbl_address.setColumnWidth(3, self.tbl_address.width() * 0.2)

    def table_section_clicked(self, index):
        self.section_clicked = index
        print(index)

    def open_addressFile(self):
        fileName, fileType = QtWidgets.QFileDialog.getOpenFileName(self, "选择服务地址文件", os.getcwd(),
                                                                   "All Files(*)")
        self.txt_addressFile.setText(fileName)

    def btn_obtainMeta_clicked(self):
        selModel = self.tbl_address.selectionModel()

        if selModel is None:
            return

        indexes = selModel.selectedIndexes()
        print(len(indexes))

        if self.rbtn_onlyHandle.isChecked():
            return

        # 测试
        # with open("data/tile_Info.json", 'r') as j:
        #     self.getInfo = json.load(j)
        # self.lods = self.getInfo['tileInfo']['lods']
        # levels = []
        # for lod in self.lods:
        #     levels.append(lod["level"])

        ## 如果有被选中的行，则只获取被选中行的信息
        if len(indexes) > 0:
            rows = sorted(set(index.row() for index in
                              self.tbl_address.selectedIndexes()))
        else:
            rows = range(0, self.tbl_address.model().rowCount(QModelIndex()))

        for row in rows:
            level_index = self.tbl_address.model().index(row, self.level_no, QModelIndex())
            url_index = self.tbl_address.model().index(row, self.url_no, QModelIndex())
            editor_delegate = self.tbl_address.itemDelegate(level_index)

            url = str(self.tbl_address.model().data(url_index, Qt.DisplayRole)).strip()

            if url == "": continue

            if url not in self.paras.keys():
                getInfo = self.get_paraInfo(url)
                if getInfo is None:
                    log.error(url + "无法获取远程参数信息，请检查地址是否正确以及网络是否连通！")
                    continue
                else:
                    log.info(url + "参数信息获取成功！")

                self.setParaToMemory(url, getInfo)

            levels = self.paras[url]['levels']

            if isinstance(editor_delegate, addressTableDelegate):
                # editor_delegate.setLevels(levels)
                self.model.setLevelData(level_index, levels)

    def setParaToMemory(self, url, getInfo):
        levels = []
        resolutions = []
        lods = []
        origin_x = origin_y = xmin = xmax = ymin = ymax = resolution = tilesize = level = ""

        if 'tileInfo' in getInfo.keys():
            if 'origin' in getInfo['tileInfo'].keys():
                if 'x' in getInfo['tileInfo']['origin'].keys():
                    origin_x = getInfo['tileInfo']['origin']['x']
                if 'y' in getInfo['tileInfo']['origin'].keys():
                    origin_y = getInfo['tileInfo']['origin']['y']
            if 'lods' in getInfo['tileInfo'].keys():
                lods = getInfo['tileInfo']['lods']

        if 'extent' in getInfo.keys():
            if 'xmin' in getInfo['extent']:
                xmin = getInfo['extent']['xmin']
            if 'xmax' in getInfo['extent']:
                xmax = getInfo['extent']['xmax']
            if 'ymin' in getInfo['extent']:
                ymin = getInfo['extent']['ymin']
            if 'ymax' in getInfo['extent']:
                ymax = getInfo['extent']['ymax']

        if 'tileInfo' in getInfo.keys():
            if 'rows' in getInfo['tileInfo']:
                tilesize = getInfo['tileInfo']['rows']

        paras = {}
        for lod in lods:
            if 'level' in lod.keys():
                level = lod['level']
                levels.append(level)

                if 'resolution' in lod.keys():
                    resolution = lod['resolution']
                    resolutions.append(resolution)

                paras[str(level)] = {
                    'origin_x': origin_x,
                    'origin_y': origin_y,
                    'xmin': xmin,
                    'xmax': xmax,
                    'ymin': ymin,
                    'ymax': ymax,
                    'tilesize': tilesize,
                    'resolution': resolution,
                    'tileFolder': '',
                    'imageFile': ''
                }

        url_encodeStr = str(base64.b64encode(url.encode("utf-8")), "utf-8")
        self.paras[url] = {
            'code': url_encodeStr,
            'levels': levels,
            'paras': paras
        }

    def get_paraInfo(self, url):
        http = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        res = re.match(http, string=url)
        url_json = url + "?f=pjson"
        if res is not None:
            getInfo = get_json(url_json)
            return getInfo
        else:
            return None

    def update_txt_info(self, index: QModelIndex, level):
        print([index.row(), index.column()])
        url_index = self.tbl_address.model().index(index.row(), 0)
        url = self.tbl_address.model().data(url_index, Qt.DisplayRole)
        getInfo = self.paras[url]['paras'][level]

        self.txt_originX.setText(str(getInfo['origin_x']))
        self.txt_originY.setText(str(getInfo['origin_x']))
        self.txt_xmin.setText(str(getInfo['xmin']))
        self.txt_xmax.setText(str(getInfo['xmax']))
        self.txt_ymin.setText(str(getInfo['ymin']))
        self.txt_ymax.setText(str(getInfo['ymax']))
        self.txt_tilesize.setText(str(getInfo['tilesize']))
        self.txt_resolution.setText(str(getInfo['resolution']))

    def cmb_selectionchange(self, i):
        self.update_txt_info(i)

    def open_tileInfoFile(self):
        fileName, fileType = QtWidgets.QFileDialog.getOpenFileName(self, "选择瓦片信息json文件", os.getcwd(),
                                                                   "json Files(*.json);;All Files(*)")
        self.txt_infoPath.setText(fileName)

    def open_tileFolder(self):
        get_folder = QtWidgets.QFileDialog.getExistingDirectory(self,
                                                                "选择瓦片文件夹",
                                                                os.getcwd())
        self.txt_imageFolderPath.setText(get_folder)

    def accept(self):
        QMessageBox.information(self, "提示", "OK", QMessageBox.Yes)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    print("start")
    style = QStyleFactory.create("windows")
    app.setStyle(style)
    # MainWindow = QDialog()
    window = Ui_Window()
    window.show()
    sys.exit(app.exec())
