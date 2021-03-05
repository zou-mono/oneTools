from PyQt5.QtCore import QRect, Qt, QPersistentModelIndex, QItemSelectionModel, QModelIndex
from PyQt5.QtGui import QDoubleValidator, QIntValidator, QPalette
from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox, QErrorMessage, QDialogButtonBox, QStyleFactory, \
    QAbstractItemView
from PyQt5 import QtWidgets, QtGui
from UI.UITileMap import Ui_Dialog
from suplicmap_tilemap import get_json
import sys
import json
import os
from UICore.Gv import SplitterState, Dock
from widgets.mTable import TableModel, mTableStyle


class Ui_Window(QtWidgets.QDialog, Ui_Dialog):
    def __init__(self):
        super(Ui_Window, self).__init__()
        self.setupUi(self)
        self.table_init()

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
        vlayout.setContentsMargins(20, 15, 20, 15)
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
        self.btn_tilesDialog.clicked.connect(self.open_tileFolder)
        self.btn_infoDialog.clicked.connect(self.open_tileInfoFile)
        self.btn_addressFile.clicked.connect(self.open_addressFile)

        self.rbtn_onlySpider.toggled.connect(lambda: self.rbtn_toggled(self.rbtn_onlySpider))
        self.rbtn_onlyHandle.toggled.connect(lambda: self.rbtn_toggled(self.rbtn_onlyHandle))
        self.rbtn_spiderAndHandle.toggled.connect(lambda: self.rbtn_toggled(self.rbtn_spiderAndHandle))

        self.rbtn_spiderAndHandle.setChecked(True)

    def table_init(self):
        self.tbl_address.setStyle(mTableStyle())

        self.tbl_address.horizontalHeader().setStretchLastSection(True)
        self.tbl_address.verticalHeader().setDefaultSectionSize(20)
        color = self.palette().color(QPalette.Button)
        self.tbl_address.horizontalHeader().setStyleSheet("QHeaderView::section {{ background-color: {}}}".format(color.name()))
        self.tbl_address.verticalHeader().setStyleSheet("QHeaderView::section {{ background-color: {}}}".format(color.name()))
        self.tbl_address.setStyleSheet("QTableCornerButton::section {{ color: {}; border: 1px solid; border-color: {}}}".format(color.name(), color.name()))

        self.tbl_address.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tbl_address.setEditTriggers(QAbstractItemView.SelectedClicked)
        self.tbl_address.DragDropMode(QAbstractItemView.InternalMove)
        self.tbl_address.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_address.setDefaultDropAction(Qt.MoveAction)

        self.tbl_address.horizontalHeader().setSectionsMovable(True)
        self.tbl_address.setDragEnabled(True)
        self.tbl_address.setAcceptDrops(True)

        self.model = TableModel()
        self.model.setHeaderData(0, Qt.Horizontal, "服务名", Qt.DisplayRole)
        self.model.setHeaderData(1, Qt.Horizontal, "地址", Qt.DisplayRole)
        self.tbl_address.setModel(self.model)

    def btn_addRow_Clicked(self):
        selModel = self.tbl_address.selectionModel()
        if len(selModel.selectedIndexes()) == 0:
            self.model.addEmptyRow(self.model.rowCount(QModelIndex()), 1, 0)
            next_index = self.model.index(self.model.rowCount(QModelIndex()) - 1, 0)
        elif len(selModel.selectedRows()) == 1:
            next_row = selModel.selectedRows()[0].row() + 1
            self.model.addEmptyRow(next_row, 1, 0)
            next_index = self.model.index(next_row, 0)

        self.tbl_address.selectionModel().select(next_index,
                                                 QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)
        self.tbl_address.setFocus()

    def removeBtn_clicked(self):
        # rows = sorted(set(index.row() for index in
        #                   self.tableView.selectedIndexes()), sereverse=True)

        index_list = []
        for model_index in self.tableView.selectionModel().selectedRows():
            index = QPersistentModelIndex(model_index)
            index_list.append(index)

        for index in index_list:
            self.tableView.model().removeRows(index.row(), 1, 0)

        next_index = self.tableView.model().index(self.tableView.model().rowCount(QModelIndex()) - 1, 0)
        # self.tableView.setCurrentIndex(next_index)
        self.tbl_address.selectionModel().select(next_index, QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)
        self.tbl_address.setFocus()

    def validateValue(self):
        doubleValidator = QDoubleValidator()
        doubleValidator.setNotation(QDoubleValidator.StandardNotation)
        self.txt_xmin.setValidator(doubleValidator)
        self.txt_xmax.setValidator(doubleValidator)
        self.txt_ymin.setValidator(doubleValidator)
        self.txt_ymax.setValidator(doubleValidator)
        self.txt_tilesize.setValidator(doubleValidator)
        self.txt_resolution.setValidator(doubleValidator)

    def rbtn_toggled(self, btn):
        if self.rbtn_onlyHandle.isChecked():
            self.txt_addressFile.setEnabled(False)
            self.btn_addressFile.setEnabled(False)
            self.tbl_address.setEnabled(False)
            self.btn_addRow.setEnabled(False)
            self.btn_removeRow.setEnabled(False)

            self.txt_infoPath.setEnabled(True)
            self.btn_infoDialog.setEnabled(True)
            self.txt_imageFolderPath.setEnabled(True)
            self.btn_tilesDialog.setEnabled(True)
        else:
            self.txt_addressFile.setEnabled(True)
            self.btn_addressFile.setEnabled(True)
            self.tbl_address.setEnabled(True)
            self.btn_addRow.setEnabled(True)
            self.btn_removeRow.setEnabled(True)

            self.txt_infoPath.setEnabled(False)
            self.btn_infoDialog.setEnabled(False)
            self.txt_imageFolderPath.setEnabled(False)
            self.btn_tilesDialog.setEnabled(False)

    def open_addressFile(self):
        fileName, fileType = QtWidgets.QFileDialog.getOpenFileName(self, "选择服务地址文件", os.getcwd(),
                                                                   "All Files(*)")
        self.txt_addressFile.setText(fileName)

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