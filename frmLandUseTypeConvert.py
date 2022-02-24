import csv
import os
import sys

import pyperclip
from PyQt5.QtWidgets import QDialogButtonBox, QAbstractButton, QMessageBox, QApplication, QStyleFactory, QFileDialog, \
    QAbstractItemView, QTableWidget, QHeaderView, QTableWidgetItem
from openpyxl import load_workbook

from UI.UILandUseTypeConvert import Ui_Dialog
from PyQt5.QtCore import Qt, QModelIndex, QEvent
from PyQt5 import QtWidgets, QtGui, QtCore

from UICore.DataFactory import workspaceFactory, read_table_header
from UICore.Gv import SplitterState, Dock, DataType
from UICore.common import get_suffix
from UICore.log4p import Log
from widgets.FileDialog import FileDialog
import UI.listview_dialog

Slot = QtCore.pyqtSlot

log = Log(__name__)


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

        # self.paras = {}  # 存储参数信息
        # self.selIndex = QModelIndex()
        # self.table_init()

        log.setLogViewer(parent=self, logViewer=self.txt_log)
        self.txt_log.setReadOnly(True)

        self.buttonBox.clicked.connect(self.buttonBox_clicked)
        self.btn_addressLayerFile.clicked.connect(self.btn_addressLayerFile_clicked)
        self.btn_addressConfigFile.clicked.connect(self.btn_addressConfigFile_clicked)
        # self.tableWidget.viewport().installEventFilter(self)
        self.tableWidget.installEventFilter(self)
        # self.splitter.splitterMoved.connect(self.splitterMoved)
        # self.splitter.handle(1).handleClicked.connect(self.handleClicked)

        self.splitter.setupUi()
        self.bInit = True

    def showEvent(self, a0: QtGui.QShowEvent) -> None:
        log.setLogViewer(parent=self, logViewer=self.txt_log)
        if self.bInit:
            self.rbtn_file.click()
            self.bInit = False

    @Slot(QAbstractButton)
    def buttonBox_clicked(self, button: QAbstractButton):
        QMessageBox.information(self, "测试", "测试", QMessageBox.Ok)

    @Slot()
    def btn_addressLayerFile_clicked(self):
        # _f_dlg = FileDialog()
        # _f_dlg.exec_()
        if self.rbtn_file.isChecked():
            fileName, fileType = QtWidgets.QFileDialog.getOpenFileName(
                self, "选择待转换矢量图层文件", os.getcwd(),
                "ESRI Shapefile(*.shp)")

            if len(fileName) == 0:
                return

            fileType = get_suffix(fileName)

            if fileType == DataType.shapefile:
                wks = workspaceFactory().get_factory(DataType.shapefile)
                datasource = wks.openFromFile(fileName)
            else:
                log.error("不识别的图形文件格式!", dialog=True)
                return None

            if datasource is None:
                # layer_name = wks.getLayerNames()[0]
                # in_layer = datasource.GetLayer()

                # datasource.Release()
                # datasource = None
                # in_layer = None
                log.error("无法读取shp文件!{}".format(fileName), dialog=True)
                return None
        elif self.rbtn_filedb.isChecked():
            fileName = QtWidgets.QFileDialog.getExistingDirectory(self, "选择需要转换的GDB数据库",
                                                                  os.getcwd(), QFileDialog.ShowDirsOnly)
            wks = workspaceFactory().get_factory(DataType.fileGDB)
            datasource = wks.openFromFile(fileName)

            if datasource is not None:
                lst_names = wks.getLayerNames()
                selected_name = None
                if len(lst_names) > 1:
                    selected_name = nameListDialog().openListDialog("请选择要转换的图层", lst_names)
                elif len(lst_names) == 1:
                    selected_name = [lst_names[0]]

                # layer = wks.openLayer(selected_name[0])
                log.warning(selected_name[0], dialog=True)
            else:
                log.error("无法读取文件数据库!{}".format(fileName), dialog=True)
                return None

    @Slot()
    def btn_addressConfigFile_clicked(self):
        fileName, types = QFileDialog.getOpenFileName(
            self, "选择土地类型转换规则表文件", os.getcwd(),
            "表格文件(*.csv *.xlsx);;csv文件(*.csv);;excel文件(*.xlsx)")

        if len(fileName) == 0:
            return

        fileType = get_suffix(fileName)

        if fileType != DataType.xlsx and fileType != DataType.csv:
            log.error("不识别的图形文件格式!", dialog=True)
            return None

        header, DLBM_values, all_data = self.read_config_table(fileName, fileType)

        DLBM_index = self.check_header(header)
        if DLBM_index > -1:
            if self.check_field_DLBM(DLBM_values):
                self.add_all_data_to_tablewidget(DLBM_index, all_data)
                rel_tables = self.generate_config_rel(DLBM_index, all_data)

    def eventFilter(self, source: 'QObject', event: 'QEvent') -> bool:
        if source is self.tableWidget and event.type() == QEvent.KeyPress:
            if event.modifiers() == Qt.ControlModifier:
                if event.key() == Qt.Key_V:
                    file = pyperclip.paste()
                    header, DLBM_values, all_data = self.read_config_table(file, fileType=DataType.memory)

                    DLBM_index = self.check_header(header)
                    if DLBM_index > -1:
                        if self.check_field_DLBM(DLBM_values):
                            self.add_all_data_to_tablewidget(DLBM_index, all_data)
                            rel_tables = self.generate_config_rel(DLBM_index, all_data)
        # if source is self.tableWidget.viewport():
        #     print(event.type())
        # # if source is self.tableWidget.viewport() and event.type() == QEvent.MouseButtonPress:
        # #     print(event.type())
        # if source is self.tableWidget.viewport() and event.type() == QtCore.QEvent.KeyPress:
        #     print(event.type())
        #     if event.modifiers() == Qt.ControlModifier:
        #         print(event.text())

        return super().eventFilter(source, event)

    #  在表格控件中显示读取的规则配置表数据
    def add_all_data_to_tablewidget(self, DLBM_index, all_data):
        col_num = len(all_data[0])
        row_num = len(all_data)

        self.tableWidget.setColumnCount(col_num)
        self.tableWidget.setRowCount(row_num - 1)
        self.tableWidget.setHorizontalHeaderLabels(all_data[0])
        self.tableWidget.horizontalHeader().setSectionsMovable(False)

        # 按行加载数据
        irow = 0
        for row_value in all_data:
            if irow == 0:
                irow += 1
                continue

            for icol in range(len(row_value)):
                newItem = QTableWidgetItem(row_value[icol])
                if icol == DLBM_index:
                    newItem.setFlags(QtCore.Qt.ItemIsEnabled)
                self.tableWidget.setItem(irow - 1, icol, newItem)

            irow += 1

        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents) # 首先根据resizetocontents自动计算合适的列宽

        # 首先根据resizetocontents自动计算合适的列宽，然后自动调整窗口大小，最后将列宽设置为可调整
        resize_width = 0
        for i in range(self.tableWidget.columnCount()):
            resize_width = resize_width + self.tableWidget.columnWidth(i)

        if self.splitter.splitterState == SplitterState.collapsed:
            init_width = self.tableWidget.width()
            resize_width = self.width() + (resize_width - init_width)
            self.resize(resize_width + 40, self.height())
        else:
            init_width = self.splitter.widget(0).width()
            resize_width2 = self.splitter.width() + (resize_width - init_width)
            self.resize(resize_width2, self.height())
            self.splitter.setSizes([resize_width, self.splitter.width() - resize_width - 30])

        self.tableWidget.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)  # 行高固定
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

    def read_config_table(self, file, fileType):
            all_data = []
            not_none_index = []
            DLBM_values = []
            DLBM_index = -1
            header = None

            if fileType == DataType.xlsx:
                wb = load_workbook(file, read_only=True)

                selected_sheet = []

                lst_names = wb.sheetnames
                if len(lst_names) > 1:
                    selected_sheet = nameListDialog().openListDialog(
                        "请选择工作表(sheet)", lst_names, QAbstractItemView.SingleSelection)
                    selected_sheet = selected_sheet[0]
                elif len(lst_names) == 1:
                    selected_sheet = lst_names[0]

                all_values = list(wb[selected_sheet].values)

                header, bheader = read_table_header(file, fileType, supplyment=False, sheet=selected_sheet)

                # 表头非空的列才计入规则表
                for i in range(len(header)):
                    if header[i] != 'None':
                        not_none_index.append(i)
                    if header[i].upper() == 'DLBM':
                        DLBM_index = i

                for row_values in all_values:
                    row_values_filter = []
                    for i in range(len(row_values)):
                        if i in not_none_index:
                            row_values_filter.append(row_values[i])
                        if i == DLBM_index:
                            DLBM_values.append(row_values[i])

                    all_data.append(row_values_filter)

                wb.close()

            elif fileType == DataType.csv:
                header, encoding, bheader = read_table_header(file, fileType, supplyment=False, sheet=None)
                for i in range(len(header)):
                    if header[i] != '':
                        not_none_index.append(i)
                    if header[i].upper() == 'DLBM':
                        DLBM_index = i

                with open(file, 'r', newline='', encoding=encoding) as f:
                    reader = csv.reader(f)
                    for row in reader:
                        row_values_filter = []
                        for i in range(len(row)):
                            if i in not_none_index:
                                row_values_filter.append(row[i])
                            if i == DLBM_index:
                                DLBM_values.append(row[i])

                        all_data.append(row_values_filter)

            elif fileType == DataType.memory:
                header, bheader = read_table_header(file, fileType, supplyment=False, sheet=None)
                for i in range(len(header)):
                    if header[i] != '':
                        not_none_index.append(i)
                    if header[i].upper() == 'DLBM':
                        DLBM_index = i

                for line in file.splitlines():
                    row = line.split('\t')
                    row_values_filter = []
                    for i in range(len(row)):
                        if i in not_none_index:
                            row_values_filter.append(row[i])
                        if i == DLBM_index:
                            DLBM_values.append(row[i])

                    all_data.append(row_values_filter)

            return header, DLBM_values, all_data

    # 检查表头和数据的合法性
    def check_header(self, header):
        DLBM_index = -1
        not_none = []
        for i in header:
            if i != '':
                not_none.append(i)

        for i in range(len(not_none)):
            if not_none[i].upper() == 'DLBM':
                DLBM_index = i
                break

        if DLBM_index == -1:
            log.error("规则表不存在必要字段DLBM，请检查!", dialog=True)
        if len(not_none) <= DLBM_index:
            log.error("DLBM列右边缺少需要匹配的列，请检查!", dialog=True)

        return DLBM_index

    def check_field_DLBM(self, DLBM):
        set_headers = set(DLBM)
        if len(set_headers) != len(DLBM):
            log.error("规则表DLBM字段不允许出现重复值，请检查!", dialog=True)
            return False
        return True

    # 生成对应规则字典, DLBM列是唯一KEY,右边的列都是VALUE
    def generate_config_rel(self, DLBM_INDEX, all_data):
        header = all_data[0]
        rel_tables = []  # 存储所有的规则关系字典

        for icol in range(DLBM_INDEX + 1, len(header)):
            iFirst = 0
            rel = {}

            for row_value in all_data:
                if iFirst == 0:
                    iFirst += 1
                    continue
                rel[row_value[DLBM_INDEX]] = row_value[icol]

            rel_tables.append(rel)

        return rel_tables


class nameListDialog(QtWidgets.QDialog, UI.listview_dialog.Ui_Dialog):
    def __init__(self):
        super(nameListDialog, self).__init__()
        self.setupUi(self)
        self.pushButton.clicked.connect(self.pushButton_clicked)
        self.select_names = []

    def openListDialog(self, title, lst_names, selectMode=QAbstractItemView.SingleSelection):
        self.lv_name.setSelectionMode(selectMode)
        self.setWindowTitle(title)

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
    window = Ui_Window()
    window.setWindowFlags(Qt.Window)
    window.show()
    sys.exit(app.exec_())
