#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/7/5 上午10:53
# @Author  : yongbo.shao
# @File    : __init__.py.py
# @Email   : yongbo.shao@amlogic.com
# @Ide: PyCharm

import logging
import pytest

from xml.etree import ElementTree as ET
from lib.common.system.Permission import Permission
from lib.common.system.ADB import ADB
from lib import get_device
from tools.StreamProvider import StreamProvider
from shutil import copyfile
from tests.OTT_Hybrid import *
from tools.resManager import ResManager
from datetime import datetime
from tests import *
import shutil


permission = Permission()
adb = ADB()
streamProvider = StreamProvider()
streamProvider1 = StreamProvider()
MULTI_APK = "MultiMediaPlayer_2022.08.12_2b45916.apk"
XML_PATH = "apk/MultiMediaPlayer.xml"
MULTIMEDIAPLAYER_TEST_APP_NAME = "com.android.multimediaplayer"
DUT_MULTIMEDIAPLAYER_PATH = "/data/data/com.android.multimediaplayer"
resmanager = ResManager()
devices = get_device()
repeat_count = int()


def check_install_apk():
    adb.install_apk("apk/" + MULTI_APK)
    adb.run_shell_cmd("adb logcat -b all -c")
    adb.run_shell_cmd("setenforce 0")
    adb.run_shell_cmd("adb logcat -G 40M")


def stop_multi_apk():
    adb.app_stop(MULTIMEDIAPLAYER_TEST_APP_NAME)


def setprop():
    adb.run_shell_cmd("setenforce 0")
    adb.run_shell_cmd("echo 0x10000000 > /sys/module/aml_media/parameters/di_dbg")
    adb.run_shell_cmd("echo 0x42 > /sys/class/video_composer/print_flag")
    adb.run_shell_cmd("echo 1 > /sys/module/aml_media/parameters/debug_flag")
    adb.run_shell_cmd("echo 0x40 > /sys/module/amvdec_mh264/parameters/h264_debug_flag;echo 0x810 > /sys/module/amvdec_mmpeg12/parameters/debug_enable")


def set_url(url):
    resmanager.get_target("apk/MultiMediaPlayer.xml")
    tree = ET.parse(os.getcwd() + "/res/apk/MultiMediaPlayer.xml")
    root = tree.getroot()
    root.find("player_list").find("player_info").find("channel_list").find("channel_data").find("url").text = url
    print(root.find("player_list").find("player_info").find("channel_list").find("channel_data").find("url").text)
    tree = ET.ElementTree(root)
    tree.write(f"{os.getcwd() + '/res/apk/MultiMediaPlayer.xml'}", encoding="utf-8")


# def get_filepath(video_name):
#     if not streamProvider.get_file_path('ts', video_name):
#         logging.error("stream provider file path doesn't exist.")
#         return
#     else:
#         file_path = streamProvider.get_file_path('ts', 'H264_Butterfly_4k')[0]
#     try:
#         streamProvider.start_send('udp', file_path, iswait=True)
#     except Exception as e:
#         logging.error("stream provider start send failed.")
#         raise False


def push_xml():
    adb.push(f"{os.getcwd()}/res/apk/MultiMediaPlayer.xml",
             DUT_MULTIMEDIAPLAYER_PATH)
    adb.run_shell_cmd(f"killall {MULTIMEDIAPLAYER_TEST_APP_NAME}")


def prepare(conf_url, protocol, conf_stream_name, stream, **kwargs):
    stream_name_list, url = get_conf_url(conf_url, protocol, conf_stream_name, stream)
    print("url", url)
    set_url(f"{url}")
    file_path = streamProvider.get_file_path(stream, 'ts', stream_name_list[0])
    print("file_path", file_path)
    try:
        if "udp" in protocol:
            streamProvider.start_send(protocol, file_path[0], url=url[6:])
        elif "rtp" in protocol:
            streamProvider.start_send(protocol, file_path[0], url=url[-4:])
        elif "rtsp" in protocol:  # rtsp
            streamProvider.start_send("rtsp", file_path[0])
        else:
            pass
    except Exception as e:
        logging.error(f"stream provider start send failed {e}")
        raise False
    return url


def stop_send():
    streamProvider.stop_send()


def save_result(xlsx_name):
    g_conf_device_id = pytest.config['device_id']
    if '.xlsx' in xlsx_name:
        target_name = xlsx_name.split('.xlsx')[0]
    else:
        target_name = xlsx_name
    if "ott_hybrid_t" in pytest.target.get("prj"):
        dirpath = "/var/www/res/android_t_kpi_result"
    else:
        dirpath = "/var/www/res/android_s_kpi_result"
    if not os.path.exists(dirpath):
        os.mkdir(dirpath)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_path = f'{timestamp}_{g_conf_device_id}'
    logging.info(new_path)
    directory = os.path.join(dirpath, new_path)
    os.makedirs(directory)
    file_list = glob.glob(f'{target_name}.*')
    for file_path in file_list:
        # shutil.move(file_path, directory)
        copyfile(file_path, f"{directory}/{file_path}")


def get_config():
    config_yaml = yamlTool(os.getcwd() + '/config/config.yaml')
    return config_yaml


