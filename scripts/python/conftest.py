#!/usr/bin/env python
# Copyright 2021 Amlogic.com, Inc. or its affiliates. All rights reserved.
#
# AMLOGIC PROPRIETARY/CONFIDENTIAL
#
# You may not use this file except in compliance with the terms and conditions
# set forth in the accompanying LICENSE.TXT file.
#
# THESE MATERIALS ARE PROVIDED ON AN "AS IS" BASIS. AMLOGIC SPECIFICALLY
# DISCLAIMS, WITH RESPECT TO THESE MATERIALS, ALL WARRANTIES, EXPRESS,
# IMPLIED, OR STATUTORY, INCLUDING THE IMPLIED WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT.
#
import os
import threading
import traceback

import pytest
import datetime
import logging
import threadpool
import shutil
from collections import OrderedDict

from .protocol.aats import *
from .baseConfigParser import get_config_json_data, get_config_data, set_config_data
from .util.errors import Errors
from .util.log_cleaner import LogCleaner
from .util.logger import LTPLogger
from lib.common.playback.MultiMediaPlayer import MultiPlayer
from tools.yamlTool import yamlTool

pytest_plugins = "util.aats_reporter_plugin"
RESULT_DIRECTORY = "results"
LOG_DIRECTORY = "logs"
RETRY_TEST_COUNT = 3


def pytest_sessionstart(session):
    """ Reads the current test config from config.json and this data can be used
    across all the test functions
    """

    logging.info("STARTING AATS TESTER SESSION !!")
    # Setup results output directory
    set_results_dir()
    pytest.result = LTPLogger("aats_tester")

    # Init common errors
    pytest.errors = Errors()

    # Init Log cleaner
    pytest.logcleaner = LogCleaner()

    logging.info("INITIALIZING SESSION: Reading test config from config.json")
    pytest.config = get_config_json_data("devices")
    device_conf = pytest.config
    pytest.test_env_data = yamlTool(os.getcwd() + '/config/config.yaml')
    remote_conf = pytest.test_env_data.get_note('broadlink')
    drm_conf = pytest.test_env_data.get_note('drm')

    # for kpi
    pytest.kpi_config = pytest.test_env_data.get_note('kpi_config')
    if pytest.kpi_config["kpi_debug"]["flag"] == "enable":
        pytest.kpi_enable = True
    else:
        pytest.kpi_enable = False
    pytest.device = None

    try:
        logging.info("INITIALIZING SESSION: Getting the device object")
        pytest.device = get_device_object(device_conf)
        # 只有手选的设备与config 不同时在进行 写入
        if pytest.device._adb_id != device_conf['device_id']:
            # 在config中修改 device_id信息
            logging.info('device name not the same , overwrite')
            temp_data, prj = get_config_data()
            temp_data['devices'][prj]['device_id'] = pytest.device._adb_id
            set_config_data(temp_data)
        pytest.config = get_config_json_data("devices")
        logging.info("INITIALIZING SESSION: Setting the device library objects")
        pytest.multimediaplayer = MultiPlayer(pytest.device)

        init_status_check()
    except Exception as ex:
        logging.exception(str(ex))


def init_status_check():
    # 测试用例进行时 实时获取 cpu 内存等情况
    from lib.common.tools.DutCheckMointor import DutCheckMointor
    pytest.dut_check = DutCheckMointor()


@pytest.fixture(scope="session")
def device():
    """This fixture returns the device object from AATS.
    This abstracts the mode of communication to the device whether it is
    ADB or serial communication.
    """
    if not hasattr(pytest, "device"):
        device_conf = get_config_json_data("devices")
        pytest.device = get_device_object(device_conf)
        pytest.device.json_loc = os.path.abspath('protocol')
        logging.debug("Device handle initialized")

    return pytest.device


def set_results_dir():
    """Creates a directory under results folder for every session based on
    the session start time
    """
    if not hasattr(pytest, "result_dir"):
        session_start_time = datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S")
        result_path = os.getenv("AATS_TESTER_SESSION_RESULT_PATH",
                                os.path.join(RESULT_DIRECTORY, session_start_time))
        result_dir = os.path.join(result_path, LOG_DIRECTORY)
        pytest.result_dir = result_dir
    if not os.path.exists(pytest.result_dir):
        try:
            os.makedirs(pytest.result_dir)
        except OSError:
            logging.exception("Unable to create result folder")


def _collect_logs(testname=""):
    if not hasattr(pytest, "device"):
        device()
    if not hasattr(pytest, "result_dir"):
        set_results_dir()
    if not testname:
        testname = pytest.result.get_name()
    logging.debug("Initiating device log collection")

    log_file_path = os.path.join(pytest.result_dir,
                                 testname + ".console.txt")
    syslog_file_path = os.path.join(pytest.result_dir,
                                    testname + ".syslog.txt")
    cmd_file_path = os.path.join(pytest.result_dir,
                                 testname + ".cmd.txt")
    kpi_file_path = os.path.join(pytest.result_dir,
                                 testname + ".kpi.txt")
    # logcat_file_path = os.path.join(pytest.result_dir,
    # testname + ".logcat.txt")
    if pytest.device._output_f_obj is None or \
            pytest.device._output_f_obj.name != log_file_path:
        pytest.device._output_f_obj = open(log_file_path, "a")
    # if not pytest.device.get_platform() == pytest.device.DEVICE_TARGET_RTOS and \
    if pytest.device._log_file_obj is None or pytest.device._log_file_obj.name != syslog_file_path:
        pytest.device._log_file_obj = open(syslog_file_path, "a")
    if pytest.device._cmd_file_obj is None or \
            pytest.device._cmd_file_obj.name != cmd_file_path:
        pytest.device._cmd_file_obj = open(cmd_file_path, "a")
    if pytest.device._kpi_file_obj is None or \
            pytest.device._kpi_file_obj.name != kpi_file_path:
        if pytest.kpi_enable:
            pytest.device._kpi_file_obj = open(kpi_file_path, "a")

    # if pytest.device._logcat_file_obj is None or \
    # pytest.device._logcat_file_obj.name != logcat_file_path:
    # pytest.device._logcat_file_obj = open(logcat_file_path, "a")
    pytest.device.start_log_collect()


@pytest.fixture(scope="function", autouse=True)
def collect_device_logs(device, request):
    """Initiates device log writing into a new test file"""
    pytest.device.wait_for_bootcomplete()
    _collect_logs()

    # stop log collection at teardown
    def teardown():
        logging.debug("collect_device_logs teardown")
        device.stop_log_collect()

    request.addfinalizer(teardown)


@pytest.mark.trylast
def pytest_generate_tests(metafunc):
    # Bypasses hook during test collection
    # if metafunc.config.option.collection:
    #    return
    pass


def generate_statuc_check():
    pytest.dut_check.cpu.generateCPUChart()
    pytest.dut_check.meminfo.generate_mem_average()


def pytest_sessionfinish(session):
    """Handling session finish"""
    if hasattr(pytest, "device") and pytest.device:
        pytest.device.close()
    if hasattr(pytest, "dut_check") and pytest.device:
        pytest.dut_check.stop_catch_logcat()

    try:
        if hasattr(pytest, "result_dir"):
            logging_plugin = session.config.pluginmanager.get_plugin("logging-plugin")
            log_file_handler = logging_plugin.log_file_handler
            log_file = log_file_handler.baseFilename
            if log_file and os.path.exists(log_file):
                shutil.copyfile(log_file, os.path.join(pytest.result_dir, os.path.basename(log_file)))
                os.remove(log_file)
            pytest.logcleaner.obfuscate_logs(pytest.result_dir)
    except Exception as e:
        logging.exception("Unable to copy pytest log to result_dir: {}".format(e))
    for i in threading.enumerate()[1:]:
        logging.debug(i.__dict__)
    # generate_statuc_check()
