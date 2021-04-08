from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal
from UICore.suplicmap_tilemap import crawl_tilemap
from UICore.merge_tiles import merge_tiles
from UICore.log4p import Log
from UICore.suplicmap_vector2 import crawl_vector, crawl_vector_batch

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
        crawl_tilemap(url, level, x0, y0, xmin, xmax, ymin, ymax, resolution, tile_size, output_path)
        self.finished.emit()

    def crawlAndMergeTiles(self, url, level, x0, y0, xmin, xmax, ymin, ymax, resolution, tile_size, output_path, merged_file):
        crawl_tilemap(url, level, x0, y0, xmin, xmax, ymin, ymax, resolution, tile_size, output_path)
        merge_tiles(output_path, [xmin, xmax, ymin, ymax], [x0, y0], resolution, tile_size, merged_file)

        self.finished.emit()

    def mergeTiles(self, output_path, x0, y0, xmin, xmax, ymin, ymax, resolution, tile_size, merged_file):
        merge_tiles(output_path, [xmin, xmax, ymin, ymax], [x0, y0], resolution, tile_size, merged_file)

        self.finished.emit()

class crawlVectorWorker(QtCore.QObject):
    crawl = pyqtSignal(str, str, str, str, str, int)
    crawlBatch = pyqtSignal(str, str, str, object)
    finished = pyqtSignal()

    def __init__(self):
        super(crawlVectorWorker, self).__init__()

    def crawlVector(self, url, service_name, layer_order, layer_name, output_path, sr):
        flag, message = crawl_vector(url, service_name, layer_order, layer_name, output_path, sr)
        if not flag:
            log.error(message)
        self.finished.emit()

    def crawlVectorBatch(self, url, key, output, paras):
        crawl_vector_batch(url, key, output, paras)
        self.finished.emit()




