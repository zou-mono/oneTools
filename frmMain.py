import csv

from PyQt5.QtCore import QRect, Qt, QPersistentModelIndex, QItemSelectionModel, QModelIndex, QThread, QObject, QSize
from PyQt5.QtGui import QDoubleValidator, QIntValidator, QPalette, QIcon
from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox, QErrorMessage, QDialogButtonBox, QStyleFactory, \
    QMainWindow, QSystemTrayIcon, QAction, QMenu
from PyQt5 import QtWidgets, QtGui, QtCore
from openpyxl import load_workbook
from osgeo import osr, gdal

import UI.UIMain
import sys
import frmVectorMap
import frmTileMap
import frmCoordTransform
import json
import os

from UICore.DataFactory import workspaceFactory, read_table_header
from UICore.Gv import SplitterState, Dock, DataType, srs_dict
from UICore.common import defaultImageFile, defaultTileFolder, urlEncodeToFileName, get_paraInfo, get_suffix, \
    encodeCurrentTime, is_header, is_already_opened_in_write_mode, launderName, check_encoding, read_first_line
from UICore.workerThread import coordTransformWorker
from widgets.mTable import TableModel, mTableStyle, layernameDelegate, srsDelegate, outputPathDelegate, xyfieldDelegate
from UICore.log4p import Log

Slot = QtCore.pyqtSlot

log = Log()

class Ui_Window(QMainWindow, UI.UIMain.Ui_MainWindow):
    def __init__(self):
        super(Ui_Window, self).__init__()
        self.setupUi(self)
        self.setFixedSize(QSize(600, 400))
        self.statusbar.setSizeGripEnabled(False)

        self.btn_coordTransform.setStyleSheet("text-align:left;")
        self.btn_imageCrawler.setStyleSheet("text-align:left;")
        self.btn_vectorCrawler.setStyleSheet("text-align:left;")

        self.bFirstHint = True

        self.createActions()
        self.createTrayIcon()
        self.trayIcon.activated.connect(self.iconActivated)

        self.trayIcon.show()

    @Slot(QSystemTrayIcon.ActivationReason)
    def iconActivated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.showNormal()

    def createActions(self):
        self.minimizeAction = QAction("隐藏", self, triggered=self.hide)
        self.restoreAction = QAction("还原", self, triggered=self.showNormal)
        self.quitAction = QAction("退出", self, triggered=QApplication.instance().quit)

    def createTrayIcon(self):
        self.trayIconMenu = QMenu(self)
        self.trayIconMenu.addAction(self.minimizeAction)
        self.trayIconMenu.addAction(self.restoreAction)
        self.trayIconMenu.addSeparator()
        self.trayIconMenu.addAction(self.quitAction)

        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setContextMenu(self.trayIconMenu)
        self.trayIcon.setIcon(QIcon(":/icons/icons/GeoprocessingToolbox48.png"))

    def closeEvent(self, event):
        if self.bFirstHint:
            QMessageBox.information(self, "工具集",
                                    "窗口将缩至系统托盘并在后台继续运行,如果需要完全"
                                    "退出程序请在托盘小图标的右键菜单中选择<b>退出</b>按钮.")
            self.bFirstHint = False

        self.hide()
        event.ignore()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # style = QStyleFactory.create("windows")
    # app.setStyle(style)

    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, "工具集", "无法检查到系统托盘程序.")
        sys.exit(1)

    QApplication.setQuitOnLastWindowClosed(False)

    frmMain = Ui_Window()

    frmVectorMap = frmVectorMap.Ui_Window(frmMain)
    frmTileMap = frmTileMap.Ui_Window(frmMain)
    frmCoordTransform = frmCoordTransform.Ui_Window(frmMain)
    frmTileMap.setWindowFlags(Qt.Window)
    frmCoordTransform.setWindowFlag(Qt.WindowMinMaxButtonsHint)
    frmVectorMap.setWindowFlags(Qt.Window)

    frmMain.btn_vectorCrawler.clicked.connect(frmVectorMap.show)
    frmMain.btn_imageCrawler.clicked.connect(frmTileMap.show)
    frmMain.btn_coordTransform.clicked.connect(frmCoordTransform.show)

    frmMain.show()

    sys.exit(app.exec_())
