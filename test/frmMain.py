from PyQt5.QtCore import QRect, Qt
from PyQt5.QtGui import QDoubleValidator, QIntValidator
from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox, QErrorMessage, QDialogButtonBox, QStyleFactory
from PyQt5 import QtWidgets, QtGui
from frmUI import Ui_Dialog
from suplicmap_tilemap import get_json
import sys
import json
import os
from UICore.Gv import SplitterState, Dock
from widgets.CollapsibleSplitter import CollapsibleSplitter
from test.frmUI import Ui_Dialog

class Ui_Window(QtWidgets.QDialog, Ui_Dialog):
    def __init__(self):
        super(Ui_Window, self).__init__()
        self.setupUi(self)
        self.setFixedWidth(self.width() + 5)
        self.frame.setFixedHeight(self.frame.height() + 90)

        self.txt_address.setText(
            "http://suplicmap.pnr.sz/tileszmap_1/rest/services/SZIMAGE/SZAVI2019_20ZWDL/ImageServer")

        doubleValidator = QDoubleValidator()
        doubleValidator.setNotation(QDoubleValidator.StandardNotation)
        self.txt_xmin.setValidator(doubleValidator)
        self.txt_xmax.setValidator(doubleValidator)
        self.txt_ymin.setValidator(doubleValidator)
        self.txt_ymax.setValidator(doubleValidator)
        self.txt_tilesize.setValidator(doubleValidator)
        self.txt_resolution.setValidator(doubleValidator)

        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.button(QDialogButtonBox.Ok).setFont(font)
        self.buttonBox.button(QDialogButtonBox.Ok).setText("确定")
        self.buttonBox.button(QDialogButtonBox.Cancel).setFont(font)
        self.buttonBox.button(QDialogButtonBox.Cancel).setText("取消")

        self.btn_tilesDialog.clicked.connect(self.open_folder)
        self.btn_infoDialog.clicked.connect(self.open_file)

        self.rbtn_onlySpider.toggled.connect(lambda: self.rbtn_toggled(self.rbtn_onlySpider))
        self.rbtn_onlyHandle.toggled.connect(lambda: self.rbtn_toggled(self.rbtn_onlyHandle))
        self.rbtn_spiderAndHandle.toggled.connect(lambda: self.rbtn_toggled(self.rbtn_spiderAndHandle))

        self.rbtn_spiderAndHandle.setChecked(True)

        self.splitter = CollapsibleSplitter(self)
        self.splitter.setGeometry(QRect(0, 0, self.frame.width(), self.frame.height() + 80))
        self.splitter.setOrientation(Qt.Vertical)
        self.splitter.setObjectName("splitter")
        # sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding)
        # self.splitter.setSizePolicy(sizePolicy)

        # self.setCentralWidget(self.splitter)

        self.splitter.addWidget(self.frame)
        self.splitter.addWidget(self.textEdit)
        # self.resize(self.width(), self.frame.height() + self.textEdit.height())

        hlayout = QtWidgets.QVBoxLayout(self)
        hlayout.addWidget(self.splitter)
        # self.adjustSize()

        self.splitter.setProperty("Stretch", SplitterState.expanded)
        self.splitter.setProperty("Dock", Dock.down)
        self.splitter.setProperty("WidgetToHide", self.textEdit)
        self.splitter.setProperty("ExpandParentForm", True)

        self.splitter.setSizes([self.frame.height(), self.textEdit.height()])
        # self.splitter.setSizes([750, self.height() - 750])

        self.btn_obtain.clicked.connect(self.btn_obtain_clicked)
        self.cmb_level.currentIndexChanged.connect(self.cmb_selectionchange)

    # def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
    #     self.adjustSize()

    def rbtn_toggled(self, btn):
        if self.rbtn_onlySpider.isChecked() or self.rbtn_spiderAndHandle.isChecked():
            self.txt_infoPath.setEnabled(False)
            self.btn_infoDialog.setEnabled(False)
            self.txt_imageFolderPath.setEnabled(False)
            self.btn_tilesDialog.setEnabled(False)
        else:
            self.txt_infoPath.setEnabled(True)
            self.btn_infoDialog.setEnabled(True)
            self.txt_imageFolderPath.setEnabled(True)
            self.btn_tilesDialog.setEnabled(True)

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

    def open_file(self):
        fileName, fileType = QtWidgets.QFileDialog.getOpenFileName(self, "选择瓦片信息json文件", os.getcwd(),
                                                                  "json Files(*.json);;All Files(*)")
        self.txt_infoPath.setText(fileName)


    def open_folder(self):
        get_folder = QtWidgets.QFileDialog.getExistingDirectory(self,
                                                                 "选择瓦片文件夹",
                                                                 os.getcwd())
        self.txt_imageFolderPath.setText(get_folder)


    def accept(self):
        QMessageBox.information(self, "提示", "OK", QMessageBox.Yes)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    style = QStyleFactory.create("windows")
    app.setStyle(style)
    # MainWindow = QDialog()
    window = Ui_Window()
    window.show()
    sys.exit(app.exec())