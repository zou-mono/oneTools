import os
import sys
import sip

import typing
from PyQt5.QtCore import QAbstractTableModel, Qt, QVariant, QModelIndex, QDataStream, QPersistentModelIndex, QMimeData, \
    QIODevice, QByteArray, QTextCodec, QItemSelectionModel, QAbstractItemModel, QTimer, QEvent, QRect, pyqtSignal
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QPalette, QColor, QPainter, QIcon, QPixmap
from PyQt5.QtWidgets import QMainWindow, QApplication, QDialog, QAbstractItemView, QHeaderView, QMessageBox, \
    QProxyStyle, QStyleOption, QTableView, QStyledItemDelegate, QWidget, QLineEdit, QPushButton, QFileDialog, QStyle, \
    QStyleOptionButton, QHBoxLayout, QComboBox


class FileAddressEditor(QWidget):
    editingFinished = pyqtSignal()
    clickButton = pyqtSignal()

    def __init__(self, parent, option, buttonType='f'):
        super().__init__(parent)

        # self.setMouseTracking(True)
        self.setAutoFillBackground(True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        mBtn_address = QPushButton(self)
        mBtn_address.setObjectName("mBtn_address")
        mBtn_address.setFocusPolicy(Qt.NoFocus)
        mBtn_address.setFixedWidth(option.rect.height())
        layout.addWidget(mBtn_address)

        self.mTxt_address = QLineEdit(self)
        self.mTxt_address.setObjectName("mTxt_address")
        layout.addWidget(self.mTxt_address)
        self.setFocusProxy(self.mTxt_address)

        icon = QIcon()
        if buttonType == 'f':
            icon.addPixmap(QPixmap(":/icons/icons/Text_File32.png"), QIcon.Normal, QIcon.Off)
            mBtn_address.setIcon(icon)
        elif buttonType == 'd':
            icon.addPixmap(QPixmap(":/icons/icons/Folder32.png"), QIcon.Normal, QIcon.Off)
            mBtn_address.setIcon(icon)

        self.mTxt_address.installEventFilter(self)
        mBtn_address.installEventFilter(self)
        self.bClickButton = False

    def setText(self, value):
        self.mTxt_address.setText(str(value))

    def text(self):
        return self.mTxt_address.text()

    def eventFilter(self, source: 'QObject', event: 'QEvent') -> bool:
        if isinstance(source, QPushButton) and event.type() == QEvent.MouseButtonPress:
            if source.objectName() == "mBtn_address":
                self.bClickButton = True
                self.clickButton.emit()
                return True

        if isinstance(source, QLineEdit) and event.type() == QEvent.FocusIn:
            self.bClickButton = False
            return True

        if isinstance(source, QLineEdit) and event.type() == QEvent.FocusOut and self.bClickButton == False:
            self.editingFinished.emit()
            return True

        return super().eventFilter(source, event)

class mTableStyle(QProxyStyle):

    def drawPrimitive(self, element, option, painter, widget=None):
        """
        Draw a line across the entire row rather than just the column
        we're hovering over.  This may not always work depending on global
        style - for instance I think it won't work on OSX.
        """
        if element == self.PE_IndicatorItemViewItemDrop and not option.rect.isNull():
            option_new = QStyleOption(option)
            rect = option_new.rect
            rect.setLeft(0)
            if widget:
                rect.setRight(widget.width())
            # rect.setY(rect.y() + rect.height())
            # rect.setHeight(2)
            option = option_new

            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setPen(QColor("red"))

        super().drawPrimitive(element, option, painter, widget)


class addressTableDelegate(QStyledItemDelegate):

    def __init__(self, parent, buttonSection, orientation=Qt.Horizontal):
        # buttonColumn用来记录需要设置按钮的单元格
        # orientation用来表示需要设置按钮的表头方向，horizontal表示所有列都设置按钮, vertical表示所有行都设置按钮
        super(addressTableDelegate, self).__init__(parent)
        self.buttonSection = buttonSection
        self.orientation = orientation
        self._isEditing = False
        # self.cmb_level = QComboBox(parent)

    def createEditor(self, parent: QWidget, option: 'QStyleOptionViewItem', index: QModelIndex) -> QWidget:
        section = index.column() if self.orientation == Qt.Horizontal else index.row()

        if self.buttonSection[section] is not None:
            title = self.buttonSection[section]['text'] if 'text' in self.buttonSection[section] else "请选择..."
            type = self.buttonSection[section]['type'] if 'type' in self.buttonSection[section] else "f"
            if type == 'c':
                self.cmb_level = QComboBox(parent)
                # datas = index.model().data(index, Qt.EditRole)
                # for data in datas:
                #     self.cmb_level.addItem(str(data))
                self.cmb_level.currentIndexChanged.connect(self.cmb_selectionchange)
                return self.cmb_level
            else:
                self.mAddressDialog = FileAddressEditor(parent, option, type)
                self.mAddressDialog.clickButton.connect(lambda: self.mBtn_address_clicked(parent, title, type))
                self.mAddressDialog.editingFinished.connect(self.commitAndCloseEditor)
                return self.mAddressDialog
        else:
            return super().createEditor(parent, option, index)

    def cmb_selectionchange(self):
        print('change')

    def mBtn_address_clicked(self, parent, title, type):
        if type == 'f':
            fileName, fileType = QFileDialog.getSaveFileName(parent, title, os.getcwd(),
                                                             "All Files(*)")
        elif type == 'd':
            fileName = QFileDialog.getExistingDirectory(parent, title, os.getcwd(), QFileDialog.ShowDirsOnly)

        if not sip.isdeleted(self.mAddressDialog):
            self.mAddressDialog.setText(fileName)
            self.commitAndCloseEditor()
        else:
            print("deleted, {}".format(fileName))

    def setModelData(self, editor: QWidget, model: QAbstractItemModel, index: QModelIndex) -> None:
        if isinstance(editor, FileAddressEditor):
            model.setData(index, editor.text())
        elif isinstance(editor, QComboBox):
            allItems = [editor.itemText(i) for i in range(editor.count())]
            model.setData(index, allItems)
        else:
            super(addressTableDelegate, self).setModelData(editor, model, index)
        self._isEditing = False

    def setEditorData(self, editor: QWidget, index: QModelIndex) -> None:
        if isinstance(editor, FileAddressEditor):
            editor.setText(index.model().data(index, Qt.EditRole))
        elif isinstance(editor, QComboBox):
            datas = index.model().data(index, Qt.EditRole)
            for data in datas:
                editor.addItem(str(data))
        else:
            super(addressTableDelegate, self).setEditorData(editor, index)
        self._isEditing = True

    def isEditing(self):
        return self._isEditing

    def commitAndCloseEditor(self):
        editor = self.sender()
        self.commitData.emit(editor)
        self.closeEditor.emit(editor)

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


class TableModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super(TableModel, self).__init__(parent)

        self.datas = []
        self.headers = []

    def datas(self):
        return self.datas

    def initData(self, headers, datas):
        self.headers = headers
        self.datas = datas

    def rowCount(self, parent):
        return len(self.datas)

    def columnCount(self, parent):
        return len(self.headers)

    def columnCount(self, parent):
        return len(self.headers)

    def flags(self, index):
        f = Qt.ItemFlags(super(TableModel, self).flags(index) | Qt.ItemIsEditable | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled)
        if not index.isValid():
            f = f | Qt.ItemIsEnabled | Qt.ItemIsDragEnabled
        return f

    def supportedDropActions(self) -> Qt.DropActions:
        return Qt.MoveAction | Qt.CopyAction

    def data(self, index, role):
        if not index.isValid() or not (0 <= index.row() < len(self.datas)):  # 无效的数据请求
            return QVariant()

        row, col = index.row(), index.column()
        if role == Qt.EditRole or role == Qt.DisplayRole:
            item = self.datas[row][col]
            # if col == AGE:                             # 还可以实现数据的转换显示或显示处理后的数据
            #     item = int(item)
            return item

    def setHeaderData(self, section: int, orientation: Qt.Orientation, value: typing.Any, role: int = ...) -> bool:
        if role != Qt.DisplayRole:
            return QVariant()
        if len(self.headers) <= section:
            self.headers.append(value)
            return True

        if self.headers[section] is not None:
            self.headers[section] = value
        else:
            self.headers.append(value)
        return True

    def appendRow(self, rowData, role):
        if role == Qt.DisplayRole:
            self.datas.append(rowData)

    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole:
            return QVariant()

        if orientation == Qt.Vertical:
            return section + 1
        else:
            return self.headers[section]

    def addEmptyRow(self, row: int, count: int, index=QModelIndex()) -> bool:
        self.beginInsertRows(QModelIndex(), row, row + count - 1)
        for i in range(count):
            data = [""] * self.columnCount(QModelIndex())
            self.datas.insert(row, data)
        self.endInsertRows()
        return True

    def insertRows(self, row: int, count: int, parent: QModelIndex = ...) -> bool:
        self.beginInsertRows(QModelIndex(), row, row + count - 1)
        for i in range(count):
            self.datas.insert(row, self.datas[row])
        self.beginInsertRows()
        return True

    def removeRows(self, row: int, count: int, parent: QModelIndex = ...) -> bool:
        self.beginRemoveRows(QModelIndex(), row, row + count - 1)
        for i in range(count):
            self.datas.remove(self.datas[row])
        self.endRemoveRows()
        return True

    def setData(self, index, value, role=Qt.EditRole):
        if index.isValid() and 0 <= index.row() < self.rowCount(QModelIndex()) and role == Qt.EditRole:
            col = index.column()
            # print(col)
            if value is None:
                value = ""
            if col < self.columnCount(QModelIndex()):
                self.beginResetModel()
                self.datas[index.row()][col] = value
                self.endResetModel()
                return True
        return False

    def mimeTypes(self) -> typing.List[str]:
        return ['application/x-tableview-dragRow']

    def mimeData(self, indexes) -> 'QMimeData':
        mimeData = QMimeData()
        encodedData = QByteArray()

        stream = QDataStream(encodedData, QIODevice.WriteOnly)
        rows = set(index.row() for index in indexes)
        for row in rows:
            stream.writeInt32(row)

        mimeData.setData('application/x-tableview-dragRow', encodedData)
        return mimeData

    def dropMimeData(self, data: 'QMimeData', action: Qt.DropAction, row: int, column: int, parent: QModelIndex) -> bool:
        if action == Qt.IgnoreAction:
            return True
        if column > 0:
            return False

        if row != -1:
            endRow = row
        elif parent.isValid():
            endRow = parent.row()
        else:
            endRow = self.rowCount(QModelIndex())

        encodedData = data.data('application/x-tableview-dragRow')
        stream = QDataStream(encodedData, QIODevice.ReadOnly)

        beginRows = []
        beginDatas = []
        # newEndRow = endRow
        while not stream.atEnd():
            beginRow = stream.readInt32()
            beginRows.append(beginRow)
            beginDatas.append(self.datas[beginRow])
            if beginRow < endRow - 1:
                endRow = endRow - 1

        beginRows = sorted(beginRows, reverse=True)
        for beginRow in beginRows:
            self.removeRows(beginRow, 1, 0)

        # if endRow == self.rowCount(QModelIndex()) - 1:
        #     endRow = endRow + 1

        for beginData in beginDatas:
            self.beginInsertRows(QModelIndex(), endRow, endRow)
            self.datas.insert(endRow, beginData)
            self.endInsertRows()

            endRow = endRow + 1

        return True

    def moveRows(self, sourceParent: QModelIndex, sourceRow: int, count: int, destinationParent: QModelIndex, destinationChild: int) -> bool:
        self.beginMoveRows(QModelIndex(), sourceRow, sourceRow + count - 1, QModelIndex(), destinationChild)
        for i in range(0, count):
            self.datas.insert(destinationChild + i, self.datas[sourceRow])
            removeIndex = sourceRow if destinationChild > sourceRow else sourceRow + 1
            self.datas.remove(self.datas[removeIndex])
        self.endMoveRows()
        return True



