from UICore.pycomcad import *
import os
import time
import click
import traceback
from enum import Enum
from UICore.log4p import Log

log = Log(__file__)

@click.command()
@click.option(
    '--input', '-i',
    help='input dxf file. For example, "data/input.dxf"',
    required=True)
@click.option(
    '--type', '-t',
    help='coordinate transform type. '
         '1 - shenzhen local to CGCS2000(PCS)'
         '2 - CGCS2000(PCS) to shenzhen local',
    type=int,
    required=True)
@click.option(
    '--output', '-o',
    help='ouput dxf file. For example, "res/output.dxf"',
    required=True)
def main(input, type, output):
    transform_dwg(input, type, output)


def transform_dwg(input, type, output):
    # cur_path = os.path.abspath('.')
    # log.info("checking parameters...")
    input_dir = os.path.abspath(os.path.dirname(input))
    input_file_name = os.path.basename(input)
    output_dir = os.path.abspath(os.path.dirname(output))
    output_file_name = os.path.basename(output)

    if not os.path.exists(input):
        log.error("输入的dwg文件不存在!")
        return None

    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    log.info("启动AutoCAD进程...")

    try:
        trytime = 0
        while trytime < 5:
            try:
                acad = Autocad()
                break
            except:
                time.sleep(1)
                trytime = trytime + 1
                continue
        else:
            log.error("未正确读取autocad的com接口,请检查是否正确安装!")
            return None

        # ACADPref = acad.Preferences.OpenSave
        # print(ACADPref.SaveAsType)

        # log.info("读取转换矩阵...")
        mat = None
        if type == transform_type.szlocal_to_cgcs2000_pcs.value:
            # tmatrix = szlocal_to_cgcs2000_mat()
            mat = sz_local_to_pcs_2000_mat
        elif type == transform_type.cgcs2000_pcs_to_szlocal.value:
            # tmatrix = cgcs2000_to_szlocal_mat()
        # mat = Matrix44_to_pmat(tmatrix)
            mat = pcs_2000_to_sz_local_mat

        if mat is None:
            log.error("不存在对应的转换矩阵!")
            return None

        mat = ArrayTransform(mat)

        log.info("打开dwg文件...")
        trytime = 0

        while trytime < 10:
            try:
                # doc = acad.Documents
                time.sleep(1)
                # doc = acad.OpenFile(input, True)
                # doc = doc.Open(input_dir + os.sep + input_file_name, True)
                doc = acad.OpenFile(input_dir + os.sep + input_file_name)
                msp = doc.ModelSpace
                layers = doc.Layers
                break
            except:
                # print("try{}".format(trytime))
                time.sleep(1)
                trytime += 1
                continue
        else:
            log.error("打开dwg文件失败!\n{}".format(traceback.format_exc()))
            return False

        trytime = 0
        for layer in layers:
            while trytime < 5:
                try:
                    if layer.Lock:
                        layer.Lock = False
                        trytime = 0
                        break
                    else:
                        break
                except:
                    time.sleep(0.5)
                    trytime = trytime + 1
            else:
                log.error("图层{}在解锁过程中发生出错.".format(layer.Name) + os.linesep + traceback.format_exc())

        total_count = msp.count

        log.info("开始转换{}个entities...".format(total_count))

        icount = 0
        iprop = 1
        ierror_num = 0
        isuccess_num = 0
        trytime = 0
        while icount < total_count:
            try:
                entity = msp.Item(icount)
                entity.TransformBy(mat)
                # if icount % 1000 == 0 and icount > 0:
                #     log.debug("{}个entities 转换成功.".format(icount))

                icount = icount + 1
                if int(icount * 100 / total_count) == iprop * 20:
                    log.debug("{:.0%}".format(icount / total_count))
                    iprop += 1

                isuccess_num = isuccess_num + 1
                trytime = 0
            except:
                time.sleep(0.5)
                if trytime < 5:
                    trytime = trytime + 1
                else:
                    log.error("handle{}发生错误.".format(entity.Handle) + os.linesep + traceback.format_exc())
                    ierror_num = ierror_num + 1
                    icount = icount + 1
                continue

        # log.info("保存结果...")
        doc.SaveAs(output_dir + os.sep + output_file_name)
        acad.Quit()
        log.info("dwg文件转换完成! Success: {}, Failure: {}".format(isuccess_num, ierror_num))
        return output, output_file_name
    except:
        log.error("转换失败.\n{}".format(traceback.format_exc()))
        return None
    finally:
        if acad is not None:
            acad.Close(False)


class transform_type(Enum):
    szlocal_to_cgcs2000_pcs = 1
    cgcs2000_pcs_to_szlocal = 2


sz_local_to_pcs_2000_mat = [
    [0.999851891277719, -0.017059492344403574, 0.0, 391090.578943],
    [0.017059492344403574, 0.999851891277719, 0.0, 2472660.600279],
    [0.0, 0.0, 0.999997415382, 0.0],
    [0.0, 0.0, 0.0, 1.0]]


pcs_2000_to_sz_local_mat = [
    [0.9998570597684675, 0.01705958052929288, 0.0, -433217.228947],
    [-0.01705958052929288, 0.9998570597684675, 0.0, -2465635.316383],
    [0.0, 0.0, 1.000002584625, 0.0],
    [0.0, 0.0, 0.0, 1.0]]


if __name__ == '__main__':
    main()

