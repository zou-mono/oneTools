import time

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal, QMutex
from suplicmap_tilemap import craw_tilemap
from merge_tiles import merge_tiles
from UICore.log4p import Log

log = Log()

class crawlTilesWorker(QtCore.QObject):
    crawl = pyqtSignal(str, int, int, int, float, float, float, float, float, int, str)
    crawlAndMerge = pyqtSignal(str, int, int, int, float, float, float, float, float, int, str, str)
    merge = pyqtSignal(str, int, int, float, float, float, float, float, int, str)
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
        self.finished.emit()

    def crawlAndMergeTiles(self, url, level, x0, y0, xmin, xmax, ymin, ymax, resolution, tile_size, output_path, merged_file):
        craw_tilemap(url, level, x0, y0, xmin, xmax, ymin, ymax, resolution, tile_size, output_path)
        merge_tiles(output_path, [xmin, xmax, ymin, ymax], [x0, y0], resolution, tile_size, merged_file)

        self.finished.emit()

    def mergeTiles(self, output_path, x0, y0, xmin, xmax, ymin, ymax, resolution, tile_size, merged_file):
        merge_tiles(output_path, [xmin, xmax, ymin, ymax], [x0, y0], resolution, tile_size, merged_file)

        self.finished.emit()




