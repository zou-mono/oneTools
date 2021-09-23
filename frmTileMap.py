import base64
import time

from PyQt5.QtCore import QRect, Qt, QPersistentModelIndex, QItemSelectionModel, QModelIndex, QThread
from PyQt5.QtGui import QDoubleValidator, QIntValidator, QPalette
from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox, QErrorMessage, QDialogButtonBox, QStyleFactory, \
    QAbstractItemView, QHeaderView, QComboBox, QAbstractButton, QFileDialog, QLineEdit
from PyQt5 import QtWidgets, QtGui, QtCore
from UI.UITileMap import Ui_Dialog
import sys
import json
import os
import re
from UICore.Gv import SplitterState, Dock
from UICore.common import defaultImageFile, defaultTileFolder, urlEncodeToFileName, get_paraInfo
from widgets.mTable import TableModel, mTableStyle, addressTableDelegate
from UICore.log4p import Log
from UICore.workerThread import crawlTilesWorker

Slot = QtCore.pyqtSlot

log = Log(__name__)

pixelType_dict = {
    'U8': '无符号8位整型',
    'S8': '符号8位整型',
    'U16': '无符号16位整型',
    'S16': '符号16位整型',
    'U32': '无符号32位整型',
    'S32': '符号32位整型',
    'F32': '32位浮点型',
    'F64': '64位浮点型'
}

class Ui_Window(QtWidgets.QDialog, Ui_Dialog):
    def __init__(self, parent=None):
        super(Ui_Window, self).__init__(parent=parent)
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

        self.splitter.splitterMoved.connect(self.splitterMoved)
        self.splitter.handle(1).handleClicked.connect(self.handleClicked)

        self.btn_addRow.clicked.connect(self.btn_addRow_Clicked)
        self.btn_removeRow.clicked.connect(self.btn_removeBtn_clicked)

        self.rbtn_onlySpider.clicked.connect(self.rbtn_toggled)
        self.rbtn_onlyHandle.clicked.connect(self.rbtn_toggled)
        self.rbtn_spiderAndHandle.clicked.connect(self.rbtn_toggled)
        self.tbl_address.verticalHeader().sectionClicked.connect(self.table_section_clicked)
        self.btn_obtainMeta.clicked.connect(self.btn_obtainMeta_clicked)
        self.buttonBox.clicked.connect(self.buttonBox_clicked)
        self.btn_saveMetaFile.clicked.connect(self.btn_saveMetaFile_clicked)

        self.btn_tileInfoDialog.clicked.connect(self.open_tileInfoFile)
        self.btn_addressFile.clicked.connect(self.open_addressFile)

        self.txt_originX.editingFinished.connect(self.txt_originX_edited)
        self.txt_originY.editingFinished.connect(self.txt_originY_edited)
        self.txt_xmin.editingFinished.connect(self.txt_xmin_edited)
        self.txt_xmax.editingFinished.connect(self.txt_xmax_edited)
        self.txt_ymin.editingFinished.connect(self.txt_ymin_edited)
        self.txt_ymax.editingFinished.connect(self.txt_ymax_edited)
        self.txt_resolution.editingFinished.connect(self.txt_resolution_edited)
        self.txt_tilesize.editingFinished.connect(self.txt_tilesize_edited)

        self.tbl_address.clicked.connect(self.table_index_clicked)

        self.validateValue()

        self.paras = {}  # 存储参数信息
        self.selIndex = QModelIndex()
        self.table_init()
        log.setLogViewer(parent=self, logViewer=self.txt_log)
        self.txt_log.setReadOnly(True)

        #  最后运算过程放至到另一个线程避免GUI卡住
        self.thread = QThread(self)
        self.crawlTilesThread = crawlTilesWorker()
        self.crawlTilesThread.moveToThread(self.thread)
        self.crawlTilesThread.crawl.connect(self.crawlTilesThread.crawlTiles)
        self.crawlTilesThread.crawlAndMerge.connect(self.crawlTilesThread.crawlAndMergeTiles)
        self.crawlTilesThread.finished.connect(self.threadStop)
        self.crawlTilesThread.merge.connect(self.crawlTilesThread.mergeTiles)

        self.bInit = True  # 第一次初始化窗口
        self.init_cmb_pixelType() # 初始化pixel type下拉框
        self.cmb_pixelType.currentIndexChanged.connect(self.cmb_pixelType_changed)

        # self.cb_compression.stateChanged.connect(self.cb_compression_changed)

    def init_cmb_pixelType(self):
        for value in pixelType_dict.values():
            self.cmb_pixelType.addItem(value)
        self.update_para_value("pixelType", self.cmb_pixelType)

    def cmb_pixelType_changed(self, i):
        self.update_para_value("pixelType", self.cmb_pixelType)

    def update_para_value(self, key, editor, bSel=True):
        if isinstance(editor, QLineEdit):
            value = editor.text()
        elif isinstance(editor, QComboBox):
            value = list(filter(lambda k: pixelType_dict[k] == editor.currentText(), pixelType_dict.keys()))[0]
        else:
            return

        if bSel and self.selIndex.row() < 0:
            return
        if self.rbtn_onlyHandle.isChecked():
            tileFolder_index = self.tbl_address.model().index(self.selIndex.row(), 0)
            tileFolder = self.tbl_address.model().data(tileFolder_index, Qt.DisplayRole)
            imageFile_index = self.tbl_address.model().index(self.selIndex.row(), 1)
            imageFile = self.tbl_address.model().data(imageFile_index, Qt.DisplayRole)
            para_key = tileFolder + "_" + imageFile
            #  以输入文件夹和输出文件作为关键字
            if para_key in self.paras:
                self.paras[para_key][key] = value
            else:
                self.paras[para_key] = {
                    key: value
                }
        else:
            url_index, level_index, url, level = self.return_url_and_level(self.selIndex.row())
            if url in self.paras:
                if level in self.paras[url]['paras']:
                    self.paras[url]['paras'][level][key] = value

        if isinstance(editor, QLineEdit):
            editor.home(False)

    def update_all_paras_value(self, oldValue, newValue, url, level):
        print(oldValue)
        if self.rbtn_onlyHandle.isChecked():
            if oldValue in self.paras:
                del self.paras[oldValue]
            self.paras[newValue] = self.update_para_dict()

    @Slot()
    def txt_originX_edited(self):
        self.update_para_value("origin_x", self.txt_originX)

    @Slot()
    def txt_originY_edited(self):
        self.update_para_value("origin_y", self.txt_originY)

    @Slot()
    def txt_xmin_edited(self):
        self.update_para_value("xmin", self.txt_xmin)

    @Slot()
    def txt_xmax_edited(self):
        self.update_para_value("xmax", self.txt_xmax)

    @Slot()
    def txt_ymin_edited(self):
        self.update_para_value("ymin", self.txt_ymin)

    @Slot()
    def txt_ymax_edited(self):
        self.update_para_value("ymax", self.txt_ymax)

    @Slot()
    def txt_resolution_edited(self):
        self.update_para_value("resolution", self.txt_resolution)

    @Slot()
    def txt_tilesize_edited(self):
        self.update_para_value("tilesize", self.txt_tilesize)

    def row_clicked(self, logicRow):
        if self.rbtn_spiderAndHandle.isChecked() or self.rbtn_onlySpider.isChecked():
            level_index = self.tbl_address.model().index(logicRow, self.level_no, QModelIndex())
            level = self.tbl_address.model().data(level_index, Qt.DisplayRole)
            self.update_txt_info(level_index, level)

            self.selIndex = level_index
        elif self.rbtn_onlyHandle.isChecked():
            sel_index = self.tbl_address.model().index(logicRow, 0, QModelIndex())
            self.update_txt_info(sel_index)
            self.selIndex = sel_index

    @Slot(int)
    def table_section_clicked(self, section):
        self.row_clicked(section)

    @Slot(QModelIndex)
    def table_index_clicked(self, index):
        self.row_clicked(index.row())

    @Slot()
    def btn_saveMetaFile_clicked(self):
        fileName = ''
        datas = self.tbl_address.model().datas
        # selModel = self.tbl_address.selectionModel()
        # if selModel is None:
        #     return
        #
        # selRow = -1
        # paras_dict = {}
        # if self.selIndex is not None:
        #     selRow = self.selIndex.row()
        #     paras_dict = self.update_para_dict()

        bHasData = False
        for i in datas:
            for j in i:
                if j != '':
                    bHasData = True
                    break
            else:
                continue
            break

        rows = range(0, len(datas))
        if self.rbtn_spiderAndHandle.isChecked() or self.rbtn_onlySpider.isChecked():
            if bHasData and bool(self.paras):
                fileName, fileType = QFileDialog.getSaveFileName(self, "请选择保存的参数文件", os.getcwd(),
                                                                 "json file(*.json)")
                # rows = range(0, self.tbl_address.model().rowCount())
                if fileName == "":
                    return

                for v in self.paras.values():
                    v['exports'] = []

                for row in rows:
                    url = datas[row][self.url_no]

                    if url in self.paras.keys():
                        level = datas[row][self.level_no]

                        if level not in self.paras[url]['paras']:
                            level = -1

                        # if row == selRow:
                        #     self.paras[url]['paras'][level] = paras_dict

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
        elif self.rbtn_onlyHandle.isChecked():
            if bHasData and bool(self.paras):
                fileName, fileType = QFileDialog.getSaveFileName(self, "请选择保存的参数文件", os.getcwd(),
                                                                 "json file(*.json)")

                if fileName == "":
                    return

                keys = []
                for row in rows:
                    tileFolder = datas[row][0]
                    imageFile = datas[row][1]
                    key = tileFolder + "_" + imageFile

                    keys.append(key)

                    # if key in self.paras:
                    #     self.paras[key]['tileFolder'] = tileFolder
                    #     self.paras[key]['imageFile'] = imageFile
                    # else:
                    self.paras[key] = self.update_para_dict()
                    self.paras[key]['tileFolder'] = tileFolder
                    self.paras[key]['imageFile'] = imageFile

                for k in list(self.paras.keys()):
                    if k not in keys:
                        del self.paras[k]
        try:
            if fileName != '':
                with open(fileName, 'w', encoding='UTF-8') as f:
                    json.dump(self.paras, f, ensure_ascii=False)
        except:
            log.error("文件存储路径错误，无法保存！", parent=self, dialog=True)

    @Slot(QAbstractButton)
    def buttonBox_clicked(self, button: QAbstractButton):
        if button == self.buttonBox.button(QDialogButtonBox.Ok):
            if not self.check_paras():
                return

            self.thread.start()
            self.run_process()
        elif button == self.buttonBox.button(QDialogButtonBox.Cancel):
            if self.thread.isRunning():
                self.thread.exit(0)
            self.close()

    def run_process(self):
        rows = range(0, self.tbl_address.model().rowCount(QModelIndex()))

        bCompression = True if self.cb_compression.checkState() == 2 else False

        for row in rows:

            # if self.rbtn_onlyHandle:
            #     pass
            # else:
            url_index, level_index, url, level = self.return_url_and_level(row)


            if self.rbtn_spiderAndHandle.isChecked():
                if url not in self.paras:
                    log.error("{}地址错误".format(url))
                    continue

                paras = self.paras[url]['paras'][level]
                tileFolder_index = self.tbl_address.model().index(row, 2, QModelIndex())
                imgFile_index = self.tbl_address.model().index(row, 3, QModelIndex())
                tileFolder = str(self.tbl_address.model().data(tileFolder_index, Qt.DisplayRole)).strip()
                imgFile = str(self.tbl_address.model().data(imgFile_index, Qt.DisplayRole)).strip()

                if tileFolder == "":
                    tileFolder = defaultTileFolder(url, level)
                    log.warning('第{}行参数缺失非必要参数"瓦片文件夹"，将使用默认值"{}".'.format(row + 1, tileFolder))
                else:
                    url_encodeStr = urlEncodeToFileName(url)
                    tileFolder = os.path.join(tileFolder, url_encodeStr, str(level))
                    if not os.path.exists(tileFolder):
                        os.makedirs(tileFolder)

                if imgFile == "":
                    imgFile = defaultImageFile(url, level)
                    log.warning('第{}行参数缺失非必要参数"输出影像文件"，将使用默认值"{}".'.format(row + 1, imgFile))

                self.crawlTilesThread.crawlAndMerge.emit(url, int(level), int(paras['origin_x']), int(paras['origin_y']),
                                                         float(paras['xmin']), float(paras['xmax']), float(paras['ymin']),
                                                         float(paras['ymax']), float(paras['resolution']), int(paras['tilesize']),
                                                         str(paras['pixelType']), bCompression, tileFolder, imgFile)
            elif self.rbtn_onlySpider.isChecked():
                if url not in self.paras:
                    log.error("{}地址错误".format(url))
                    continue

                paras = self.paras[url]['paras'][level]
                tileFolder_index = self.tbl_address.model().index(row, 2, QModelIndex())
                tileFolder = str(self.tbl_address.model().data(tileFolder_index, Qt.DisplayRole)).strip()
                if tileFolder == "":
                    tileFolder = defaultTileFolder(url, level)
                    log.warning('第{}行参数缺失非必要参数"瓦片文件夹"，将使用默认值"{}".'.format(row + 1, tileFolder))
                else:
                    url_encodeStr = urlEncodeToFileName(url)
                    tileFolder = os.path.join(tileFolder, url_encodeStr, str(level))
                    if not os.path.exists(tileFolder):
                        os.makedirs(tileFolder)

                self.crawlTilesThread.crawl.emit(url, int(level), int(paras['origin_x']), int(paras['origin_y']),
                                                 float(paras['xmin']), float(paras['xmax']), float(paras['ymin']),
                                                 float(paras['ymax']), float(paras['resolution']), int(paras['tilesize']), tileFolder)
            elif self.rbtn_onlyHandle.isChecked():
                key = url + "_" + level
                if key not in self.paras:
                    log.error("参数错误！")
                    continue

                paras = self.paras[key]
                imgFile_index = self.tbl_address.model().index(row, 1, QModelIndex())
                imgFile = str(self.tbl_address.model().data(imgFile_index, Qt.DisplayRole)).strip()
                if imgFile == "":
                    imgFile = defaultImageFile(url, level)
                    log.warning('第{}行参数缺失非必要参数"输出影像文件"，将使用默认值"{}".'.format(row + 1, imgFile))

                self.crawlTilesThread.merge.emit(url, int(paras['origin_x']), int(paras['origin_y']),
                                                 float(paras['xmin']), float(paras['xmax']), float(paras['ymin']),
                                                 float(paras['ymax']), float(paras['resolution']),
                                                 int(paras['tilesize']), str(paras['pixelType']), bCompression, imgFile)

    def check_paras(self):
        rows = range(0, self.tbl_address.model().rowCount(QModelIndex()))
        for row in rows:
            url_index, level_index, url, level = self.return_url_and_level(row)

            if self.rbtn_spiderAndHandle.isChecked() or self.rbtn_onlySpider.isChecked():
                if url == "":
                    log.error('第{}行缺失必要参数"地址"，请补全！'.format(row), dialog=True)
                    return False
                if level == "":
                    log.error('第{}行缺失必要参数"等级"，请补全！'.format(row), dialog=True)
                    return False

            elif self.rbtn_onlyHandle.isChecked():
                if url == "":
                    log.error('第{}行缺失必要参数"瓦片文件夹"，请补全！'.format(row), dialog=True)
                    return False
        return True


    def threadStop(self):
        self.thread.quit()

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
        log.setLogViewer(parent=self, logViewer=self.txt_log)
        if self.bInit:
            self.rbtn_spiderAndHandle.click()
            self.bInit = False

    def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
        self.table_layout()

    def splitterMoved(self):
        self.table_layout()

    def handleClicked(self):
        self.table_layout()

    def table_layout(self):
        if self.rbtn_onlyHandle.isChecked():
            self.tbl_address.setColumnWidth(0, self.tbl_address.width() / 2)
            self.tbl_address.setColumnWidth(1, self.tbl_address.width() / 2)
        elif self.rbtn_onlySpider.isChecked():
            self.tbl_address.setColumnWidth(0, self.tbl_address.width() * 0.4)
            self.tbl_address.setColumnWidth(1, self.tbl_address.width() * 0.2)
            self.tbl_address.setColumnWidth(2, self.tbl_address.width() * 0.4)
        elif self.rbtn_spiderAndHandle.isChecked():
            self.tbl_address.setColumnWidth(0, self.tbl_address.width() * 0.4)
            self.tbl_address.setColumnWidth(1, self.tbl_address.width() * 0.2)
            self.tbl_address.setColumnWidth(2, self.tbl_address.width() * 0.2)
            self.tbl_address.setColumnWidth(3, self.tbl_address.width() * 0.2)

    def return_url_and_level(self, logicRow):
        url_index = self.tbl_address.model().index(logicRow, self.url_no)
        level_index = self.tbl_address.model().index(logicRow, self.level_no)
        url = self.tbl_address.model().data(url_index, Qt.DisplayRole)
        level = self.tbl_address.model().data(level_index, Qt.DisplayRole)

        return url_index, level_index, url, level

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

    def btn_removeBtn_clicked(self):
        index_list = []
        selModel = self.tbl_address.selectionModel()
        if selModel is None:
            return
        if len(selModel.selectedRows()) < 1:
            return
        for model_index in selModel.selectedRows():
            index = QPersistentModelIndex(model_index)
            index_list.append(index)

        oldrow = index.row()
        for index in index_list:
            self.model.removeRows(index.row(), 1, 0)

        if self.model.rowCount(QModelIndex()) == 1:
            next_index = self.model.index(0, 0)
        else:
            next_index = self.model.index(oldrow, 0)
        # next_index = self.model.index(self.model.rowCount(QModelIndex()) - 1, 0)
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
            self.table_init_onlyHandle()
        else:
            self.txt_addressFile.setEnabled(True)
            self.btn_addressFile.setEnabled(True)

            self.txt_tileInfoFile.setEnabled(False)
            self.btn_tileInfoDialog.setEnabled(False)
            self.txt_tileInfoFile.clear()

            self.txt_originX.setEnabled(False)
            self.txt_originY.setEnabled(False)
            self.txt_resolution.setEnabled(False)
            self.txt_tilesize.setEnabled(False)

            self.txt_level.setEnabled(False)
            self.btn_obtainMeta.setEnabled(True)

            self.model.setHeaderData(0, Qt.Horizontal, "地址", Qt.DisplayRole)

            if self.rbtn_onlySpider.isChecked():
                self.table_init_onlySpider()
            elif self.rbtn_spiderAndHandle.isChecked():
                self.table_init_spiderAndHandle()

    def table_init_onlyHandle(self):
        self.txt_addressFile.setEnabled(False)
        self.btn_addressFile.setEnabled(False)
        self.txt_addressFile.clear()

        self.txt_tileInfoFile.setEnabled(True)
        self.btn_tileInfoDialog.setEnabled(True)

        self.txt_originX.setEnabled(True)
        self.txt_originY.setEnabled(True)
        self.txt_resolution.setEnabled(True)
        self.txt_tilesize.setEnabled(True)

        self.txt_level.setEnabled(False)
        self.btn_obtainMeta.setEnabled(False)

        self.model.setHeaderData(0, Qt.Horizontal, "输入瓦片文件夹", Qt.DisplayRole)
        # self.model.setHeaderData(1, Qt.Horizontal, "参数文件", Qt.DisplayRole)
        self.model.setHeaderData(1, Qt.Horizontal, "输出影像文件", Qt.DisplayRole)
        delegate = addressTableDelegate(self, [{'text': "请选择瓦片文件夹", 'type': "d"},
                                               {'text': "请选择或创建影像文件", 'type': "f"}])
        self.tbl_address.setModel(self.model)
        self.tbl_address.setItemDelegate(delegate)
        self.tbl_address.setColumnWidth(0, self.tbl_address.width() / 2)
        self.tbl_address.setColumnWidth(1, self.tbl_address.width() / 2)

        self.paras = {}

        self.cb_compression.setEnabled(True)

    def table_init_onlySpider(self):
        self.model.setHeaderData(1, Qt.Horizontal, "等级", Qt.DisplayRole)
        self.model.setHeaderData(2, Qt.Horizontal, "瓦片文件夹", Qt.DisplayRole)

        delegate = addressTableDelegate(self, [None, {'type': 'c'},
                                               {'text': "请选择输出瓦片文件夹", 'type': "d"}])
        self.tbl_address.setModel(self.model)
        self.tbl_address.setItemDelegate(delegate)
        self.tbl_address.setColumnWidth(0, self.tbl_address.width() * 0.4)
        self.tbl_address.setColumnWidth(1, self.tbl_address.width() * 0.2)
        self.tbl_address.setColumnWidth(2, self.tbl_address.width() * 0.4)

        self.cb_compression.setEnabled(False)

    def table_init_spiderAndHandle(self):
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

        self.cb_compression.setEnabled(True)

        self.paras = {}

    @Slot()
    def open_addressFile(self):
        fileName, fileType = QtWidgets.QFileDialog.getOpenFileName(self, "选择影像服务参数文件", os.getcwd(),
                                                                   "All Files(*)")
        self.txt_addressFile.setText(fileName)

        if fileName == "":
            return

        try:
            with open(fileName, 'r', encoding='utf-8') as f:
                self.paras = json.load(f)

            self.add_address_rows_from_paras()
        except:
            if self.model.rowCount(QModelIndex()) > 0:
                self.model.removeRows(self.model.rowCount(QModelIndex()) - 1, 1, QModelIndex())
            log.error("读取参数文件失败！", dialog=True)

    def add_address_rows_from_paras(self):
        for kv in self.paras.items():
            url = kv[0]
            v = kv[1]
            imp = v['exports']
            levels = v['levels']

            for i in range(len(imp)):
                row = self.model.rowCount(QModelIndex())
                self.model.addEmptyRow(self.model.rowCount(QModelIndex()), 1, 0)

                url_index = self.tbl_address.model().index(row, self.url_no)
                level_index = self.tbl_address.model().index(row, self.level_no)
                self.tbl_address.model().setData(url_index, url)
                if imp[i]['level'] == -1:
                    self.tbl_address.model().setData(level_index, "")
                else:
                    self.tbl_address.model().setData(level_index, imp[i]['level'])
                self.tbl_address.model().setData(self.tbl_address.model().index(row, 2), imp[i]['tileFolder'])

                if self.rbtn_spiderAndHandle.isChecked():
                    self.tbl_address.model().setData(self.tbl_address.model().index(row, 3), imp[i]['imageFile'])

                editor_delegate = self.tbl_address.itemDelegate(level_index)
                if isinstance(editor_delegate, addressTableDelegate):
                    # self.model.setLevelData(level_index, levels)
                    self.model.setLevelData(url, levels)

    @Slot()
    def open_tileInfoFile(self):
        fileName, fileType = QtWidgets.QFileDialog.getOpenFileName(self, "选择瓦片参数文件", os.getcwd(),
                                                                   "All Files(*)")
        self.txt_tileInfoFile.setText(fileName)

        if fileName == "":
            return

        try:
            with open(fileName, 'r') as f:
                self.paras = json.load(f)

                for kv in self.paras.items():
                    imp = kv[1]

                    row = self.model.rowCount(QModelIndex())
                    self.model.addEmptyRow(self.model.rowCount(QModelIndex()), 1, 0)

                    if 'tileFolder' not in imp:
                        self.tbl_address.model().setData(self.tbl_address.model().index(row, 0), "")
                    else:
                        self.tbl_address.model().setData(self.tbl_address.model().index(row, 0), imp['tileFolder'])

                    if 'imageFile' not in imp:
                        self.tbl_address.model().setData(self.tbl_address.model().index(row, 1), "")
                    else:
                        self.tbl_address.model().setData(self.tbl_address.model().index(row, 1), imp['imageFile'])
        except:
            log.error("读取参数文件失败！", dialog=True)

    @Slot()
    def btn_obtainMeta_clicked(self):
        selModel = self.tbl_address.selectionModel()

        if selModel is None:
            return

        indexes = selModel.selectedIndexes()

        if self.rbtn_onlyHandle.isChecked():
            return

        ## 如果有被选中的行，则只获取被选中行的信息
        if len(indexes) > 0:
            rows = sorted(set(index.row() for index in
                              self.tbl_address.selectedIndexes()))
        else:
            rows = range(0, self.tbl_address.model().rowCount(QModelIndex()))

        for row in rows:
            url_index, level_index, url, level = self.return_url_and_level(row)
            editor_delegate = self.tbl_address.itemDelegate(level_index)

            url = str(self.tbl_address.model().data(url_index, Qt.DisplayRole)).strip()

            if url == "": continue

            # if url not in self.paras.keys():
            getInfo = get_paraInfo(url)
            if getInfo is None:
                log.error(url + "无法获取远程参数信息，请检查地址是否正确以及网络是否连通！")
                continue
            else:
                log.info(url + "参数信息获取成功！")

            self.setParaToMemory(url, getInfo)

            levels = self.paras[url]['levels']

            if isinstance(editor_delegate, addressTableDelegate):
                # self.model.setLevelData(level_index, levels)
                self.model.setLevelData(url, levels)

    def setParaToMemory(self, url, getInfo):
        levels = []
        resolutions = []
        lods = []
        origin_x = origin_y = xmin = xmax = ymin = ymax = resolution = tilesize = level = pixelType = ""

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

        if 'pixelType' in getInfo.keys():
            pixelType = getInfo['pixelType']

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
                    'pixelType': pixelType
                }

        url_encodeStr = urlEncodeToFileName(url)
        self.paras[url] = {
            'code': url_encodeStr,
            'levels': levels,
            'paras': paras
        }

    def update_para_dict(self):
        pixelType_key = list(filter(lambda k: pixelType_dict[k] == self.cmb_pixelType.currentText(), pixelType_dict.keys()))[0]

        dict = {
            "origin_x": self.txt_originX.text(),
            "origin_y": self.txt_originY.text(),
            "xmin": self.txt_xmin.text(),
            "xmax": self.txt_xmax.text(),
            "ymin": self.txt_ymin.text(),
            "ymax": self.txt_ymax.text(),
            "tilesize": self.txt_tilesize.text(),
            "resolution": self.txt_resolution.text(),
            "pixelType": pixelType_key
        }
        return dict

    def update_txt_info(self, index: QModelIndex, level=-1):
        # print([index.row(), index.column()])
        key1_index, key2_index, key1, key2 = self.return_url_and_level(index.row())
        # key1_index = self.tbl_address.model().index(index.row(), 0)
        # key1 = self.tbl_address.model().data(key1_index, Qt.DisplayRole)
        # key2_index = self.tbl_address.model().index(index.row(), 1)
        # key2 = self.tbl_address.model().data(key2_index, Qt.DisplayRole)

        self.txt_level.setText("")
        self.txt_originX.setText("")
        self.txt_originY.setText("")
        self.txt_xmin.setText("")
        self.txt_xmax.setText("")
        self.txt_ymin.setText("")
        self.txt_ymax.setText("")
        self.txt_tilesize.setText("")
        self.txt_resolution.setText("")

        bUpdate = False
        if self.rbtn_spiderAndHandle.isChecked() or self.rbtn_onlySpider.isChecked():
            if key1 not in self.paras:
                return

            if level in self.paras[key1]['paras']:
                getInfo = self.paras[key1]['paras'][level]
                self.txt_level.setText(str(level))
                bUpdate = True
        else:
            key = key1 + "_" + key2
            if key in self.paras:
                getInfo = self.paras[key]
                bUpdate = True
            else:
                bUpdate = False

        if bUpdate:
            if 'origin_x' in getInfo:
                self.txt_originX.setText(str(getInfo['origin_x']))
                self.txt_originX.home(False)
            if 'origin_y' in getInfo:
                self.txt_originY.setText(str(getInfo['origin_y']))
                self.txt_originY.home(False)
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
            if 'tilesize' in getInfo:
                self.txt_tilesize.setText(str(getInfo['tilesize']))
                self.txt_tilesize.home(False)
            if 'resolution' in getInfo:
                self.txt_resolution.setText(str(getInfo['resolution']))
                self.txt_resolution.home(False)
            if 'pixelType' in getInfo:
                if isinstance(getInfo['pixelType'], list):
                    k = getInfo['pixelType'][0]
                else:
                    k = getInfo['pixelType']
                if k in pixelType_dict:
                    self.cmb_pixelType.setCurrentText(pixelType_dict[k])


if __name__ == '__main__':
    app = QApplication(sys.argv)
    style = QStyleFactory.create("windows")
    app.setStyle(style)
    window = Ui_Window()
    window.setWindowFlags(Qt.Window)
    window.show()
    sys.exit(app.exec_())
