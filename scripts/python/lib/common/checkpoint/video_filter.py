#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/7/11 下午4:20
# @Author  : yongbo.shao
# @File    : video_filter.py
# @Email   : yongbo.shao@amlogic.com
# @Ide: PyCharm
import re
import os
import subprocess


def get_freeze_whitelist(file_path):
    """
    using ffmpeg freezedetect api
    Returns:
    """
    with open("freeze_whitelist.txt", "a+") as f:
        content = f.read()
        # print("content", content)
        # 正则表达式匹配
        pattern = r"/([^/]+)\.ts$"
        matches = re.findall(pattern, content, flags=re.IGNORECASE)
        if matches[0] in content:
            return
        else:
            video_list = []
            # 使用FFmpeg的freezedetect滤镜
            command = ["ffmpeg", "-i", file_path, "-vf", "freezedetect=n=0.05:d=3", "-f", "null",
                       "-"]  # 噪声值越小，越宽松，越容易漏报
            output = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            # 分析输出
            lines = output.stderr.split("\n")
            # print(lines)
            for line in lines:
                if "freeze" in line:
                    video_list.append(line)
                    # print(line)
            f.write(file_path + ":" + str(video_list) + "\n")


def save_file(file_path):
    with open("saved_video.txt", "w") as f:
        pattern = r"/([^/]+)\.ts$"
        matches = re.findall(pattern, file_path, flags=re.IGNORECASE)
        if matches:
            f.write(matches[0])


def read_file():
    with open("saved_video.txt", "r") as f:
        content = f.read()
    return content


def check_freeze(file_path):
    print(os.getcwd())
    video_dict = {}
    video_list = []
    # 使用FFmpeg的freezedetect滤镜
    command = ["ffmpeg", "-i", file_path, "-vf", "freezedetect=n=0.05:d=3", "-f", "null",
               "-"]  # 噪声值越小，越宽松，越容易漏报
    output = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # 分析输出
    lines = output.stderr.split("\n")
    # print(lines)
    for line in lines:
        with open(os.getcwd() + "/lib/common/checkpoint/freeze_whitelist.txt", "r+") as f:
            content = f.readlines()
        for ele in content:
            if ("freeze_start" in line) and (line not in ele):
                video_list.append(line)
            if (("freeze_duration" in line)) and (line not in ele):
                video_list.append(line)
            if (("freeze_end" in line)) and (line not in ele):
                video_list.append(line)
        if ("freeze_duration" and "freeze_start" and "freeze_end") in video_list:
            print(video_list)
            video_dict[file_path] = video_list
            f.write(str(video_dict))
    #     print(f"checked {file_path} freeze", video_list)
    #     return False