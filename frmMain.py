import csv
import os

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMessageBox, QMainWindow, QSystemTrayIcon, QAction, QMenu
from PyQt5 import QtCore
import UI.UIMain
import sys
import frmVectorMap
import frmTileMap
import frmCoordTransform
from UICore.log4p import Log

Slot = QtCore.pyqtSlot

log = Log(__name__)


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

    print(os.environ['GDAL_DRIVER_PATH'])
    print(os.environ['GDAL_DATA'])
    print(os.environ['PROJ_LIB'])

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
                                    "窗口将缩至系统托盘并在后台继续运行,如需完全"
                                    "退出程序请在托盘小图标的右键菜单中选择<b>退出</b>按钮.")
            self.bFirstHint = False

        self.hide()
        event.ignore()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # style = QStyleFactory.create("windows")
    # app.setStyle(style)
    # os.environ['PROJ_LIB'] = r'.\osgeo\data\proj'
    # os.environ['PROJ_LIB'] = r"./Library/share/proj"
    # os.environ['GDAL_DRIVER_PATH'] = os.path.dirname(sys.argv[0]) + "/Library/lib/gdalplugins"
    # os.environ['GDAL_DATA'] = r"./Library/share/gdal"
    # print(os.path.dirname(sys.argv[0]))
    log.debug(os.environ['GDAL_DRIVER_PATH'])
    log.debug(os.environ['GDAL_DATA'])
    log.debug(os.environ['PROJ_LIB'])

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
