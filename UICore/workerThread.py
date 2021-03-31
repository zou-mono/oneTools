import time

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal
from suplicmap_tilemap import craw_tilemap
from UICore.log4p import Log

log = Log()

class crawlTilesWorker(QtCore.QObject):
    crawl = pyqtSignal(str, int, int, int, float, float, float, float, float, int, str)
    finished = pyqtSignal()

    def __init__(self):
        super(crawlTilesWorker, self).__init__()

    def crawlTiles(self, url, level, x0, y0, xmin, xmax, ymin, ymax, resolution, tile_size, output_path):
        # count = 0
        # while count < 50:
        #     time.sleep(1)
        #     print("B Increasing")
        #     count += 1
        craw_tilemap(url, level, x0, y0, xmin, xmax, ymin, ymax, resolution, tile_size, output_path)
        log.info('爬取瓦片任务全部完成！瓦片存储至{}.'.format(output_path))
        self.finished.emit()




