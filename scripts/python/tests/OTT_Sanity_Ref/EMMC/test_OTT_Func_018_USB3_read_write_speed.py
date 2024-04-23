from lib.common.system.ADB import ADB
from tools.resManager import ResManager
import pytest
import subprocess
import logging
import re
import allure
import os
import json


adb = ADB()
resmanager = ResManager()
read = ["adb", "-s", adb.serialnumber, "shell", "/system/bin/amldevread", "/dev/block/sda"]
write = ["adb", "-s", adb.serialnumber, "shell", "/system/bin/amldevwrite", "/dev/block/sda"]


@pytest.fixture(scope='function', autouse=True)
def setup_teardown():
    resmanager.get_target(path="test_bin/amldevwrite", source_path="test_bin/amldevwrite")
    resmanager.get_target(path="test_bin/amldevread", source_path="test_bin/amldevread")
    adb.push("res/test_bin/amldevwrite", "/system/bin/")
    adb.push("res/test_bin/amldevread", "/system/bin/")
    adb.run_shell_cmd("chmod 777 /system/bin/amldevread")
    adb.run_shell_cmd("chmod 777 /system/bin/amldevwrite")
    adb.run_shell_cmd("echo performance > /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor")


@allure.step("Test emmc read speed")
def test_018_read_speed():
    numbers = ""
    read_speed = get_speed("read", read)
    logging.info(f"read_speed: {read_speed}")
    for line in read_speed.values():
        numbers = line/1000
        save_to_allure_report(read_speed)
    logging.info(f"numbers: {numbers}")
    if numbers > 120:
        assert True
    else:
        assert False, f"read speed is slow: {numbers}"


@allure.step("Test emmc write speed")
def test_018_write_speed():
    numbers = ""
    write_speed = get_speed("write", write)
    logging.info(f"write_speed: {write_speed}")
    for line in write_speed.values():
        numbers = line/1000
        save_to_allure_report(write_speed)
    logging.info(f"numbers: {numbers}")
    if numbers > 15:
        assert True
    else:
        assert False, f"write speed is slow: {numbers}"


def get_speed(method, command):
    speed_line = {}
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    for line in process.stdout:
        if "block=" in line:
            print("line", line, end='')
            value = re.findall(r'\b\d+\b', line)[1]
            if not speed_line:
                speed_line[method] = int(value)
            else:
                if int(value) > speed_line[method]:
                    speed_line[method] = int(value)

    process.wait()
    return speed_line


@allure.title("emmc read and write speed")
def save_to_allure_report(speed_value):
    allure.attach(json.dumps(speed_value), name="emmc_read_write_speed", attachment_type=allure.attachment_type.JSON)