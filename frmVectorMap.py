import json
import os
import sys
import traceback

from PyQt5.QtGui import QFont, QPalette, QShowEvent, QResizeEvent
from UI.UIVectorMap import Ui_Dialog
from PyQt5.QtWidgets import QApplication, QDialog, QStyleFactory, QVBoxLayout, QDialogButtonBox, QFileDialog, \
    QHeaderView, QAbstractItemView, QAbstractButton
from PyQt5.QtCore import Qt, QItemSelectionModel, QModelIndex, QPersistentModelIndex, QThread
from PyQt5 import QtCore

from UICore.DataFactory import workspaceFactory
from UICore.Gv import SplitterState, Dock, DataType
from UICore.common import get_paraInfo, urlEncodeToFileName, get_suffix
from UICore.log4p import Log
from UICore.workerThread import crawlVectorWorker
from widgets.mTable import mTableStyle, TableModel, vectorTableDelegate

Slot = QtCore.pyqtSlot

log = Log(__name__)

# 定义请求头
reqheaders = {
    'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36 Edg/81.0.416.72',
    # 'Content-Type': 'application/x-www-form-urlencoded',
    # 'Host': 'suplicmap.pnr.sz',
    'Pragma': 'no-cache'}

class Ui_Window(QDialog, Ui_Dialog):
    def __init__(self, parent=None):
        super(Ui_Window, self).__init__(parent=parent)
        self.setupUi(self)

        font = QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(9)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.button(QDialogButtonBox.Ok).setFont(font)
        self.buttonBox.button(QDialogButtonBox.Ok).setText("确定")
        self.buttonBox.button(QDialogButtonBox.Cancel).setFont(font)
        self.buttonBox.button(QDialogButtonBox.Cancel).setText("取消")

        vlayout = QVBoxLayout(self)
        vlayout.addWidget(self.splitter)
        vlayout.setContentsMargins(0, 0, 10, 10)
        self.splitter.setGeometry(0, 0, self.width(), self.height())
        self.splitter.setOrientation(Qt.Horizontal)
        self.splitter.setProperty("Stretch", SplitterState.collapsed)
        self.splitter.setProperty("Dock", Dock.right)
        self.splitter.setProperty("WidgetToHide", self.txt_log)
        self.splitter.setProperty("ExpandParentForm", True)

        self.splitter.setSizes([600, self.splitter.width() - 590])
        self.resize(self.splitter.width(), self.splitter.height())

        self.paras = {}  # 存储参数信息
        self.selIndex = QModelIndex()
        self.table_init()
        log.setLogViewer(parent=self, logViewer=self.txt_log)
        self.txt_log.setReadOnly(True)

        self.btn_addressFile.clicked.connect(self.open_addressFile)
        self.buttonBox.clicked.connect(self.buttonBox_clicked)

        self.btn_addRow.clicked.connect(self.btn_addRow_Clicked)
        self.btn_removeRow.clicked.connect(self.btn_removeBtn_clicked)
        self.btn_obtainMeta.clicked.connect(self.btn_obtainMeta_clicked)
        self.btn_saveMetaFile.clicked.connect(self.btn_saveMetaFile_clicked)
        self.splitter.splitterMoved.connect(self.splitterMoved)
        self.splitter.handle(1).handleClicked.connect(self.handleClicked)
        self.tbl_address.clicked.connect(self.table_index_clicked)
        self.tbl_address.verticalHeader().sectionClicked.connect(self.table_section_clicked)

        self.txt_subscriptionToken.setText('0d6325d440f14ee8847f7551c686f19c')
        # self.txt_apiToken.setText('eyJpc3N1Y2Nlc3MiOiJ0cnVlIiwiZmFpbHJlc29uIjoiIiwiYWNjb3VudCI6InpvdWhhaXgiLCJ0b2tlbiI6IjY1ZTBlYmI1ZWYyMTRlNjhhNDA5NWU5MDA1ZWYyYzIyIn0=.Eg4DFhERDQ==')
        self.txt_apiToken.setText('eyJpc3N1Y2Nlc3MiOiJ0cnVlIiwiZmFpbHJlc29uIjoiIiwiYWNjb3VudCI6InpvdWhhaXgiLCJ0b2tlbiI6IjFmMGVkMTM2MWY3ZjRiZTJhMGJkMjMzYjAzYmQwYjhlIn0%3D.Eg4DFhERDQ%3D%3D')
        self.txt_subscriptionToken.home(False)
        self.txt_apiToken.home(False)
        self.splitter.setupUi()

    def showEvent(self, a0: QShowEvent) -> None:
        log.setLogViewer(parent=self, logViewer=self.txt_log)
        self.table_layout()
        desktop = QApplication.desktop()
        self.move(int((desktop.width() - self.width())/2), int((desktop.height() - self.height())/2))

    def resizeEvent(self, a0: QResizeEvent) -> None:
        self.table_layout()

    def splitterMoved(self):
        self.table_layout()

    def handleClicked(self):
        self.table_layout()

    def table_layout(self):
        self.tbl_address.setColumnWidth(0, self.tbl_address.width() * 0.4)
        self.tbl_address.setColumnWidth(1, self.tbl_address.width() * 0.2)
        self.tbl_address.setColumnWidth(2, self.tbl_address.width() * 0.2)
        self.tbl_address.setColumnWidth(3, self.tbl_address.width() * 0.2)

    def threadTerminate(self):
        try:
            if self.thread.isRunning():
                self.thread.terminate()
                self.thread.wait()
                del self.thread,
            else:
                self.thread.quit()
                self.thread.wait()
        except:
            return

    def threadStop(self):
        self.thread.quit()

    @Slot(QAbstractButton)
    def buttonBox_clicked(self, button: QAbstractButton):
        try:
            if button == self.buttonBox.button(QDialogButtonBox.Ok):
                if not self.check_paras():
                    return

                #  最后运算过程放至到另一个线程避免GUI卡住
                self.thread = QThread()
                self.crawlVectorThread = crawlVectorWorker()
                self.crawlVectorThread.moveToThread(self.thread)
                self.crawlVectorThread.crawl.connect(self.crawlVectorThread.crawlVector)
                self.crawlVectorThread.crawlBatch.connect(self.crawlVectorThread.crawlVectorBatch)
                self.crawlVectorThread.finished.connect(self.threadStop)

                self.thread.start()
                self.run_process()
            elif button == self.buttonBox.button(QDialogButtonBox.Cancel):
                self.threadTerminate()
                self.close()
        except:
            return

    def run_process(self):
        rows = range(0, self.tbl_address.model().rowCount(QModelIndex()))
        for row in rows:
            url_index, service_index, url, service = self.return_url_and_level(row)
            # layername_index = self.tbl_address.model().index(row, 2, QModelIndex())
            output_index = self.tbl_address.model().index(row, 3, QModelIndex())
            # layername = str(self.tbl_address.model().data(layername_index, Qt.DisplayRole)).strip()
            output = str(self.tbl_address.model().data(output_index, Qt.DisplayRole)).strip()
            subscription_token = self.txt_subscriptionToken.text()
            api_token = self.txt_apiToken.text()

            if service != "*":
                key = url + "_" + str(service)
                sr = self.paras[key]['spatialReference']
                service = self.paras[key]['service']
                service_name = self.paras[key]['service_name']
                layername = self.paras[key]['new_layername']
                if url[-1] == r"/":
                    res_url = url + str(service)
                else:
                    res_url = url + "/" + str(service)

                if self.paras[key]['output'] != "":
                    output = self.paras[key]['output']

                if layername == "":
                    layername = self.paras[key]['old_layername']

                # crawl_vector(res_url, service_name=service_name, layer_order=service, layer_name=layername, output_path=output, sr=sr)
                self.crawlVectorThread.crawl.emit(res_url, service_name, str(service), layername, output,
                                                  api_token, subscription_token, sr, log)
            else:
                key_all = url + "_*"
                if self.paras[key_all]['output'] != "":
                    output = self.paras[key_all]['output']

                self.crawlVectorThread.crawlBatch.emit(url, key_all, output, api_token, subscription_token, self.paras, log)

    def check_paras(self):
        rows = range(0, self.tbl_address.model().rowCount(QModelIndex()))
        for row in rows:
            url_index, service_index, url, service = self.return_url_and_level(row)
            layername_index = self.tbl_address.model().index(row, 2, QModelIndex())
            output_index = self.tbl_address.model().index(row, 3, QModelIndex())
            layername = str(self.tbl_address.model().data(layername_index, Qt.DisplayRole)).strip()
            output = str(self.tbl_address.model().data(output_index, Qt.DisplayRole)).strip()

            if url == "":
                log.error('第{}行缺失必要参数"地址"，请补全！'.format(row), dialog=True)
                return False
            if service == "":
                log.error('第{}行缺失必要参数"服务号"，请补全！'.format(row), dialog=True)
                return False

            # in_format = get_suffix(in_path)
            # if in_format is None:
            #     log.error('第{}行的输入数据格式不支持！目前只支持csv, excel和dbf'.format(row), dialog=True)
            #     return False
            # else:
            #     in_wks = workspaceFactory().get_factory(in_format)
            #     if in_wks.driver is None:
            #         log.error("缺失图形文件引擎{}!".format(in_wks.driverName))
            #         return False

            out_format = get_suffix(output)
            out_wks = workspaceFactory().get_factory(DataType.fileGDB)

            if out_wks.driver is None:
                log.error("缺失图形文件引擎{}!".format(out_wks.driverName))
                return False

            if service != "*":
                key = url + "_" + str(service)
                url_lst = url.split(r'/')
                service_name = url_lst[-2]
                # filepath, filename = os.path.split(output)

                if layername == "":
                    layername = self.paras[key]['old_layername']
                    log.warning('第{}行缺失非必要参数"输出图层名"，将使用默认值"{}".'.format(row + 1, layername))

                if out_format != DataType.fileGDB:
                # if os.path.splitext(filename)[1] != '.gdb':
                    gdb_name = service_name + ".gdb"
                    if key in self.paras:
                        if output == "":
                            if not os.path.exists("res"):
                                os.makedirs("res")
                            output = os.path.join(os.path.abspath("res"), gdb_name)
                            self.paras[key]['output'] = output
                            log.warning('第{}行缺失非必要参数"输出路径"，将使用默认值"{}".'.format(row + 1, output))
                        else:
                            output = os.path.join(output, gdb_name)
                            self.paras[key]['output'] = output
                            log.warning('第{}行"输出路径"参数缺失输出gdb数据库名，将使用默认值"{}".'.format(row + 1, gdb_name))
                    else:
                        log.error("{}地址填写错误.".format(url))
                        return False
            else:
                key_all = url + "_*"
                if out_format != DataType.fileGDB:
                    gdb_name = urlEncodeToFileName(url) + ".gdb"
                    if output == "":
                        if not os.path.exists("res"):
                            os.makedirs("res")
                        output = os.path.abspath("res")
                        self.paras[key_all]['output'] = output
                        log.warning('第{}行缺失非必要参数"输出路径"，将使用默认值"{}".'.format(row + 1, output))
                    else:
                        self.paras[key_all]['output'] = output
                        log.warning('第{}行"输出路径"参数缺失输出gdb数据库名，将使用默认值"{}".'.format(row + 1, gdb_name))

                    gdb_name = urlEncodeToFileName(url) + ".gdb"
                    output = os.path.join(output, gdb_name)
                    self.paras[key_all]['output'] = output
                    log.warning('第{}行缺失非必要参数"输出路径"，将使用默认值"{}".'.format(row + 1, output))


                # filepath, filename = os.path.split(output)
                # key_all = url + "_*"
                # if out_format != DataType.fileGDB:
                #     gdb_name = urlEncodeToFileName(url) + ".gdb"
                #     output = os.path.join(output, gdb_name)
                #     self.paras[key_all]['output'] = output
                #     log.warning('第{}行缺失非必要参数"输出路径"，将使用默认值"{}".'.format(row + 1, output))
        return True

    @Slot(int)
    def table_section_clicked(self, section):
        self.row_clicked(section)

    @Slot(QModelIndex)
    def table_index_clicked(self, index):
        self.row_clicked(index.row())

    @Slot()
    def btn_addRow_Clicked(self):
        selModel = self.tbl_address.selectionModel()
        if selModel is None:
            return
        if len(selModel.selectedIndexes()) == 0:
            self.model.addEmptyRow(self.model.rowCount(QModelIndex()), 1, 0)
            next_index = self.model.index(self.model.rowCount(QModelIndex()) - 1, 0)
        elif len(selModel.selectedRows()) == 1:
            next_row = selModel.selectedRows()[0].row() + 1
            self.model.addEmptyRow(next_row, 1, 0)
            next_index = self.model.index(next_row, 0)

        selModel.select(next_index, QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)
        self.tbl_address.setFocus()

    @Slot()
    def btn_removeBtn_clicked(self):
        index_list = []
        selModel = self.tbl_address.selectionModel()
        if selModel is None:
            return
        if len(selModel.selectedRows()) < 1:
            return
        for model_index in selModel.selectedRows():
            index = QPersistentModelIndex(model_index)
            index_list.append(index)

        oldrow = index.row()
        for index in index_list:
            self.model.removeRows(index.row(), 1, 0)

        if self.model.rowCount(QModelIndex()) == 1:
            next_index = self.model.index(0, 0)
        else:
            next_index = self.model.index(oldrow, 0)
        # next_index = self.model.index(self.model.rowCount(QModelIndex()) - 1, 0)
        selModel.select(next_index, QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)
        self.tbl_address.setFocus()

    @Slot()
    def open_addressFile(self):
        fileName, fileType = QFileDialog.getOpenFileName(self, "选择矢量服务参数文件", os.getcwd(),
                                                                   "All Files(*)")
        self.txt_addressFile.setText(fileName)

        if fileName == "":
            return

        try:
            with open(fileName, 'r', encoding='utf-8') as f:
                self.paras = json.load(f)

            self.add_address_rows_from_paras()
        except:
            if self.model.rowCount(QModelIndex()) > 0:
                self.model.removeRows(self.model.rowCount(QModelIndex()) - 1, 1, QModelIndex())
            log.error("读取参数文件失败！", dialog=True)

    def add_address_rows_from_paras(self):
        keys = self.paras["exports"]
        for key in keys:
            if key in self.paras:
                row = self.model.rowCount(QModelIndex())
                self.model.addEmptyRow(self.model.rowCount(QModelIndex()), 1, 0)

                url = self.paras[key]['url']
                service = self.paras[key]['service']
                output = self.paras[key]['output']
                layername = self.paras[key]['new_layername']

                url_index = self.tbl_address.model().index(row, 0)
                self.tbl_address.model().setData(url_index, url)
                service_index = self.tbl_address.model().index(row, 1)
                self.tbl_address.model().setData(service_index, service)
                index = self.tbl_address.model().index(row, 2)
                self.tbl_address.model().setData(index, layername)
                index = self.tbl_address.model().index(row, 3)
                self.tbl_address.model().setData(index, output)

                editor_delegate = self.tbl_address.itemDelegate(service_index)
                key_all = url + "_*"

                if key_all in self.paras:
                    services = self.paras[key_all]['services']
                    if isinstance(editor_delegate, vectorTableDelegate):
                        self.model.setLevelData(key, services)

    @Slot()
    def btn_saveMetaFile_clicked(self):
        datas = self.tbl_address.model().datas

        bHasData = False
        for i in datas:
            for j in i:
                if j != '':
                    bHasData = True
                    break
            else:
                continue
            break

        rows = range(0, len(datas))
        if bHasData and bool(self.paras):
            fileName, fileType = QFileDialog.getSaveFileName(self, "请选择保存的参数文件", os.getcwd(),
                                                             "json file(*.json)")

            self.paras['exports'] = []

            for row in rows:
                url = datas[row][self.url_no]
                service = datas[row][self.service_no]

                if service == "":
                    continue

                key = str(url) + "_" + str(service)

                if key in self.paras:
                    self.paras[key]['new_layername'] = datas[row][2]
                    self.paras[key]['output'] = datas[row][3]
                    self.paras['exports'].append(key)
        try:
            if fileName != '':
                with open(fileName, 'w', encoding='UTF-8') as f:
                    json.dump(self.paras, f, ensure_ascii=False)
        except:
            log.error("文件存储路径错误，无法保存！", parent=self, dialog=True)

    def table_init(self):
        self.tbl_address.setStyle(mTableStyle())

        self.tbl_address.horizontalHeader().setStretchLastSection(True)
        self.tbl_address.verticalHeader().setDefaultSectionSize(20)
        self.tbl_address.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)  # 行高固定

        color = self.palette().color(QPalette.Button)
        self.tbl_address.horizontalHeader().setStyleSheet(
            "QHeaderView::section {{ background-color: {}}}".format(color.name()))
        self.tbl_address.verticalHeader().setStyleSheet(
            "QHeaderView::section {{ background-color: {}}}".format(color.name()))
        self.tbl_address.setStyleSheet(
            "QTableCornerButton::section {{ color: {}; border: 1px solid; border-color: {}}}".format(color.name(),
                                                                                                     color.name()))

        self.tbl_address.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tbl_address.setEditTriggers(QAbstractItemView.SelectedClicked | QAbstractItemView.DoubleClicked)
        self.tbl_address.DragDropMode(QAbstractItemView.InternalMove)
        self.tbl_address.setSelectionBehavior(QAbstractItemView.SelectRows | QAbstractItemView.SelectItems)
        self.tbl_address.setDefaultDropAction(Qt.MoveAction)

        self.tbl_address.horizontalHeader().setSectionsMovable(False)
        self.tbl_address.setDragEnabled(True)
        self.tbl_address.setAcceptDrops(True)

        self.service_no = 1  # 服务名字段的序号
        self.url_no = 0  # url地址的序号

        self.model = TableModel()

        self.model.setHeaderData(0, Qt.Horizontal, "地址", Qt.DisplayRole)
        self.model.setHeaderData(1, Qt.Horizontal, "服务号", Qt.DisplayRole)
        self.model.setHeaderData(2, Qt.Horizontal, "输出图层名", Qt.DisplayRole)
        self.model.setHeaderData(3, Qt.Horizontal, "输出路径", Qt.DisplayRole)

        delegate = vectorTableDelegate(self, [None, {'type': 'c'}, None,
                                              {'text': "请选择或创建文件数据库", 'type': "d"}])
        self.tbl_address.setModel(self.model)
        self.tbl_address.setItemDelegate(delegate)

    @Slot()
    def btn_obtainMeta_clicked(self):
        try:
            selModel = self.tbl_address.selectionModel()

            if selModel is None:
                return

            indexes = selModel.selectedIndexes()

            ## 如果有被选中的行，则只获取被选中行的信息
            if len(indexes) > 0:
                rows = sorted(set(index.row() for index in
                                  self.tbl_address.selectedIndexes()))
            else:
                rows = range(0, self.tbl_address.model().rowCount(QModelIndex()))

            subscription_token = self.txt_subscriptionToken.text()
            if subscription_token != '':
                global reqheaders
                reqheaders['X-OPENAPI-SubscriptionToken'] = subscription_token

            for row in rows:
                url_index, service_index, url, service = self.return_url_and_level(row)
                editor_delegate = self.tbl_address.itemDelegate(service_index)

                if url == "": continue

                getInfo = get_paraInfo(url, reqheaders=reqheaders)

                key = url + "_*"
                if getInfo is None:
                    log.error(url + "无法获取远程参数信息，请检查地址是否正确以及网络是否连通！")
                    continue
                else:
                    log.info(url + "参数信息获取成功！")

                self.setAllParaToMemory(url, getInfo)

                services = self.paras[key]['services']
                if isinstance(editor_delegate, vectorTableDelegate):
                    self.model.setLevelData(key, services)

                if service != "*" and service != "":
                    layername_index = self.tbl_address.model().index(row, 2)
                    if url + "_" + str(service) in self.paras:
                        layername = self.paras[url + "_" + str(service)]['old_layername']
                        self.tbl_address.model().setData(layername_index, layername)
        except:
            log.error("无法获取远程参数，错误原因：\n{}".format(traceback.format_exc()))

    def setAllParaToMemory(self, url, getInfo):
        xmin = xmax = ymin = ymax = sp = ""

        services = ["*"]
        if 'layers' in getInfo.keys():
            layers = getInfo['layers']
            for layer in layers:
                if 'subLayerIds' in layer:
                    if layer['subLayerIds'] is None:
                        if 'id' in layer:
                            service = layer['id']
                            services.append(service)
                            new_url = url + "/" + str(service)
                            layer_getInfo = get_paraInfo(new_url, reqheaders=reqheaders)
                            self.setParaToMemory(url, str(service), layer_getInfo)

        if 'fullExtent' in getInfo.keys():
            if 'xmin' in getInfo['fullExtent']:
                xmin = getInfo['fullExtent']['xmin']
            if 'xmax' in getInfo['fullExtent']:
                xmax = getInfo['fullExtent']['xmax']
            if 'ymin' in getInfo['fullExtent']:
                ymin = getInfo['fullExtent']['ymin']
            if 'ymax' in getInfo['fullExtent']:
                ymax = getInfo['fullExtent']['ymax']

        if 'spatialReference' in getInfo.keys():
            if 'wkid' in getInfo['spatialReference']:
                sp = getInfo['spatialReference']['wkid']

        url_encodeStr = urlEncodeToFileName(url)
        self.paras[url + "_*"] = {
            'url': url,
            'service': "*",
            'code': url_encodeStr,
            'services': services,
            'xmin': xmin,
            'xmax': xmax,
            'ymin': ymin,
            'ymax': ymax,
            'spatialReference': sp,
            "output": ""
        }

    def setParaToMemory(self, url, service, getInfo):
        xmin = xmax = ymin = ymax = sp = layername = ""

        key = url + "_" + service

        if 'id' in getInfo.keys():
            service = getInfo['id']
            if 'name' in getInfo.keys():
                layername = getInfo['name']

        if service == "": return

        if 'extent' in getInfo.keys():
            if 'xmin' in getInfo['extent']:
                xmin = getInfo['extent']['xmin']
            if 'xmax' in getInfo['extent']:
                xmax = getInfo['extent']['xmax']
            if 'ymin' in getInfo['extent']:
                ymin = getInfo['extent']['ymin']
            if 'ymax' in getInfo['extent']:
                ymax = getInfo['extent']['ymax']
            if 'spatialReference' in getInfo['extent']:
                if 'wkid' in getInfo['extent']['spatialReference']:
                    sp = getInfo['extent']['spatialReference']['wkid']

        url_encodeStr = urlEncodeToFileName(url)
        url_lst = url.split(r'/')
        service_name = url_lst[-2]
        self.paras[key] = {
            'url': url,
            'service': service,
            'service_name': service_name,
            'code': url_encodeStr,
            'old_layername': layername,
            'xmin': xmin,
            'xmax': xmax,
            'ymin': ymin,
            'ymax': ymax,
            'spatialReference': sp,
            'new_layername': "",
            'output': ""
        }

    def row_clicked(self, logicRow):
        sel_index = self.tbl_address.model().index(logicRow, 0, QModelIndex())
        self.update_txt_info(sel_index)
        self.selIndex = sel_index

    def return_url_and_level(self, logicRow):
        url_index = self.tbl_address.model().index(logicRow, self.url_no)
        level_index = self.tbl_address.model().index(logicRow, self.service_no)
        url = self.tbl_address.model().data(url_index, Qt.DisplayRole)
        level = self.tbl_address.model().data(level_index, Qt.DisplayRole)
        return url_index, level_index, url, level

    def update_txt_info(self, index: QModelIndex, level=-1):
        # key1_index = self.tbl_address.model().index(index.row(), 0)
        # key1 = self.tbl_address.model().data(key1_index, Qt.DisplayRole)
        # key2_index = self.tbl_address.model().index(index.row(), 1)
        # key2 = self.tbl_address.model().data(key2_index, Qt.DisplayRole)
        key1_index, key2_index, key1, key2 = self.return_url_and_level(index.row())

        self.txt_xmin.setText("")
        self.txt_xmax.setText("")
        self.txt_ymin.setText("")
        self.txt_ymax.setText("")
        self.txt_spatialReference.setText("")
        self.lbl_layer.setText("")

        if level == -1:
            key = key1 + "_" + str(key2)
        else:
            key = key1 + "_" + str(level)

        if key not in self.paras:
            return

        getInfo = self.paras[key]

        if 'old_layername' in getInfo:
            self.lbl_layer.setText(str(getInfo['old_layername']))
            layername_index = self.tbl_address.model().index(index.row(), 2)
            if key1 + "_" + str(level) in self.paras:
                layername = self.paras[key1 + "_" + str(level)]['old_layername']
                self.tbl_address.model().setData(key2_index, level)
                self.tbl_address.model().setData(layername_index, layername)
        if 'xmin' in getInfo:
            self.txt_xmin.setText(str(getInfo['xmin']))
            self.txt_xmin.home(False)
        if 'xmax' in getInfo:
            self.txt_xmax.setText(str(getInfo['xmax']))
            self.txt_xmax.home(False)
        if 'ymin' in getInfo:
            self.txt_ymin.setText(str(getInfo['ymin']))
            self.txt_ymin.home(False)
        if 'ymax' in getInfo:
            self.txt_ymax.setText(str(getInfo['ymax']))
            self.txt_ymax.home(False)
        if 'spatialReference' in getInfo:
            self.txt_spatialReference.setText(str(getInfo['spatialReference']))
            self.txt_spatialReference.home(False)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    style = QStyleFactory.create("windows")
    app.setStyle(style)
    window = Ui_Window()
    window.setWindowFlags(Qt.Window)
    window.show()
    sys.exit(app.exec_())
