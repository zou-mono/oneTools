import sys

import typing
from PyQt5.QtCore import QAbstractTableModel, Qt, QVariant, QModelIndex, QDataStream, QPersistentModelIndex, QMimeData, \
    QIODevice, QByteArray, QTextCodec, QItemSelectionModel
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QPalette, QColor, QPainter
from PyQt5.QtWidgets import QMainWindow, QApplication, QDialog, QAbstractItemView, QHeaderView, QMessageBox, \
    QProxyStyle, QStyleOption, QTableView


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


class TableModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super(TableModel, self).__init__(parent)

        self.datas = []
        self.headers = []

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
        data = self.datas[row]
        if role == Qt.EditRole or role == Qt.DisplayRole:
            item = data[col]
            # if col == AGE:                             # 还可以实现数据的转换显示或显示处理后的数据
            #     item = int(item)
            return item

    # def setHeaderData(self, section: int, orientation: Qt.Orientation, value: typing.Any, role: int = ...) -> bool:

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
            self.datas.append(data)
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
        if index.isValid() and 0 <= index.row() < self.rowCount(QModelIndex()) and role == Qt.EditRole and value:
            col = index.column()
            # print(col)
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



