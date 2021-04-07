from osgeo import gdal, ogr


class GdalErrorHandler(object):
    def __init__(self):
        self.err_level=gdal.CE_None
        self.err_no=0
        self.err_msg=''

    def handler(self, err_level, err_no, err_msg):
        self.err_level=err_level
        self.err_no=err_no
        self.err_msg=err_msg

if __name__=='__main__':

    err=GdalErrorHandler()
    handler=err.handler # Note don't pass class method directly or python segfaults
    # due to a reference counting bug
    # http://trac.osgeo.org/gdal/ticket/5186#comment:4

    # gdal.PushErrorHandler(handler)
    gdal.UseExceptions() #Exceptions will get raised on anything >= gdal.CE_Failure
    ogr.UseExceptions()

    try:
        # gdal.Error(gdal.CE_Warning,1,'Test warning message')
        outdriver = ogr.GetDriverByName('CAD')
        gdb = outdriver.Open("c:/sss", 1)

        ds = gdal.Open('test.tif')
    except Exception as e:
        print('Operation raised an exception')
        raise e
    # else:
    #     if err.err_level >= gdal.CE_Warning:
    #         print('Operation raised an warning')
    #         raise RuntimeError(err.err_level, err.err_no, err.err_msg)
    # finally:
    #     gdal.PopErrorHandler()