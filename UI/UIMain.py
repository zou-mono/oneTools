# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'UIMain.ui'
#
# Created by: PyQt5 UI code generator 5.15.2
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.setWindowModality(QtCore.Qt.WindowModal)
        MainWindow.resize(600, 400)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("AcadEref")
        font.setPointSize(10)
        MainWindow.setFont(font)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/icons/GeoprocessingToolbox48.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MainWindow.setWindowIcon(icon)
        MainWindow.setUnifiedTitleAndToolBarOnMac(False)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.btn_coordTransform = QtWidgets.QPushButton(self.centralwidget)
        self.btn_coordTransform.setGeometry(QtCore.QRect(20, 20, 221, 36))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btn_coordTransform.sizePolicy().hasHeightForWidth())
        self.btn_coordTransform.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        self.btn_coordTransform.setFont(font)
        self.btn_coordTransform.setLayoutDirection(QtCore.Qt.LeftToRight)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/icons/icons/EditingAdjustmentModifyLink32.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btn_coordTransform.setIcon(icon1)
        self.btn_coordTransform.setIconSize(QtCore.QSize(32, 32))
        self.btn_coordTransform.setCheckable(False)
        self.btn_coordTransform.setObjectName("btn_coordTransform")
        self.btn_vectorCrawler = QtWidgets.QPushButton(self.centralwidget)
        self.btn_vectorCrawler.setGeometry(QtCore.QRect(20, 70, 221, 36))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btn_vectorCrawler.sizePolicy().hasHeightForWidth())
        self.btn_vectorCrawler.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        self.btn_vectorCrawler.setFont(font)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/icons/icons/AnimationCreateGroup32.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btn_vectorCrawler.setIcon(icon2)
        self.btn_vectorCrawler.setIconSize(QtCore.QSize(32, 32))
        self.btn_vectorCrawler.setObjectName("btn_vectorCrawler")
        self.btn_imageCrawler = QtWidgets.QPushButton(self.centralwidget)
        self.btn_imageCrawler.setGeometry(QtCore.QRect(20, 120, 221, 36))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btn_imageCrawler.sizePolicy().hasHeightForWidth())
        self.btn_imageCrawler.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        self.btn_imageCrawler.setFont(font)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(":/icons/icons/RasterImageAnalysisDifference32.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btn_imageCrawler.setIcon(icon3)
        self.btn_imageCrawler.setIconSize(QtCore.QSize(32, 32))
        self.btn_imageCrawler.setObjectName("btn_imageCrawler")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 600, 25))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "工具集"))
        self.btn_coordTransform.setText(_translate("MainWindow", "坐标转换"))
        self.btn_vectorCrawler.setText(_translate("MainWindow", "抓取多规合一矢量数据"))
        self.btn_imageCrawler.setText(_translate("MainWindow", "抓取多规合一影像数据"))
import icons_rc
