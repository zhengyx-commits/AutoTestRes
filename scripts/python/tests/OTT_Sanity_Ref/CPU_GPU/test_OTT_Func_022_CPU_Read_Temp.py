import logging
import time
import re
import pytest
from lib.common.system.SerialPort import SerialPort
from lib.common.system.ADB import ADB

adb = ADB()
p_result_path = f'{pytest.result_dir}/../../cpu_gpu_info.log'


def test_022_CPU_Read_Temp():
    serialcmd = SerialPort()
    assert serialcmd.enter_uboot()
    serialcmd.write('\x0d')
    serialcmd.write('\x0d')
    serialcmd.write('\x0d')
    serialcmd.write("read_temp")
    time.sleep(0.5)
    data = serialcmd.recv()
    data = data.strip().splitlines()
    for i in data:
        read_temp = re.findall(r'temp1: (\d+)', i)
        logging.info(f"res:{read_temp}")
        if read_temp:
            if int(read_temp[0]) > 0:
                f = open(p_result_path, 'a')
                f.write(f'Time : {time.asctime()} \n')
                f.write(f'read_temp: {read_temp[0]}' + '\n')
                f.write('-' * 20 + '\n')
                f.close()
                assert True, f'CPU Temp : {read_temp[0]}'
            else:
                assert False
    serialcmd.write('\n')
    serialcmd.write("reboot")
    time.sleep(40)
    adb.root()
