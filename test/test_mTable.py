import os
import sys

from PyQt5.QtGui import QPalette, QPainter
from PyQt5.QtWidgets import QHeaderView, QAbstractItemView, QApplication, QDialog, QStyledItemDelegate, QWidget, \
    QFileDialog, QPushButton, QStyle, QStyleOptionButton, QLineEdit, QItemDelegate
from PyQt5.QtCore import Qt, QItemSelectionModel, QPersistentModelIndex, QModelIndex, QRect, QAbstractItemModel, QEvent, \
    QTimer
from UItableview import Ui_Dialog
from widgets.mTable import TableModel, mTableStyle

# class FileDialogEditor(QWidget):



class addressTableDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super(addressTableDelegate, self).__init__(parent)

    def createEditor(self, parent: QWidget, option: 'QStyleOptionViewItem', index: QModelIndex) -> QWidget:
        mAddressDialog = QWidget(parent)
        mAddressDialog.setGeometry(option.rect)
        self.mTxt_address = QLineEdit(mAddressDialog)
        self.mTxt_address.setText(str(index.data()))
        self.mTxt_address.setGeometry(0, 0, option.rect.width() - option.rect.height(), option.rect.height())
        mAddressDialog.setFocusProxy(self.mTxt_address)

        mBtn_address = QPushButton(mAddressDialog)
        mBtn_address.setFocusPolicy(Qt.NoFocus)
        mBtn_address.setGeometry(option.rect.width() - option.rect.height(), 0, option.rect.height(), option.rect.height())
        mBtn_address.clicked.connect(lambda: self.mBtn_address_clicked(parent))
        self.mTxt_address.editingFinished.connect(lambda: self.commitAndCloseEditor(mAddressDialog))

        return mAddressDialog

    def mBtn_address_clicked(self, parent):
        fileName, fileType = QFileDialog.getOpenFileName(parent, "选择服务地址文件", os.getcwd(),
                                                                   "All Files(*)")
        self.mTxt_address.setText(fileName)
        self.fileName = fileName

    # def destroyEditor(self, parent: QWidget, index: QModelIndex) -> QWidget:
    #     print("destroy")
        # super(addressTableDelegate, self).destroyEditor(parent, index)

    def setModelData(self, editor: QWidget, model: QAbstractItemModel, index: QModelIndex) -> None:
        if index.data():
            model.setData(index, str(self.mTxt_address.text()))
        print(index.data())
        # if isinstance(editor, QLineEdit):
        #     model.setData(index, editor.text())
        # else:
        #     super(addressTableDelegate, self).setModelData(editor, model, index)

    def setEditorData(self, editor: QWidget, index: QModelIndex) -> None:
        if index.data():
            self.mTxt_address.setText(str(index.model().data(index, Qt.EditRole)))
            # self.mTxt_address.setText("正在测试")
        # if isinstance(editor, QLineEdit):
        #     editor.setText(index.model().data(index, Qt.EditRole))
        # else:
        #     super(addressTableDelegate, self).setEditorData(editor, index)

    def commitAndCloseEditor(self, parent):
        editor = self.sender()
        print("over")
        self.commitData.emit(parent)
        self.closeEditor.emit(parent)

    def paint(self, painter: QPainter, option: 'QStyleOptionViewItem', index: QModelIndex) -> None:
        widget = option.widget
        self.initStyleOption(option, index)
        style = QApplication.style() if widget is None else widget.style()
        style.drawControl(QStyle.CE_ItemViewItem, option, painter, widget)

        if not (option.state & QStyle.State_Editing):
            return
        btn_address = QStyleOptionButton()
        btn_address.features = QStyleOptionButton.DefaultButton
        btn_address.fontMetrics = option.fontMetrics
        btn_address.palette = option.palette
        btn_address.styleObject = option.styleObject
        btn_address.rect = QRect(option.rect.left() + option.rect.width() - option.rect.height(),
                                 option.rect.top(), option.rect.height(), option.rect.height())

        style.drawControl(QStyle.CE_PushButton, btn_address, painter, widget)

    def editorEvent(self, event: QEvent, model: QAbstractItemModel, option: 'QStyleOptionViewItem', index: QModelIndex) -> bool:
        if (event.type() == QEvent.MouseButtonPress and
                event.button() == Qt.LeftButton and
                index in option.widget.selectedIndexes()):
            # the index is already selected, we'll delay the (possible)
            # editing but we MUST store the direct reference to the table for
            # the lambda function, since the option object is going to be
            # destroyed; this is very important: if you use "option.widget"
            # in the lambda the program will probably hang or crash
            table = option.widget
            QTimer.singleShot(0, lambda: self.checkIndex(table, index))
        return super().editorEvent(event, model, option, index)

    def checkIndex(self, table, index):
        if index in table.selectedIndexes() and index == table.currentIndex():
            table.edit(index)


class Ui_Window(QDialog, Ui_Dialog):
    def __init__(self):
        super(Ui_Window, self).__init__()
        self.setupUi(self)
        model = TableModel()
        self.tableView.setStyle(mTableStyle())

        # model.initData(["服务名", "地址"], [])
        model.setHeaderData(0, Qt.Horizontal, "服务名", Qt.DisplayRole)
        model.setHeaderData(1, Qt.Horizontal, "地址", Qt.DisplayRole)

        model.appendRow([1, "2"], Qt.DisplayRole)

        # self.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # self.tableView.horizontalHeader().setStretchLastSection(True)
        self.tableView.verticalHeader().setDefaultSectionSize(20)
        color = self.palette().color(QPalette.Button)
        self.tableView.horizontalHeader().setStyleSheet("QHeaderView::section {{ background-color: {}}}".format(color.name()))
        self.tableView.verticalHeader().setStyleSheet("QHeaderView::section {{ background-color: {}}}".format(color.name()))
        self.tableView.setStyleSheet("QTableCornerButton::section {{ color: {}; border: 1px solid; border-color: {}}}".format(color.name(), color.name()))

        self.tableView.setModel(model)
        self.tableView.setItemDelegate(addressTableDelegate(self))

        # self.tableView.setSelectionMode(QAbstractItemView.ExtendedSelection)
        # self.tableView.setEditTriggers(QAbstractItemView.SelectedClicked)
        # self.tableView.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.SelectedClicked)
        self.tableView.DragDropMode(QAbstractItemView.InternalMove)
        # self.tableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableView.setDefaultDropAction(Qt.MoveAction)

        self.tableView.horizontalHeader().setSectionsMovable(True)
        self.tableView.setDragEnabled(True)
        self.tableView.setAcceptDrops(True)

    def btn_clicked(self):
        # QMessageBox.information(self, "测试", "测试", QMessageBox.Ok)
        # print(self.tableView.model().rowCount(0))
        self.tableView.model().addEmptyRow(self.tableView.model().rowCount(0), 1, 0)

    def removeBtn_clicked(self):
        # selRows = self.tableView.selectionModel().selectedRows()
        rows = sorted(set(index.row() for index in
                          self.tableView.selectedIndexes()), reverse=True)

        index_list = []
        for model_index in self.tableView.selectionModel().selectedRows():
            index = QPersistentModelIndex(model_index)
            index_list.append(index)

        for index in index_list:
            self.tableView.model().removeRows(index.row(), 1, 0)

        next_index = self.tableView.model().index(self.tableView.model().rowCount(QModelIndex()) - 1, 0)
        # self.tableView.setCurrentIndex(next_index)
        self.tableView.selectionModel().select(next_index, QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)
        self.tableView.setFocus()
        # self.tableView.selectionModel().selectedColumns(self.tableView.model().rowCount(QModelIndex()) - 1)

        # for row in rows:
        #     self.tableView.model().removeRows(row, 1, 0)

if __name__ == '__main__':
    # palette = QPalette()
    # palette.setColor(QPalette.Window, QColor(53, 53, 53))

    app = QApplication(sys.argv)
    # app.setPalette(palette)
    ui = Ui_Dialog()
    window = Ui_Window()
    window.show()
    sys.exit(app.exec_())