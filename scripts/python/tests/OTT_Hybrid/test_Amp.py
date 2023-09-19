import pytest
import logging
import json
import os
import pandas as pd
from lib.common.system.ADB import ADB
from tools.resManager import ResManager
from . import *

p_conf_localplay = config_yaml.get_note('conf_localplay')
p_conf_uuid = p_conf_localplay['uuid']
p_conf_video_path = p_conf_localplay['video_path']
p_conf_saved_path = p_conf_localplay['saved_path']

adb = ADB()
resmanager = ResManager()
test_dir = {}
test_list = []


def test_amp():
    res = True
    amlMpUnitTest = resmanager.get_target("amlMpUnitTest")
    adb.push(amlMpUnitTest, "/data")
    logging.info(f"./data/amlMpUnitTest /storage/{p_conf_uuid}/{p_conf_video_path}")
    adb.run_shell_cmd("chmod 777 /data/amlMpUnitTest")
    adb.run_shell_cmd(f"./data/amlMpUnitTest --url /storage/{p_conf_uuid}/{p_conf_video_path} --gtest_output=json:{p_conf_saved_path}")
    adb.pull(p_conf_saved_path, adb.logdir)

    with open(adb.logdir + "/" + "amlMpUnitTest.json") as f:
        content = json.load(f)
        test_number = content["tests"]
        failures = content["failures"]
        test_dir["test_number"] = test_number
        test_dir["failures"] = failures
        testsuites = content["testsuites"]
        for testsuite in testsuites:
            testcases = testsuite["testsuite"]
            for testcase in testcases:
                testcase_name = testcase["name"]
                if "failures" in testcase:
                    testcase_failures = testcase["failures"]
                    testcase_name = testcase["name"]
                    test_dir[testcase_name] = testcase_failures
                    res = False
                else:
                    test_dir[testcase_name] = "pass"
    df = pd.DataFrame(list(test_dir.items()))
    df.to_excel(adb.logdir + "_" + "amlMpUnitTest.xlsx")
    assert res
