#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/6/9
# @Author  : KeJun.Chen
# @File    : test_DVB_Sanity_Func_KPI_Scan.py
# @Email   : kejun.chen@amlogic.com
# @Ide: PyCharm

from tools.KpiAnalyze import *
from tools.DVBStreamProvider import DVBStreamProvider
from lib.common.tools.DVB import DVB
from lib.common.checkpoint.DvbCheck import DvbCheck
from tools.yamlTool import yamlTool
from tests.DVB.KPI import *

adb = ADB()
dvb = DVB()
dvb_stream = DVBStreamProvider()
dvb_check = DvbCheck()

config_yaml = yamlTool(os.getcwd() + '/config/config_dvb_kpi.yaml').get_note("kpi_config")
preset_expected_value = config_yaml.get('kpi_results_detect')['dvb_scan_kpi_excepted_results']
preset_manual_value = config_yaml.get('kpi_results_detect')['dvb_scan_kpi_manual_results']

for g_conf_device_id in get_device():
    DVBKPI = KpiAnalyze(for_framework=True, adb=g_conf_device_id,
                        config="/config/config_dvb_kpi.yaml",
                        kpi_name="dvb_scan_kpi",
                        targetfile=None, kpifileobj=f"dvb_scan_{g_conf_device_id}.txt",
                        kpifileobj_xlsx=f"dvb_scan_{g_conf_device_id}.xlsx")
    repeat_count = DVBKPI.repeat_count


@pytest.fixture(scope='module', autouse=True)
def multi_teardown():
    dvb_stream.start_dvbc_stream('23_Serbia_DVBC_Discovery_short_Event_Descriptor')
    adb.run_shell_cmd("dmesg -c")
    adb.run_shell_cmd("logcat -b all -c")
    time.sleep(3)
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


@pytest.mark.repeat(repeat_count)
def test_scan():
    logging.info('start scan.')
    dvb.start_livetv_apk_and_manual_scan()
    time.sleep(10)


def test_kpi_result():
    DVBKPI.kpi_analysis()
    DVBKPI.kpi_calculate()
    DVBKPI.save_to_excel()
    DVBKPI.save_to_db(name='dvb_scan_kpi', flag='1')
    DVBKPI.results_detect(f'dvb_scan_{g_conf_device_id}.xlsx', preset_expected_value, preset_manual_value)
    save_result(DVBKPI.kpifileobj_xlsx)
