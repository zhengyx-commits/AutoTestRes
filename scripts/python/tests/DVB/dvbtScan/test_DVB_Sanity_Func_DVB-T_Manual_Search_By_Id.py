#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/2/23
# @Author  : kejun.chen
# @File    : test_DVB_Sanity_Func_DVB-T_Manual_Search_By_Id.py
# @Email   : kejun.chen@amlogic.com
# @Ide: PyCharm
import pytest
from tools.DVBStreamProvider import DVBStreamProvider
# from tools.DVBStreamProvider_Linux import DVBStreamProvider
from lib.common.tools.DVB import DVB
from lib.common.checkpoint.DvbCheck import DvbCheck


dvb = DVB()
dvb_stream = DVBStreamProvider()
dvb_check = DvbCheck()


scan_param = [
    {"No": "1", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "8", "fft_size": "2k",
     "mode": "64QPSK", "freq": "474", "G_I": "1/4", "code_rate": "1/2", "index": "11"},
    {"No": "2", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "7", "fft_size": "8k",
     "mode": "64QPSK", "freq": "177.5", "G_I": "1/16", "code_rate": "7/8", "index": "3"}]
# task_ids = ['Task{}({}, {}, {}, {}, {}, {}, {}, {}'.format(
#     t["No"], t["video_name"], t["scan_format"], t["band_width"], t["fft_size"], t["mode"], t["freq"],
#     t["G_I"].replace('/', '_'), t["code_rate"].replace('/', '_')) for t in scan_param]
# # scan_param_debug = [scan_param[0]]

scan_params = []
for t in scan_param:
    parameter = f'{t["code_rate"]}_{t["band_width"]}MHz_{t["mode"]}_G={t["G_I"]}_{t["fft_size"].upper()}_NATIVE'
    # new_scan_param = f'Task{t["No"]}({t["video_name"]}, {t["scan_format"]}, {t["freq"]}, {parameter}, {t["index"]})'
    task_dict = {
        "No": t["No"],
        "video_name": t["video_name"],
        "scan_format": t["scan_format"],
        "freq": t["freq"],
        "parameters": parameter,
        "index": t["index"]
    }
    scan_params.append(task_dict)
task_ids = ['Task{}({}, {}, {}, {}, {}'.format(
    t["No"], t["video_name"], t["scan_format"], t["freq"], t["parameters"], t["index"]) for t in scan_params]


@pytest.fixture(scope='function', autouse=True)
def dvb_setup_teardown():
    yield
    dvb.stop_livetv_apk()
    dvb_stream.stop_dvb()


@pytest.mark.parametrize('param', scan_params, ids=task_ids)
def test_dvb_scan(param):
    # dvb_stream.start_dvbt_stream(video_name=param["video_name"], scan_format=param["scan_format"],
    #                              band_width=param["band_width"], fft_size=param["fft_size"], mode=param["mode"],
    #                              freq=param["freq"], G_I=param["G_I"], code_rate=param["code_rate"])
    dvb_stream.start_dvbt_stream(video_name=param["video_name"], scan_format=param["scan_format"],
                                 freq=param["freq"], parameter=param["parameters"])
    dvb.start_livetv_apk()
    dvb.set_channel_mode_dvbt()
    dvb.dvbt_manual_scan_by_id(index=param["index"])
    assert dvb_check.check_dvbt_manual_scan_by_id()
    dvb_check.check_play_status_main_thread()
