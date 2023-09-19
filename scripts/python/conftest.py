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
from .baseConfigParser import get_config_json_data, get_config_data, set_config_data, get_device_config_by_device_id, get_config_json
from .util.errors import Errors
from .util.log_cleaner import LogCleaner
from .util.logger import LTPLogger
from tools.flashkey import Flashkey
# from lib.common.system.BroadLinkRM3 import IRControl, KeyEventMapping
from tools.yamlTool import yamlTool

pytest_plugins = "util.aats_reporter_plugin"
RESULT_DIRECTORY = "results"
LOG_DIRECTORY = "logs"
RETRY_TEST_COUNT = 3
pytest.connect_type = ""
pytest.multi_instance_devices = []
pytest.serialnumber = []


def pytest_sessionstart(session):
    """ Reads the current test config from config.json and this data can be used
    across all the test functions
    """
    multi_instance = session.config.getoption("--multiInstance")
    conn_type = session.config.getoption("--conn_type")
    print("--conn_type", conn_type, type(conn_type))
    if len(multi_instance) != 0:
        pytest.multi_instance = multi_instance
    print("--multiInstance", multi_instance, type(multi_instance))
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
    # choose adb or linux for framework
    if conn_type == "adb":
        pytest.connect_type = "adb"
    elif ("device_id" not in device_conf) or (conn_type == "serial"):
        pytest.connect_type = "serial"
    else:
        pass

    pytest.test_env_data = yamlTool(os.getcwd() + '/config/config.yaml')

    # for kpi
    pytest.kpi_config = pytest.test_env_data.get_note('kpi_config')
    if pytest.kpi_config["kpi_debug"]["flag"] == "enable":
        pytest.kpi_enable = True
    else:
        pytest.kpi_enable = False
    pytest.device = None

    try:
        logging.info("INITIALIZING SESSION: Getting the device object")
        pytest.device = get_device_object(pytest.connect_type, device_conf, multi_instance)
        print("pytest device", pytest.device)
        if len(multi_instance) != 0:
            pytest.config = get_device_config_by_device_id(multi_instance)
            for device in pytest.config:
                pytest.serialnumber.append(device['device_id'])
        else:
            # 只有首选的设备与config 不同时在进行 写入
            if pytest.connect_type.startswith("adb"):
                if pytest.device._adb_id != device_conf['device_id']:
                # 在config中修改 device_id信息
                   logging.info('device name not the same , overwrite')
                   temp_data, prj = get_config_data()
                   temp_data['devices'][prj]['device_id'] = pytest.device._adb_id
                   set_config_data(temp_data)
                pytest.serialnumber = pytest.config['device_id']
            pytest.config = get_config_json_data("devices")
        print("pytest config", pytest.config)
        print("pytest serialnumber", pytest.serialnumber)
        # init_status_check()
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
        if isinstance(pytest.device, list):
            # For multiple instances, get device objects for each specified device ID
            # device_ids = pytest.multi_instance.split(',')
            pytest.device = get_device_object(pytest.connect_type, device_conf, pytest.multi_instance)
        else:
            # For single instance, get a single device object
            pytest.device = get_device_object(pytest.connect_type, device_conf)
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


def _collect_logs(testname="", device_id=None):
    # if not hasattr(pytest, "device"):
    #     device()
    if not hasattr(pytest, "result_dir"):
        set_results_dir()
    if not testname:
        testname_original = pytest.result.get_name()
        testname = testname_original.replace('/', '_') if isinstance(testname_original, str) else testname_original
    logging.info("Initiating device log collection")
    if isinstance(pytest.device, list):
        # Multi-device: handle log file creation for each device
        for i, device_instance_obj in enumerate(pytest.device):
            if device_id is None or device_id == i:
                log_file_path = os.path.join(pytest.result_dir, f"{testname}_device_{device_id}.console.txt")
                syslog_file_path = os.path.join(pytest.result_dir, f"{testname}_device_{device_id}.syslog.txt")
                cmd_file_path = os.path.join(pytest.result_dir, f"{testname}_device_{device_id}.cmd.txt")
                kpi_file_path = os.path.join(pytest.result_dir, f"{testname}_device_{device_id}.kpi.txt")

                pytest.device_instance_obj = device_instance_obj
                if pytest.device_instance_obj._output_f_obj is None or pytest.device_instance_obj._output_f_obj.name != log_file_path:
                    pytest.device_instance_obj._output_f_obj = open(log_file_path, "a")
                if pytest.device_instance_obj._log_file_obj is None or pytest.device_instance_obj._log_file_obj.name != syslog_file_path:
                    pytest.device_instance_obj._log_file_obj = open(syslog_file_path, "a")
                if pytest.device_instance_obj._cmd_file_obj is None or pytest.device_instance_obj._cmd_file_obj.name != cmd_file_path:
                    pytest.device_instance_obj._cmd_file_obj = open(cmd_file_path, "a")
                # if pytest.device_instance_obj._kpi_file_obj is None or pytest.device_instance_obj._kpi_file_obj.name != kpi_file_path:
                    # if pytest.kpi_enable:
                    #     pytest.device._kpi_file_obj = open(kpi_file_path, "a")
                AATSADBTarget(pytest.device_instance_obj._adb_id)
                pytest.device_instance_obj.start_log_collect()
    else:
        # Single device: handle log file creation as before
        log_file_path = os.path.join(pytest.result_dir, f"{testname}.console.txt")
        syslog_file_path = os.path.join(pytest.result_dir, f"{testname}.syslog.txt")
        cmd_file_path = os.path.join(pytest.result_dir, f"{testname}.cmd.txt")
        kpi_file_path = os.path.join(pytest.result_dir, f"{testname}.kpi.txt")

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

        pytest.device.start_log_collect()


@pytest.fixture(scope="function", autouse=True)
def collect_device_logs(device, request):
    """Initiates device log writing into a new test file"""
    # Multi-device: loop through all devices
    if isinstance(pytest.device, list):
        for device_id, device_instance_obj in enumerate(pytest.device):
            # pytest.device = device_instance
            device_instance_obj.wait_for_bootcomplete()
            _collect_logs(device_id=device_id)

            def teardown():
                logging.debug("collect_device_logs teardown")
                device_instance_obj.stop_log_collect()

            request.addfinalizer(teardown)
    else:
        # Single device: continue with the original logic
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


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_makereport(item, call):
    if hasattr(item, 'execution_count'):
        pytest.reruns_count = item.execution_count


def pytest_sessionfinish(session):
    """Handling session finish"""
    if isinstance(pytest.device, list):
        for device_instance_obj in pytest.device:
            device_instance_obj.close()
    else:
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


def pytest_addoption(parser):
    parser.addoption("--piplineType", action="store", default="iptv", help="Specify the pipeline type")
    parser.addoption("--project", action="store", default="ref", help="Specify project test cases")
    parser.addoption("--multiInstance", action="append", default=[], help="multi instance")
    parser.addoption("--conn_type", action="store", default="adb", help="Specify connected DUT type")


