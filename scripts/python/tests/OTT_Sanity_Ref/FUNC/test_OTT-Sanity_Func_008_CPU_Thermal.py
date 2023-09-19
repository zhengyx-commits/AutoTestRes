import time

from lib.common.system.CPU import CPU
from lib import get_device
import pytest
import logging
from tests.OTT_Sanity_Ref import config_yaml
from tests import *

p_conf_cpu_thermal = config_yaml.get_note('conf_cpu_thermal')
p_conf_thermal_mode = p_conf_cpu_thermal['thermal_mode']
for g_config_device_id in get_device():
    cpu = CPU(serialnumber=g_config_device_id)
p_result_path = f'{pytest.result_dir}/../../cpu_gpu_info.log'


class TestOTTCPUTHERMAL:

    def test_OTT_Sanity_Func_045_046(self):
        actual_thermal_mode = cpu.temperature_control[1]
        logging.info(f"cpu actual_thermal_mode: {actual_thermal_mode}")
        if actual_thermal_mode == "":
            assert False
        else:
            f = open(p_result_path, 'a')
            f.write(f'Time : {time.asctime()} \n')
            f.write(f'cpu actual thermal mode: {actual_thermal_mode}')
            f.write('\n')
            f.close()
            assert actual_thermal_mode == p_conf_thermal_mode, f'cpu actual thermal mode not match {p_conf_thermal_mode}'

    def test_OTT_Sanity_Func_047(self):
        actual_thermal = cpu.run_shell_cmd(cpu.CPU_TEMPERATURE_COMMAND)[1]
        logging.info(f"cpu actual_thermal:{actual_thermal}")
        if actual_thermal.isdigit() and (int(actual_thermal) != 0):
            f = open(p_result_path, 'a')
            f.write(f'cpu actual thermal: {actual_thermal}' + '\n')
            f.write('-' * 20 + '\n')
            f.close()
            assert True
        else:
            assert False
