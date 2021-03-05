import sys

from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import QHeaderView, QAbstractItemView, QApplication, QDialog
from PyQt5.QtCore import Qt, QItemSelectionModel, QPersistentModelIndex, QModelIndex
from UItableview import Ui_Dialog
from widgets.mTable import TableModel, mTableStyle

class Ui_Window(QDialog, Ui_Dialog):
    def __init__(self):
        super(Ui_Window, self).__init__()
        self.setupUi(self)
        model = TableModel()
        self.tableView.setStyle(mTableStyle())

        model.initData(["服务名", "地址"], [])

        # self.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableView.horizontalHeader().setStretchLastSection(True)
        self.tableView.verticalHeader().setDefaultSectionSize(20)
        color = self.palette().color(QPalette.Button)
        self.tableView.horizontalHeader().setStyleSheet("QHeaderView::section {{ background-color: {}}}".format(color.name()))
        self.tableView.verticalHeader().setStyleSheet("QHeaderView::section {{ background-color: {}}}".format(color.name()))
        self.tableView.setStyleSheet("QTableCornerButton::section {{ color: {}; border: 1px solid; border-color: {}}}".format(color.name(), color.name()))

        self.tableView.setModel(model)

        self.tableView.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tableView.setEditTriggers(QAbstractItemView.SelectedClicked)
        self.tableView.DragDropMode(QAbstractItemView.InternalMove)
        self.tableView.setSelectionBehavior(QAbstractItemView.SelectRows)
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