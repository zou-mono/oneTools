# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'frmUI.ui'
#
# Created by: PyQt5 UI code generator 5.15.2
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        Dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        Dialog.resize(620, 900)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        self.frame = QtWidgets.QFrame(Dialog)
        self.frame.setGeometry(QtCore.QRect(10, 5, 601, 691))
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.groupBox = QtWidgets.QGroupBox(self.frame)
        self.groupBox.setGeometry(QtCore.QRect(10, 400, 581, 191))
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        self.groupBox.setFont(font)
        self.groupBox.setObjectName("groupBox")
        self.layoutWidget = QtWidgets.QWidget(self.groupBox)
        self.layoutWidget.setGeometry(QtCore.QRect(150, 35, 227, 28))
        self.layoutWidget.setObjectName("layoutWidget")
        self.horizontalLayout_8 = QtWidgets.QHBoxLayout(self.layoutWidget)
        self.horizontalLayout_8.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_8.setObjectName("horizontalLayout_8")
        self.label_6 = QtWidgets.QLabel(self.layoutWidget)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        self.label_6.setFont(font)
        self.label_6.setObjectName("label_6")
        self.horizontalLayout_8.addWidget(self.label_6)
        self.txt_ymax = QtWidgets.QLineEdit(self.layoutWidget)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        self.txt_ymax.setFont(font)
        self.txt_ymax.setReadOnly(False)
        self.txt_ymax.setObjectName("txt_ymax")
        self.horizontalLayout_8.addWidget(self.txt_ymax)
        self.layoutWidget1 = QtWidgets.QWidget(self.groupBox)
        self.layoutWidget1.setGeometry(QtCore.QRect(150, 140, 224, 28))
        self.layoutWidget1.setObjectName("layoutWidget1")
        self.horizontalLayout_11 = QtWidgets.QHBoxLayout(self.layoutWidget1)
        self.horizontalLayout_11.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_11.setObjectName("horizontalLayout_11")
        self.label_7 = QtWidgets.QLabel(self.layoutWidget1)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        self.label_7.setFont(font)
        self.label_7.setObjectName("label_7")
        self.horizontalLayout_11.addWidget(self.label_7)
        self.txt_ymin = QtWidgets.QLineEdit(self.layoutWidget1)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        self.txt_ymin.setFont(font)
        self.txt_ymin.setObjectName("txt_ymin")
        self.horizontalLayout_11.addWidget(self.txt_ymin)
        self.layoutWidget2 = QtWidgets.QWidget(self.groupBox)
        self.layoutWidget2.setGeometry(QtCore.QRect(10, 90, 224, 28))
        self.layoutWidget2.setObjectName("layoutWidget2")
        self.horizontalLayout_9 = QtWidgets.QHBoxLayout(self.layoutWidget2)
        self.horizontalLayout_9.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_9.setObjectName("horizontalLayout_9")
        self.label_4 = QtWidgets.QLabel(self.layoutWidget2)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        self.label_4.setFont(font)
        self.label_4.setObjectName("label_4")
        self.horizontalLayout_9.addWidget(self.label_4)
        self.txt_xmin = QtWidgets.QLineEdit(self.layoutWidget2)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        self.txt_xmin.setFont(font)
        self.txt_xmin.setObjectName("txt_xmin")
        self.horizontalLayout_9.addWidget(self.txt_xmin)
        self.layoutWidget3 = QtWidgets.QWidget(self.groupBox)
        self.layoutWidget3.setGeometry(QtCore.QRect(330, 90, 227, 28))
        self.layoutWidget3.setObjectName("layoutWidget3")
        self.horizontalLayout_10 = QtWidgets.QHBoxLayout(self.layoutWidget3)
        self.horizontalLayout_10.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_10.setObjectName("horizontalLayout_10")
        self.label_5 = QtWidgets.QLabel(self.layoutWidget3)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        self.label_5.setFont(font)
        self.label_5.setObjectName("label_5")
        self.horizontalLayout_10.addWidget(self.label_5)
        self.txt_xmax = QtWidgets.QLineEdit(self.layoutWidget3)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        self.txt_xmax.setFont(font)
        self.txt_xmax.setObjectName("txt_xmax")
        self.horizontalLayout_10.addWidget(self.txt_xmax)
        self.buttonBox = QtWidgets.QDialogButtonBox(self.frame)
        self.buttonBox.setGeometry(QtCore.QRect(250, 650, 341, 32))
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        self.buttonBox.setFont(font)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.layoutWidget4 = QtWidgets.QWidget(self.frame)
        self.layoutWidget4.setGeometry(QtCore.QRect(10, 320, 281, 28))
        self.layoutWidget4.setObjectName("layoutWidget4")
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout(self.layoutWidget4)
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_5.setSpacing(12)
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.label_10 = QtWidgets.QLabel(self.layoutWidget4)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        self.label_10.setFont(font)
        self.label_10.setObjectName("label_10")
        self.horizontalLayout_5.addWidget(self.label_10)
        self.cmb_level = QtWidgets.QComboBox(self.layoutWidget4)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        self.cmb_level.setFont(font)
        self.cmb_level.setObjectName("cmb_level")
        self.horizontalLayout_5.addWidget(self.cmb_level)
        self.horizontalLayout_5.setStretch(0, 2)
        self.horizontalLayout_5.setStretch(1, 5)
        self.layoutWidget5 = QtWidgets.QWidget(self.frame)
        self.layoutWidget5.setGeometry(QtCore.QRect(10, 360, 281, 31))
        self.layoutWidget5.setObjectName("layoutWidget5")
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout(self.layoutWidget5)
        self.horizontalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.label_2 = QtWidgets.QLabel(self.layoutWidget5)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        self.label_2.setFont(font)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_6.addWidget(self.label_2)
        self.txt_originX = QtWidgets.QTextEdit(self.layoutWidget5)
        self.txt_originX.setEnabled(True)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        self.txt_originX.setFont(font)
        self.txt_originX.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.txt_originX.setReadOnly(True)
        self.txt_originX.setObjectName("txt_originX")
        self.horizontalLayout_6.addWidget(self.txt_originX)
        self.layoutWidget6 = QtWidgets.QWidget(self.frame)
        self.layoutWidget6.setGeometry(QtCore.QRect(320, 360, 271, 31))
        self.layoutWidget6.setObjectName("layoutWidget6")
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout(self.layoutWidget6)
        self.horizontalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.label_3 = QtWidgets.QLabel(self.layoutWidget6)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        self.label_3.setFont(font)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_7.addWidget(self.label_3)
        self.txt_originY = QtWidgets.QTextEdit(self.layoutWidget6)
        self.txt_originY.setEnabled(True)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        self.txt_originY.setFont(font)
        self.txt_originY.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.txt_originY.setReadOnly(True)
        self.txt_originY.setObjectName("txt_originY")
        self.horizontalLayout_7.addWidget(self.txt_originY)
        self.layoutWidget7 = QtWidgets.QWidget(self.frame)
        self.layoutWidget7.setGeometry(QtCore.QRect(10, 600, 235, 28))
        self.layoutWidget7.setObjectName("layoutWidget7")
        self.horizontalLayout_12 = QtWidgets.QHBoxLayout(self.layoutWidget7)
        self.horizontalLayout_12.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_12.setObjectName("horizontalLayout_12")
        self.label_8 = QtWidgets.QLabel(self.layoutWidget7)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        self.label_8.setFont(font)
        self.label_8.setObjectName("label_8")
        self.horizontalLayout_12.addWidget(self.label_8)
        self.txt_resolution = QtWidgets.QLineEdit(self.layoutWidget7)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        self.txt_resolution.setFont(font)
        self.txt_resolution.setObjectName("txt_resolution")
        self.horizontalLayout_12.addWidget(self.txt_resolution)
        self.layoutWidget8 = QtWidgets.QWidget(self.frame)
        self.layoutWidget8.setGeometry(QtCore.QRect(330, 600, 252, 28))
        self.layoutWidget8.setObjectName("layoutWidget8")
        self.horizontalLayout_13 = QtWidgets.QHBoxLayout(self.layoutWidget8)
        self.horizontalLayout_13.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_13.setObjectName("horizontalLayout_13")
        self.label_9 = QtWidgets.QLabel(self.layoutWidget8)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        self.label_9.setFont(font)
        self.label_9.setObjectName("label_9")
        self.horizontalLayout_13.addWidget(self.label_9)
        self.txt_tilesize = QtWidgets.QLineEdit(self.layoutWidget8)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        self.txt_tilesize.setFont(font)
        self.txt_tilesize.setObjectName("txt_tilesize")
        self.horizontalLayout_13.addWidget(self.txt_tilesize)
        self.widget = QtWidgets.QWidget(self.frame)
        self.widget.setGeometry(QtCore.QRect(11, 13, 581, 29))
        self.widget.setObjectName("widget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.widget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.rbtn_onlyHandle = QtWidgets.QRadioButton(self.widget)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        self.rbtn_onlyHandle.setFont(font)
        self.rbtn_onlyHandle.setObjectName("rbtn_onlyHandle")
        self.horizontalLayout.addWidget(self.rbtn_onlyHandle)
        self.rbtn_spiderAndHandle = QtWidgets.QRadioButton(self.widget)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        self.rbtn_spiderAndHandle.setFont(font)
        self.rbtn_spiderAndHandle.setObjectName("rbtn_spiderAndHandle")
        self.horizontalLayout.addWidget(self.rbtn_spiderAndHandle)
        self.rbtn_onlySpider = QtWidgets.QRadioButton(self.widget)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        self.rbtn_onlySpider.setFont(font)
        self.rbtn_onlySpider.setObjectName("rbtn_onlySpider")
        self.horizontalLayout.addWidget(self.rbtn_onlySpider)
        self.widget1 = QtWidgets.QWidget(self.frame)
        self.widget1.setGeometry(QtCore.QRect(10, 50, 581, 255))
        self.widget1.setObjectName("widget1")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.widget1)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label = QtWidgets.QLabel(self.widget1)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.horizontalLayout_3.addWidget(self.label)
        self.txt_address = QtWidgets.QTextEdit(self.widget1)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        self.txt_address.setFont(font)
        self.txt_address.setFrameShape(QtWidgets.QFrame.Box)
        self.txt_address.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.txt_address.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.txt_address.setObjectName("txt_address")
        self.horizontalLayout_3.addWidget(self.txt_address)
        self.btn_obtain = QtWidgets.QPushButton(self.widget1)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        self.btn_obtain.setFont(font)
        self.btn_obtain.setObjectName("btn_obtain")
        self.horizontalLayout_3.addWidget(self.btn_obtain)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.label_11 = QtWidgets.QLabel(self.widget1)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        self.label_11.setFont(font)
        self.label_11.setObjectName("label_11")
        self.verticalLayout.addWidget(self.label_11)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.txt_infoPath = QtWidgets.QLineEdit(self.widget1)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        self.txt_infoPath.setFont(font)
        self.txt_infoPath.setObjectName("txt_infoPath")
        self.horizontalLayout_2.addWidget(self.txt_infoPath)
        self.btn_infoDialog = QtWidgets.QPushButton(self.widget1)
        self.btn_infoDialog.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/icons/openDialog.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btn_infoDialog.setIcon(icon)
        self.btn_infoDialog.setIconSize(QtCore.QSize(25, 25))
        self.btn_infoDialog.setObjectName("btn_infoDialog")
        self.horizontalLayout_2.addWidget(self.btn_infoDialog)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.label_12 = QtWidgets.QLabel(self.widget1)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        self.label_12.setFont(font)
        self.label_12.setObjectName("label_12")
        self.verticalLayout.addWidget(self.label_12)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.txt_imageFolderPath = QtWidgets.QLineEdit(self.widget1)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        self.txt_imageFolderPath.setFont(font)
        self.txt_imageFolderPath.setObjectName("txt_imageFolderPath")
        self.horizontalLayout_4.addWidget(self.txt_imageFolderPath)
        self.btn_tilesDialog = QtWidgets.QPushButton(self.widget1)
        self.btn_tilesDialog.setText("")
        self.btn_tilesDialog.setIcon(icon)
        self.btn_tilesDialog.setIconSize(QtCore.QSize(25, 25))
        self.btn_tilesDialog.setObjectName("btn_tilesDialog")
        self.horizontalLayout_4.addWidget(self.btn_tilesDialog)
        self.verticalLayout.addLayout(self.horizontalLayout_4)
        self.textEdit = QtWidgets.QTextEdit(Dialog)
        self.textEdit.setGeometry(QtCore.QRect(10, 670, 256, 192))
        self.textEdit.setObjectName("textEdit")

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "抓取影像数据"))
        self.groupBox.setTitle(_translate("Dialog", "获取坐标范围"))
        self.label_6.setText(_translate("Dialog", "ymax:"))
        self.label_7.setText(_translate("Dialog", "ymin:"))
        self.label_4.setText(_translate("Dialog", "xmin:"))
        self.label_5.setText(_translate("Dialog", "xmax:"))
        self.label_10.setText(_translate("Dialog", "瓦片等级:"))
        self.label_2.setText(_translate("Dialog", "初始x坐标:"))
        self.label_3.setText(_translate("Dialog", "初始y坐标:"))
        self.label_8.setText(_translate("Dialog", "分辨率:"))
        self.label_9.setText(_translate("Dialog", "瓦片尺寸:"))
        self.rbtn_onlyHandle.setText(_translate("Dialog", "仅预处理"))
        self.rbtn_spiderAndHandle.setText(_translate("Dialog", "既抓取又预处理"))
        self.rbtn_onlySpider.setText(_translate("Dialog", "仅抓取"))
        self.label.setText(_translate("Dialog", "地址:"))
        self.btn_obtain.setText(_translate("Dialog", "获取信息"))
        self.label_11.setText(_translate("Dialog", "离线的瓦片信息json文件"))
        self.label_12.setText(_translate("Dialog", "瓦片文件夹"))
import icons_rc
