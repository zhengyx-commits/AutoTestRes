#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/03/26 19:39
# @Author  : A.T.
# @Site    :
# @File    : __init__.py.py
# @Software: PyCharm
import glob
import os
import re
from tools.yamlTool import yamlTool
from lib.common.system.NetworkAuxiliary import differentiate_servers
from tools.resManager import ResManager
import random

DEVICE_IP, STREAM_IP, RTSP_PATH = differentiate_servers()

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
            if "udp" in conf_url:
                # download udp streams
                resmanager.get_target(path=sub_name, source_path="rtp_udp_videos/" + sub_name)
                final_url = url[0:-3] + str(random.randint(0, 9)) + str(random.randint(0, 9)) + str(random.randint(0, 9))
            elif "rtp" in conf_url:
                final_url = url[0:-3] + str(random.randint(0, 9)) + str(random.randint(0, 9)) + str(random.randint(0, 9))
                # download rtp streams
                resmanager.get_target(path=sub_name, source_path="rtp_udp_videos/" + sub_name)
            elif "rtsp" in sub_url:
                final_url = f"rtsp://{STREAM_IP}" + url
                # download rtsp single stream
                resmanager.get_target(path=url[1:],
                                      source_path="live555_videos/" + re.sub(r'^/[^/]+/', '', url))
            else:
                final_url = f"http://{DEVICE_IP}" + sub_url
            stream_name_list.append(p_conf_sub_name)
            print(f"stream_name_list:{stream_name_list}, final_url:{final_url}")
            return stream_name_list, final_url
        else:
            final_url = f"http://{DEVICE_IP}" + url
            # download hls single streams
            if "HLS" in url:
                url = url.rsplit("/", 1)[0]
                resmanager.get_target(path=re.sub(r'^/[^/]+/', '', url) + "/",
                                    source_path="http_hls_videos/" + re.sub(r'^/[^/]+/', '', url))
            # download http single stream
            else:
                resmanager.get_target(path=re.sub(r'^/[^/]+/', '', url),
                                  source_path="http_hls_videos/" + re.search(r'[^/]+/[^/]+$', url).group(0))
            final_urllist.append(final_url)
            print(final_urllist)
            return final_urllist
    else:
        if conf_stream_name and sub_name:
            p_conf_stream_name = config_yaml.get_note(conf_stream_name)
            print(p_conf_stream_name)
            for k, v in p_conf_stream_name.items():
                stream_name_list.append(v)
            url = url.get("file")
            if "udp" in conf_url:
                # download udp videos
                resmanager.get_target(path=sub_name, source_path="rtp_udp_videos/" + sub_name)
                url = url[0:-3] + str(random.randint(0, 9)) + str(random.randint(0, 9)) + str(random.randint(0, 9))
            elif "rtp" in conf_url:
                # download rtp videos
                resmanager.get_target(path=sub_name, source_path="rtp_udp_videos/" + sub_name)
                url = url[0:-3] + str(random.randint(0, 9)) + str(random.randint(0, 9)) + str(random.randint(0, 9))
                print(stream_name_list, url)
            return stream_name_list, url
        else:
            # download rtsp videos
            if "rtsp" in conf_url:
                dir_url = url.get("dir")
                file_path = resmanager.get_target(path=dir_url, source_path="live555_videos/" + dir_url.split("/")[1])
                print(f"file_path: {file_path}")
                files = glob.glob(f"{file_path}/*.ts", recursive=True)
                for file in files:
                    file = f"rtsp://{STREAM_IP}" + "/" + "/".join(file.split("/")[-3:])
                    final_urllist.append(file)
            # download http videos
            if "http" in conf_url:
                dir_url = url.get("dir")
                file_path = resmanager.get_target(path=dir_url, source_path="http_hls_videos/" + dir_url.split("/")[1])
                print(f"file_path: {file_path}")
                files = glob.glob(f"/var/www/res/{dir_url}/*.ts", recursive=True)
                for file in files:
                    file = f"http://{DEVICE_IP}" + "/" + "/".join(file.split("/")[-4:])
                    final_urllist.append(file)
            # download hls videos
            elif "hls" in conf_url:
                dir_url = url.get("dir")
                file_path = resmanager.get_target(path=dir_url, source_path="http_hls_videos/" + dir_url.split("/")[1])
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
