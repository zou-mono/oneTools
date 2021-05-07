import csv

from PyQt5.QtCore import QRect, Qt, QPersistentModelIndex, QItemSelectionModel, QModelIndex, QThread, QObject, QSize
from PyQt5.QtGui import QDoubleValidator, QIntValidator, QPalette
from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox, QErrorMessage, QDialogButtonBox, QStyleFactory, \
    QMainWindow
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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    style = QStyleFactory.create("windows")
    app.setStyle(style)

    frmVectorMap = frmVectorMap.Ui_Window()
    frmTileMap = frmTileMap.Ui_Window()
    frmCoordTransform = frmCoordTransform.Ui_Window()

    frmMain = Ui_Window()
    # frmMain.setWindowFlags(Qt.Window)

    frmMain.btn_vectorCrawler.clicked.connect(frmVectorMap.show)
    frmMain.btn_imageCrawler.clicked.connect(frmTileMap.show)
    frmMain.btn_coordTransform.clicked.connect(frmCoordTransform.show)

    frmMain.show()

    frmTileMap.setWindowFlags(Qt.Window)
    frmCoordTransform.setWindowFlag(Qt.WindowMinMaxButtonsHint)
    frmVectorMap.setWindowFlags(Qt.Window)

    sys.exit(app.exec_())
