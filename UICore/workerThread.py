from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal, QThread
from UICore.suplicmap_tilemap import crawl_tilemap
from UICore.merge_tiles2 import merge_tiles
from UICore.log4p import Log
from UICore.suplicmap_vector2 import crawl_vector, crawl_vector_batch
from UICore.coordTransform import coordTransform
import UICore.coordTransform_table
from UICore.updateLandUseType import update_and_stat

log = Log(__name__)


class crawlTilesWorker(QtCore.QObject):
    crawl = pyqtSignal(str, int, int, int, float, float, float, float, float, int, str)
    crawlAndMerge = pyqtSignal(str, int, int, int, float, float, float, float, float, int, str, bool, str, str)
    merge = pyqtSignal(str, int, int, float, float, float, float, float, int, str, bool, str)
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

    def crawlAndMergeTiles(self, url, level, x0, y0, xmin, xmax, ymin, ymax, resolution, tile_size, pixelType, bCompression, output_path, merged_file):
        crawl_tilemap(url, level, x0, y0, xmin, xmax, ymin, ymax, resolution, tile_size, output_path)
        merge_tiles(output_path, [xmin, xmax, ymin, ymax], [x0, y0], resolution, tile_size, pixelType, bCompression, merged_file)

        self.finished.emit()

    def mergeTiles(self, output_path, x0, y0, xmin, xmax, ymin, ymax, resolution, tile_size, pixelType, bCompression, merged_file):
        merge_tiles(output_path, [xmin, xmax, ymin, ymax], [x0, y0], resolution, tile_size, pixelType, bCompression, merged_file)

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


class coordTransformWorker(QtCore.QObject):
    transform = pyqtSignal(str, str, int, str, str, int)
    transform_tbl = pyqtSignal(str, str, bool, int, int, int, int, str, str)
    finished = pyqtSignal()

    def __init__(self):
        super(coordTransformWorker, self).__init__()

    def coordTransform(self, inpath, inlayer, insrs, outpath, outlayer, outsrs):
        flag = coordTransform(inpath, inlayer, insrs, outpath, outlayer, outsrs)
        # if not flag:
        #     log.error(message)
        self.finished.emit()

    def tableTransform(self, inpath, inencode, header, xfield, yfield, insrs, outsrs, outpath, outencode):
        flag = UICore.coordTransform_table.coordTransform(
            inpath, inencode, header, xfield, yfield, insrs, outsrs, outpath, outencode)
        # if not flag:
        #     log.error(message)
        self.finished.emit()


class updateLandUseTypeWorker(QtCore.QObject):
    update = pyqtSignal(object, str, str, object, object, object, object, str, bool, bool, bool, bool, bool)
    finished = pyqtSignal(bool)

    def __init__(self):
        super(updateLandUseTypeWorker, self).__init__()

    def updateAttribute(self, file_type, in_path, layer_name, header, rel_tables, MC_tables, DLBM_values, report_file_name,
                        bConvert, bReport1, bReport2, bReport3, bReport4):
        flag = update_and_stat(file_type, in_path, layer_name, header, rel_tables, MC_tables, DLBM_values, report_file_name,
                        bConvert, bReport1, bReport2, bReport3, bReport4)
        self.finished.emit(flag)
