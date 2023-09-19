#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/5/16 下午3:44
# @Author  : yongbo.shao
# @File    : test_ott_s_s905y4_boot_up.py
# @Email   : yongbo.shao@amlogic.com
# @Ide: PyCharm
from tools.KpiAnalyze import KpiAnalyze
from tools.yamlTool import yamlTool
from lib.common.system.ADB import ADB
from lib.common.system.SerialPort import SerialPort
from tests.OTT_Hybrid.KPI import *
import os
import time
import pytest
import random

logdir = pytest.result_dir
config_yaml = yamlTool(os.getcwd() + '/config/config.yaml')
p_conf_boot_up = config_yaml.get_note("kpi_config").get("vod_s_t_kpi").get("boot_up")

for g_conf_device_id in get_device():
    adb_cmd = ["/usr/bin/adb", "-s", g_conf_device_id, "shell", "logcat -s ActivityManager"]
    kpianalyze = KpiAnalyze(for_framework=True, adb=g_conf_device_id, config="/config/config.yaml",
                                    kpi_name="vod_s_boot_up_kpi",
                                    targetfile=None, kpifileobj=f"s_boot_up_{g_conf_device_id}.txt",
                                    kpifileobj_xlsx=f"s_boot_up_{g_conf_device_id}.xlsx", case="boot")
    logcat_file = f'logcat_{kpianalyze.kpifile.name.split(".")[0]}_{g_conf_device_id}.log'
    repeat_count = kpianalyze.repeat_count


ser = SerialPort()
adb = ADB()
os.system("rm boottotal.log")
os.system("rm boot_*.log")


@pytest.mark.repeat(repeat_count)
# @pytest.mark.repeat(3)
def test_boot_up_kpi_result():
    ser.write("logcat -c")
    ser.enter_uboot()
    ser.enter_kernel()
    uboot_time = int(ser.uboot_time)/1000
    kpianalyze.uboot_time.append(str(uboot_time))
    ser.write("su")
    ser.write(f"logcat -b all > /data/{logcat_file} &")
    data = ser.write_pipe("logcat |grep -i 'for service {com.google.android.apps.tv.launcherx/com.google.android.apps.tv.launcherx.coreservices.notificationlistener.TvNotificationListenerService}' ")
    if data:
        time.sleep(30)
        ser.write("fg")
        ser.write("\x03")
        ser.write("\x03")
        ser.write("\x03")
        adb.root()
        adb.pull(f"/data/{logcat_file}", f"{os.getcwd()}/boot_{random.randint(0, 100)}.log")


def test_analysis():
    os.system("chmod 777 boot_*.log")
    os.system(f"cat boot_*.log > boottotal.log")
    kpianalyze.kpi_analysis()
    kpianalyze.kpi_calculate()
    kpianalyze.save_to_excel()
    kpianalyze.save_to_db(name='vod_s_boot_up_kpi', flag='1')
    save_result(kpianalyze.kpifileobj_xlsx)
    kpianalyze.filter_abnormal_value(p_conf_boot_up)
