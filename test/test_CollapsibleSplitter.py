from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt, pyqtSignal, QPointF, QObject, QEvent, QRect
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QStyleFactory
import sys
from widgets.CollapsibleSplitter import CollapsibleSplitter
from UICore.Gv import Dock, SplitterState


class Window(QMainWindow):
    def __init__(self):
        super(Window, self).__init__()

        self.setObjectName("MainWindow")
        self.resize(800, 600)
        self.centralwidget = QtWidgets.QWidget(self)
        self.centralwidget.setObjectName("centralwidget")
        self.centralwidget.setMouseTracking(True)

        self.bSplitterButton = False  # 显示按钮
        self.splitter = CollapsibleSplitter(self.centralwidget)
        self.setCentralWidget(self.centralwidget)
        hlayout = QtWidgets.QHBoxLayout(self.centralwidget)
        hlayout.addWidget(self.splitter)

        self.splitter.setGeometry(0, 0, 800, 600)
        self.splitter.setHandleWidth(10)

        self.textEdit1 = QtWidgets.QTextEdit()
        self.textEdit1.setObjectName("textEdit1")
        self.textEdit1.setText("textEdit1")
        self.textEdit2 = QtWidgets.QTextEdit()
        self.textEdit2.setObjectName("textEdit2")
        self.textEdit2.setText("textEdit2")

        self.splitter.addWidget(self.textEdit1)
        self.splitter.addWidget(self.textEdit2)


        # self.widgetToHide = self.textEdit1

        # self.otherWidget = self.textEdit2

        self.splitter.setSizes([200, 600])
        # self.splitter.setOrientation(Qt.Vertical)
        self.splitter.setProperty("SplitterButton", self.bSplitterButton)
        self.splitter.setProperty("Stretch", SplitterState.collapsed)
        self.splitter.setProperty("Dock", Dock.right)
        self.splitter.setProperty("WidgetToHide", self.textEdit2)
        self.splitter.setProperty("ExpandParentForm", True)

        # self.splitter.setupUi()

        if self.bSplitterButton:
            if self.splitter.orientation() == Qt.Vertical:
                self.splitter.createButton(60, 30)
                self.splitter.widgetToHide.setMinimumHeight(30)
                self.splitter.otherWidget.setMinimumHeight(30)
                self.splitter.minDistanceToEdge = 30
            elif self.splitter.orientation() == Qt.Horizontal:
                self.splitter.createButton(30, 60)
                self.splitter.widgetToHide.setMinimumWidth(30)
                self.splitter.otherWidget.setMinimumWidth(30)
                self.splitter.minDistanceToEdge = 30

        self.textEdit1.viewport().installEventFilter(self)
        self.textEdit2.viewport().installEventFilter(self)

    def eventFilter(self, obj: QObject, event: QEvent):
        # print(event.type())
        if self.bSplitterButton:
            if event.type() == QEvent.MouseMove:
                rect = self.splitter.button.frameGeometry()
                if self.splitter.orientation() == Qt.Vertical:
                    nRect = QRect(self.splitter.handle(1).pos().x(), self.splitter.handle(1).pos().y() - rect.height(),
                                  self.splitter.handle(1).width(), rect.height() * 2)
                else:
                    nRect = QRect(self.splitter.handle(1).pos().x() - rect.width(), self.splitter.handle(1).pos().y(),
                                  rect.width() * 2, self.splitter.handle(1).height())
                # print(event.windowPos().toPoint())
                if nRect.contains(event.windowPos().toPoint()):
                    self.splitter.button.show()
                else:
                    self.splitter.button.hide()

        return super(Window, self).eventFilter(obj, event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    style = QStyleFactory.create("windows")
    app.setStyle(style)
    # MainWindow = QMainWindow()
    # MainWindow.setMouseTracking(True)
    ui = Window()
    ui.setMouseTracking(True)
    ui.show()
    sys.exit(app.exec_())
