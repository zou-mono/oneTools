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
    crawl = pyqtSignal(str, int, int, int, float, float, float, float, float, int, str, str, str, object)
    crawlAndMerge = pyqtSignal(str, int, int, int, float, float, float, float, float, int, str, bool, str, str, str, str, object)
    merge = pyqtSignal(str, int, int, float, float, float, float, float, int, str, bool, str, object)
    finished = pyqtSignal(bool)

    def __init__(self):
        super(crawlTilesWorker, self).__init__()

    def crawlTiles(self, url, level, x0, y0, xmin, xmax, ymin, ymax, resolution, tile_size,
                   api_token, subscription_token, output_path, log):
        # count = 0
        # while count < 50:
        #     time.sleep(1)
        #     print("B Increasing")
        #     count += 1
        bflag = crawl_tilemap(url, level, x0, y0, xmin, xmax, ymin, ymax, resolution, tile_size,
                      api_token, subscription_token, output_path, log)
        self.finished.emit(bflag)

    def crawlAndMergeTiles(self, url, level, x0, y0, xmin, xmax, ymin, ymax, resolution, tile_size, pixelType, bCompression,
                           output_path, api_token, subscription_token, merged_file, log):
        bflag1 = crawl_tilemap(url, level, x0, y0, xmin, xmax, ymin, ymax, resolution, tile_size,
                      api_token, subscription_token, output_path, log)
        bflag2 = merge_tiles(output_path, [xmin, xmax, ymin, ymax], [x0, y0], resolution, tile_size, pixelType,
                    bCompression, merged_file, log)

        bflag = bflag1 and bflag2
        self.finished.emit(bflag)

    def mergeTiles(self, output_path, x0, y0, xmin, xmax, ymin, ymax, resolution, tile_size,
                   pixelType, bCompression, merged_file, log):
        bflag = merge_tiles(output_path, [xmin, xmax, ymin, ymax], [x0, y0], resolution, tile_size,
                    pixelType, bCompression, merged_file, log)

        self.finished.emit(bflag)


class crawlVectorWorker(QtCore.QObject):
    crawl = pyqtSignal(str, str, str, str, str, str, str, int, object)
    crawlBatch = pyqtSignal(str, str, str, str, str, object, object)
    finished = pyqtSignal()

    def __init__(self):
        super(crawlVectorWorker, self).__init__()

    def crawlVector(self, url, service_name, layer_order, layer_name, output_path, api_token, subscription_token, sr, logClass):
        flag, message = crawl_vector(url, service_name, layer_order, layer_name, output_path, sr, api_token, subscription_token, logClass)
        if not flag:
            log.error(message)
        self.finished.emit()

    def crawlVectorBatch(self, url, key, output, api_token, subscription_token, paras, logClass):
        crawl_vector_batch(url, key, output, api_token, subscription_token, paras, logClass)
        self.finished.emit()


class coordTransformWorker(QtCore.QObject):
    transform = pyqtSignal(str, str, int, str, str, int, object)
    transform_tbl = pyqtSignal(str, str, bool, int, int, int, int, str, str, object)
    finished = pyqtSignal()

    def __init__(self):
        super(coordTransformWorker, self).__init__()

    def coordTransform(self, inpath, inlayer, insrs, outpath, outlayer, outsrs, logClass):
        flag = coordTransform(inpath, inlayer, insrs, outpath, outlayer, outsrs, logClass)
        # if not flag:
        #     log.error(message)
        self.finished.emit()

    def tableTransform(self, inpath, inencode, header, xfield, yfield, insrs, outsrs, outpath, outencode, logClass):
        flag = UICore.coordTransform_table.coordTransform(
            inpath, inencode, header, xfield, yfield, insrs, outsrs, outpath, outencode, logClass)
        # if not flag:
        #     log.error(message)
        self.finished.emit()


class updateLandUseTypeWorker(QtCore.QObject):
    update = pyqtSignal(object, str, str, object, object, object, object, str, bool, bool, bool, bool, bool, object)
    finished = pyqtSignal(bool)

    def __init__(self):
        super(updateLandUseTypeWorker, self).__init__()

    def updateAttribute(self, file_type, in_path, layer_name, header, rel_tables, MC_tables, DLBM_values, report_file_name,
                        bConvert, bReport1, bReport2, bReport3, bReport4, logClass):
        flag = update_and_stat(file_type, in_path, layer_name, header, rel_tables, MC_tables, DLBM_values, report_file_name,
                        bConvert, bReport1, bReport2, bReport3, bReport4, logClass)
        self.finished.emit(flag)
