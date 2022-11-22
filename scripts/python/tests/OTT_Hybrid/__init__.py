#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/03/26 19:39
# @Author  : A.T.
# @Site    :
# @File    : __init__.py.py
# @Software: PyCharm
import glob
import os

from tools.yamlTool import yamlTool
from lib.common.system.NetworkAuxiliary import getIfconfig
from tools.resManager import ResManager
# from tests.OTT_Hybrid.MULTI import *

iplist = getIfconfig()
# print(iplist)
DEVICE_IP = ""
STREAM_IP = ""

device_ip_sz = '192.168.1.246'
if device_ip_sz in iplist:
    stream_ip = '192.168.1.247:8554'
    DEVICE_IP = device_ip_sz
    STREAM_IP = stream_ip
else:
    device_ip_sh = '192.168.1.100'
    stream_ip = '192.168.1.102:8554'
    DEVICE_IP = device_ip_sh
    STREAM_IP = stream_ip

config_yaml = yamlTool(os.getcwd() + '/config/config_ott_hybrid.yaml')
p_conf_single_stream = config_yaml.get_note("conf_play_single_stream")
resmanager = ResManager()


def get_conf_url(conf_url, sub_url, conf_stream_name=None, sub_name=None, single_stream=None):
    p_conf_url = config_yaml.get_note(conf_url)
    # print(f"p_conf_url: {p_conf_url}")
    url = p_conf_url.get(sub_url)
    # get conf_play_single_stream, if True: play single stream; otherwise, play multi streams from directory
    single_stream = p_conf_single_stream
    print(f"single_stream: {single_stream}")
    final_urllist = []
    stream_name_list = []
    if single_stream:
        url = url.get("file")
        if conf_stream_name and sub_name:
            # stream_name_list = []
            p_conf_stream_name = config_yaml.get_note(conf_stream_name)
            p_conf_sub_name = p_conf_stream_name.get(sub_name)
            if "rtp" in url:
                final_url = url
            elif "rtsp" in sub_url:
                final_url = f"rtsp://{STREAM_IP}" + url
            elif "udp" in url:
                final_url = url
            else:
                final_url = f"http://{DEVICE_IP}" + sub_url
            stream_name_list.append(p_conf_sub_name)
            print(f"stream_name_list:{stream_name_list}, final_url:{final_url}")
            return stream_name_list, final_url
        else:
            final_url = f"http://{DEVICE_IP}" + url
            final_urllist.append(final_url)
            print(final_urllist)
            return final_urllist
    else:
        if conf_stream_name and sub_name:
            p_conf_stream_name = config_yaml.get_note(conf_stream_name)
            print(p_conf_stream_name)
            for k, v in p_conf_stream_name.items():
                stream_name_list.append(v)
            final_url = url.get("file")
            if "rtsp" in conf_url:
                final_url = f"rtsp://{STREAM_IP}" + final_url
            print(stream_name_list, final_url)
            return stream_name_list, final_url
        else:
            if "http" in conf_url:
                dir_url = url.get("dir")
                file_path = resmanager.get_target(f"{dir_url}")
                print(f"file_path: {file_path}")
                files = glob.glob(f"{file_path}/*.ts", recursive=True)
                for file in files:
                    file = f"http://{DEVICE_IP}" + "/" + "/".join(file.split("/")[-4:])
                    final_urllist.append(file)
            elif "hls" in conf_url:
                dir_url = url.get("dir")
                file_path = resmanager.get_target(f"{dir_url}")
                print(f"file_path: {file_path}")
                files = glob.glob(f"{file_path}/*", recursive=True)
                for file in files:
                    files = glob.glob(f"{file}/*.m3u8", recursive=True)
                    for file in files:
                        if ("hlsV3_TS_H265_4K" == sub_url) and ("1.m3u8" in file):
                            pass
                        else:
                            file = f"http://{DEVICE_IP}" + "/" + "/".join(file.split("/")[-5:])
                            final_urllist.append(file)
            else:
                pass
            print(f"final_urllist:{final_urllist}")
            return final_urllist





