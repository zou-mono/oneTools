from PyQt5.QtCore import QRect, Qt, QPersistentModelIndex, QItemSelectionModel, QModelIndex
from PyQt5.QtGui import QDoubleValidator, QIntValidator, QPalette
from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox, QErrorMessage, QDialogButtonBox, QStyleFactory, \
    QAbstractItemView, QHeaderView, QComboBox
from PyQt5 import QtWidgets, QtGui
from UI.UITileMap import Ui_Dialog
from suplicmap_tilemap import get_json
import sys
import json
import os
from UICore.Gv import SplitterState, Dock
from widgets.mTable import TableModel, mTableStyle, addressTableDelegate


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

        self.cmb_level.currentIndexChanged.connect(self.cmb_selectionchange)
        self.btn_addRow.clicked.connect(self.btn_addRow_Clicked)
        self.btn_addressFile.clicked.connect(self.open_addressFile)
        self.btn_removeRow.clicked.connect(self.removeBtn_clicked)

        self.rbtn_onlySpider.clicked.connect(self.rbtn_toggled)
        self.rbtn_onlyHandle.clicked.connect(self.rbtn_toggled)
        self.rbtn_spiderAndHandle.clicked.connect(self.rbtn_toggled)
        self.tbl_address.verticalHeader().sectionClicked.connect(self.table_section_clicked)
        self.btn_obtainMeta.clicked.connect(self.btn_obtainMeta_clicked)

        self.table_init()

    def table_init(self):
        self.tbl_address.setStyle(mTableStyle())

        self.tbl_address.horizontalHeader().setStretchLastSection(True)
        self.tbl_address.verticalHeader().setDefaultSectionSize(20)
        self.tbl_address.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)  # 行高固定

        color = self.palette().color(QPalette.Button)
        self.tbl_address.horizontalHeader().setStyleSheet("QHeaderView::section {{ background-color: {}}}".format(color.name()))
        self.tbl_address.verticalHeader().setStyleSheet("QHeaderView::section {{ background-color: {}}}".format(color.name()))
        self.tbl_address.setStyleSheet("QTableCornerButton::section {{ color: {}; border: 1px solid; border-color: {}}}".format(color.name(), color.name()))

        self.tbl_address.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tbl_address.setEditTriggers(QAbstractItemView.SelectedClicked | QAbstractItemView.DoubleClicked)
        self.tbl_address.DragDropMode(QAbstractItemView.InternalMove)
        self.tbl_address.setSelectionBehavior(QAbstractItemView.SelectRows | QAbstractItemView.SelectItems)
        self.tbl_address.setDefaultDropAction(Qt.MoveAction)

        self.tbl_address.horizontalHeader().setSectionsMovable(False)
        self.tbl_address.setDragEnabled(True)
        self.tbl_address.setAcceptDrops(True)

        # self.rbtn_spiderAndHandle.setChecked(True)

    # def showEvent(self, a0: QtGui.QShowEvent) -> None:
        # self.rbtn_spiderAndHandle.click()
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

    def rbtn_toggled(self, btn):
        self.model = TableModel()

        if self.rbtn_onlyHandle.isChecked():
            self.txt_addressFile.setEnabled(False)
            self.btn_addressFile.setEnabled(False)

            self.txt_tileInfoFile.setEnabled(True)
            self.btn_tileInfoDialog.setEnabled(True)

            self.model.setHeaderData(0, Qt.Horizontal, "瓦片文件夹", Qt.DisplayRole)
            self.model.setHeaderData(1, Qt.Horizontal, "参数文件", Qt.DisplayRole)
            self.model.setHeaderData(2, Qt.Horizontal, "影像文件", Qt.DisplayRole)
            delegate = addressTableDelegate(self, [{'text': "请选择瓦片文件夹", 'type': "d"},
                                                   {'text': "请选择瓦片信息文件", 'type': "f"},
                                                   {'text': "请选择输出影像文件", 'type': "f"}])
            self.tbl_address.setModel(self.model)
            self.tbl_address.setItemDelegate(delegate)
            self.tbl_address.setColumnWidth(0, self.tbl_address.width()/3)
            self.tbl_address.setColumnWidth(1, self.tbl_address.width()/3)
            self.tbl_address.setColumnWidth(2, self.tbl_address.width()/3)
        else:
            self.txt_addressFile.setEnabled(True)
            self.btn_addressFile.setEnabled(True)

            self.txt_tileInfoFile.setEnabled(False)
            self.btn_tileInfoDialog.setEnabled(False)

            self.model.setHeaderData(0, Qt.Horizontal, "ID", Qt.DisplayRole)
            self.model.setHeaderData(1, Qt.Horizontal, "地址", Qt.DisplayRole)

            if self.rbtn_onlySpider.isChecked():
                self.model.setHeaderData(2, Qt.Horizontal, "等级", Qt.DisplayRole)
                self.model.setHeaderData(3, Qt.Horizontal, "瓦片文件夹", Qt.DisplayRole)

                delegate = addressTableDelegate(self, [None, None, {'type': 'c'},
                                                       {'text': "请选择输出瓦片文件夹", 'type': "d"}])
                self.tbl_address.setModel(self.model)
                self.tbl_address.setItemDelegate(delegate)
                self.tbl_address.setColumnWidth(0, self.tbl_address.width() * 0.1)
                self.tbl_address.setColumnWidth(1, self.tbl_address.width() * 0.3)
                self.tbl_address.setColumnWidth(2, self.tbl_address.width() * 0.3)
                self.tbl_address.setColumnWidth(3, self.tbl_address.width() * 0.3)

            elif self.rbtn_spiderAndHandle.isChecked():
                self.model.setHeaderData(2, Qt.Horizontal, "等级", Qt.DisplayRole)
                self.model.setHeaderData(3, Qt.Horizontal, "瓦片文件夹", Qt.DisplayRole)
                self.model.setHeaderData(4, Qt.Horizontal, "影像文件", Qt.DisplayRole)

                delegate = addressTableDelegate(self, [None, None,{'type': 'c'},
                                                       {'text': "请选择输出瓦片文件夹", 'type': "d"},
                                                       {'text': "请选择输出影像文件", 'type': "f"}])
                self.tbl_address.setModel(self.model)
                self.tbl_address.setItemDelegate(delegate)
                self.tbl_address.setColumnWidth(0, self.tbl_address.width() * 0.1)
                self.tbl_address.setColumnWidth(1, self.tbl_address.width() * 0.3)
                self.tbl_address.setColumnWidth(2, self.tbl_address.width() * 0.2)
                self.tbl_address.setColumnWidth(3, self.tbl_address.width() * 0.2)
                self.tbl_address.setColumnWidth(4, self.tbl_address.width() * 0.2)

    def table_section_clicked(self, index):
        print("clicked:{}".format(index))

    def open_addressFile(self):
        fileName, fileType = QtWidgets.QFileDialog.getOpenFileName(self, "选择服务地址文件", os.getcwd(),
                                                                   "All Files(*)")
        self.txt_addressFile.setText(fileName)

    def btn_obtainMeta_clicked(self):
        selModel = self.tbl_address.selectionModel()

        print([self.tbl_address.currentIndex().row(), self.tbl_address.currentIndex().column()])

        indexes = selModel.selectedIndexes()
        level_no = 2  # 等级字段的序号

        if self.rbtn_onlyHandle.isChecked():
            return

        colCount = len(self.tbl_address.model().headers)

        ## 如果有被选中的行，则只获取被选中行的信息
        if len(indexes) > 0:
            rows = sorted(set(index.row() for index in
                              self.tbl_address.selectedIndexes()))
            rows = range(0, len(rows))
            for row in rows:
                index = indexes[colCount * row + level_no]
                editor_delegate = self.tbl_address.itemDelegate(index)
                if isinstance(editor_delegate, addressTableDelegate):
                    self.tbl_address.model().setData(index, [1,2,3,4])
        else:
            rows = range(0, self.tbl_address.model().rowCount(QModelIndex()))
            for row in rows:
                index = self.tbl_address.model().index(row, level_no, QModelIndex())
                editor_delegate = self.tbl_address.itemDelegate(index)

                if isinstance(editor_delegate, addressTableDelegate):
                    self.tbl_address.model().setData(index, [1,2,3,4])

    def btn_obtain_clicked(self):
        self.cmb_level.clear()
        if self.txt_address.toPlainText() == "":
            msg_box = QMessageBox(QMessageBox.Critical, '错误', '地址不能为空!')
            msg_box.exec()
        else:
            # 测试
            with open("data/tile_Info.json", 'r') as j:
                self.getInfo = json.load(j)

            self.txt_originX.setText(str(self.getInfo['tileInfo']['origin']['x']))
            self.txt_originY.setText(str(self.getInfo['tileInfo']['origin']['y']))
            self.lods = self.getInfo['tileInfo']['lods']
            for lod in self.lods:
                self.cmb_level.addItem("level {}".format(lod["level"]))
            # self.update_txt_info(0)

    def update_txt_info(self, i):
        self.url = self.txt_address.toPlainText()

        self.txt_xmin.setText(str(self.getInfo['extent']['xmin']))
        self.txt_xmax.setText(str(self.getInfo['extent']['xmax']))
        self.txt_ymin.setText(str(self.getInfo['extent']['ymin']))
        self.txt_ymax.setText(str(self.getInfo['extent']['ymax']))

        self.txt_tilesize.setText(str(self.getInfo['tileInfo']['rows']))
        # self.resolution = lod['resolution']
        self.txt_resolution.setText(str(self.lods[i]['resolution']))

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