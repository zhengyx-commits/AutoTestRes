import time
import subprocess
from lib.common.system.ADB import ADB
import re
import logging

adb = ADB()


def test_019_ddr_bandwidth():
    ddr_freq = adb.run_shell_cmd("cat /sys/class/aml_ddr/freq")[1]
    ddr_freq = re.findall(r"(.*) MHz", ddr_freq)[0]
    logging.info(f"ddr_freq: {ddr_freq}")
    ddr_clk = int(ddr_freq) * 2
    assert ddr_clk >= 912

    adb.res_manager.get_target(path="test_bin/stressapptest_linux", source_path="test_bin/stressapptest_linux")
    adb.push("res/test_bin/stressapptest_linux", "/data")
    adb.run_shell_cmd("chmod 777 /data/stressapptest_linux")

    command = 'adb shell /data/stressapptest_linux -s 10 -m 10 -M 300 -W --pause_delay 10 --pause_duration 1 --max_errors 3 --printsec 5'

    try:
        output = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        logging.info(f"output.stdout: {output.stdout}")
        lines = output.stdout.strip().split('\n')
        bandwidth_result = 0
        for line in lines:
            if "Stats: Completed" in line:
                logging.info(f"line: {line}")
                bandwidth_result = re.findall(r".* Stats: Completed: .* (.*)?MB/s", line, re.S)[0]
                logging.info(f"bandwidth_result: {bandwidth_result}")
        refer_value = (ddr_clk * 2 * 32)/8
        assert float(bandwidth_result) >= (float(refer_value) * 0.6)
    except subprocess.CalledProcessError as e:
        logging.error(f"Error: {e}, {e.returncode}")






