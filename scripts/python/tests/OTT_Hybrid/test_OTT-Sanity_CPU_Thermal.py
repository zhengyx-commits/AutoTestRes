from lib.common.system.CPU import CPU
import pytest
import logging
from . import *

p_conf_cpu_thermal = config_yaml.get_note('conf_cpu_thermal')
p_conf_thermal_enable = p_conf_cpu_thermal['thermal_enable']

cpu = CPU()


class TestOTTCPUTHERMAL:

    def test_OTT_Sanity_Func_045_046(self):
        actual_thermal_mode = cpu.temperature_control[1]
        logging.info(f"actual_thermal_mode: {actual_thermal_mode}")
        if actual_thermal_mode == "":
            assert False
        else:
            assert actual_thermal_mode == p_conf_thermal_enable

    def test_OTT_Sanity_Func_047(self):
        actual_thermal = cpu.run_shell_cmd(cpu.CPU_TEMPERATURE_COMMAND)[1]
        logging.info(f"actual_thermal:{actual_thermal}")
        if actual_thermal.isdigit() and (int(actual_thermal) != 0):
            assert True
        else:
            assert False


