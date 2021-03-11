import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtGui as QtGui
import PyQt5.QtCore as QtCore

class ClickDelegate(QtWidgets.QStyledItemDelegate):
    blankText = '<Click here to add path>'

    def openFileDialog(self, lineEdit):
        if not self.blankText.startswith(lineEdit.text()):
            currentPath = lineEdit.text()
        else:
            currentPath = ''
        path, _ = QtWidgets.QFileDialog.getOpenFileName(lineEdit.window(),
                                                        'Select file', currentPath)
        if path:
            lineEdit.setText(path)

    def createEditor(self, parent, option, index):
        editor = QtWidgets.QWidget(parent)

        layout = QtWidgets.QHBoxLayout(editor)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        editor.lineEdit = QtWidgets.QLineEdit(self.blankText)
        layout.addWidget(editor.lineEdit)
        # set the line edit as focus proxy so that it correctly handles focus
        editor.setFocusProxy(editor.lineEdit)
        # install an event filter on the line edit, because we'll need to filter
        # mouse and keyboard events
        editor.lineEdit.installEventFilter(self)

        button = QtWidgets.QToolButton(text='...')
        layout.addWidget(button)
        button.setFocusPolicy(QtCore.Qt.NoFocus)
        button.clicked.connect(lambda: self.openFileDialog(editor.lineEdit))
        return editor

    def setEditorData(self, editor, index):
        if index.data():
            editor.lineEdit.setText(str(index.data()))
        editor.lineEdit.selectAll()

    def setModelData(self, editor, model, index):
        # if there is no text, the data is cleared
        if not editor.lineEdit.text():
            model.setData(index, None)
        # if there is text and is not the "blank" default, set the data accordingly
        elif not self.blankText.startswith(editor.lineEdit.text()):
            model.setData(index, editor.lineEdit.text())

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        if not option.text:
            option.text = self.blankText

    def eventFilter(self, source, event):
        if isinstance(source, QtWidgets.QLineEdit):
            if (event.type() == QtCore.QEvent.MouseButtonPress and
                    source.hasSelectedText() and
                    self.blankText.startswith(source.text())):
                res = super().eventFilter(source, event)
                # clear the text if it's the "Click here..."
                source.clear()
                return res
            elif event.type() == QtCore.QEvent.KeyPress and event.key() in (
                    QtCore.Qt.Key_Escape, QtCore.Qt.Key_Tab, QtCore.Qt.Key_Backtab):
                # ignore some key events so that they're correctly filtered as
                # they are emitted by actual editor (the QWidget)
                return False
        return super().eventFilter(source, event)

    def checkIndex(self, table, index):
        if index in table.selectedIndexes() and index == table.currentIndex():
            table.edit(index)

    def editorEvent(self, event, model, option, index):
        if (event.type() == QtCore.QEvent.MouseButtonPress and
                event.button() == QtCore.Qt.LeftButton and
                index in option.widget.selectedIndexes()):
            # the index is already selected, we'll delay the (possible)
            # editing but we MUST store the direct reference to the table for
            # the lambda function, since the option object is going to be
            # destroyed; this is very important: if you use "option.widget"
            # in the lambda the program will probably hang or crash
            table = option.widget
            QtCore.QTimer.singleShot(0, lambda: self.checkIndex(table, index))
        return super().editorEvent(event, model, option, index)


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    model = QtGui.QStandardItemModel(4, 2)
    tableView = QtWidgets.QTableView()
    tableView.setModel(model)
    delegate = ClickDelegate(tableView)
    tableView.setItemDelegate(delegate)
    section_list = ['w','c','h']
    for row in range(4):
        for column in range(2):
            index = model.index(row, column, QtCore.QModelIndex())
            model.setData(index, (row + 1) * (column + 1))
    tableView.setWindowTitle("Spin Box Delegate")
    tableView.show()
    sys.exit(app.exec_())