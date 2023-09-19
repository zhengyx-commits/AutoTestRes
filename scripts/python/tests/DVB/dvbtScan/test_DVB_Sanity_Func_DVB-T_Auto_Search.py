#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/2/22
# @Author  : kejun.chen
# @File    : test_DVB_Sanity_Func_DVB-T_Auto_Search.py
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
    {"No": "1", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "7", "fft_size": "2k",
     "mode": "64QPSK", "freq": "177.5", "G_I": "1/4", "code_rate": "1/2"},
    {"No": "2", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "7", "fft_size": "2k",
     "mode": "64QPSK", "freq": "177.5", "G_I": "1/32", "code_rate": "2/3"},
    {"No": "3", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "7", "fft_size": "2k",
     "mode": "64QPSK", "freq": "177.5", "G_I": "1/8", "code_rate": "3/4"},
    {"No": "4", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "7", "fft_size": "2k",
     "mode": "64QPSK", "freq": "177.5", "G_I": "1/16", "code_rate": "5/6"},
    {"No": "5", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "7", "fft_size": "2k",
     "mode": "64QPSK", "freq": "177.5", "G_I": "1/4", "code_rate": "7/8"},
    {"No": "6", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "7", "fft_size": "2k",
     "mode": "16QPSK", "freq": "205.5", "G_I": "1/4", "code_rate": "1/2"},
    {"No": "7", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "7", "fft_size": "2k",
     "mode": "16QPSK", "freq": "205.5", "G_I": "1/8", "code_rate": "2/3"},
    {"No": "8", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "7", "fft_size": "2k",
     "mode": "16QPSK", "freq": "205.5", "G_I": "1/16", "code_rate": "3/4"},
    {"No": "9", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "7", "fft_size": "2k",
     "mode": "16QPSK", "freq": "205.5", "G_I": "1/32", "code_rate": "5/6"},
    {"No": "10", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "7", "fft_size": "2k",
     "mode": "16QPSK", "freq": "205.5", "G_I": "1/8", "code_rate": "7/8"},
    {"No": "11", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "7", "fft_size": "2k",
     "mode": "QPSK", "freq": "226.5", "G_I": "1/8", "code_rate": "1/2"},
    {"No": "12", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "7", "fft_size": "2k",
     "mode": "QPSK", "freq": "226.5", "G_I": "1/4", "code_rate": "2/3"},
    {"No": "13", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "7", "fft_size": "2k",
     "mode": "QPSK", "freq": "226.5", "G_I": "1/16", "code_rate": "3/4"},
    {"No": "14", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "7", "fft_size": "2k",
     "mode": "QPSK", "freq": "226.5", "G_I": "1/32", "code_rate": "5/6"},
    {"No": "15", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "7", "fft_size": "2k",
     "mode": "QPSK", "freq": "226.5", "G_I": "1/32", "code_rate": "7/8"},
    {"No": "16", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "7", "fft_size": "8k",
     "mode": "64QPSK", "freq": "177.5", "G_I": "1/4", "code_rate": "1/2"},
    {"No": "17", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "7", "fft_size": "8k",
     "mode": "64QPSK", "freq": "177.5", "G_I": "1/8", "code_rate": "2/3"},
    {"No": "18", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "7", "fft_size": "8k",
     "mode": "64QPSK", "freq": "177.5", "G_I": "1/16", "code_rate": "3/4"},
    {"No": "19", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "7", "fft_size": "8k",
     "mode": "64QPSK", "freq": "177.5", "G_I": "1/32", "code_rate": "5/6"},
    {"No": "20", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "7", "fft_size": "8k",
     "mode": "64QPSK", "freq": "177.5", "G_I": "1/4", "code_rate": "7/8"},
    {"No": "21", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "7", "fft_size": "8k",
     "mode": "16QPSK", "freq": "226.5", "G_I": "1/4", "code_rate": "1/2"},
    {"No": "22", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "7", "fft_size": "8k",
     "mode": "16QPSK", "freq": "226.5", "G_I": "1/8", "code_rate": "2/3"},
    {"No": "23", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "7", "fft_size": "8k",
     "mode": "16QPSK", "freq": "226.5", "G_I": "1/16", "code_rate": "3/4"},
    {"No": "24", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "7", "fft_size": "8k",
     "mode": "16QPSK", "freq": "226.5", "G_I": "1/32", "code_rate": "5/6"},
    {"No": "25", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "7", "fft_size": "8k",
     "mode": "16QPSK", "freq": "226.5", "G_I": "1/8", "code_rate": "7/8"},
    {"No": "26", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "7", "fft_size": "8k",
     "mode": "QPSK", "freq": "205.5", "G_I": "1/4", "code_rate": "1/2"},
    {"No": "27", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "7", "fft_size": "8k",
     "mode": "QPSK", "freq": "205.5", "G_I": "1/8", "code_rate": "2/3"},
    {"No": "28", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "7", "fft_size": "8k",
     "mode": "QPSK", "freq": "205.5", "G_I": "1/16", "code_rate": "3/4"},
    {"No": "29", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "7", "fft_size": "8k",
     "mode": "QPSK", "freq": "205.5", "G_I": "1/32", "code_rate": "5/6"},
    {"No": "30", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "7", "fft_size": "8k",
     "mode": "QPSK", "freq": "205.5", "G_I": "1/32", "code_rate": "7/8"},
    {"No": "31", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "8", "fft_size": "2k",
     "mode": "64QPSK", "freq": "474", "G_I": "1/4", "code_rate": "1/2"},
    {"No": "32", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "8", "fft_size": "2k",
     "mode": "64QPSK", "freq": "474", "G_I": "1/8", "code_rate": "2/3"},
    {"No": "33", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "8", "fft_size": "2k",
     "mode": "64QPSK", "freq": "474", "G_I": "1/16", "code_rate": "3/4"},
    {"No": "34", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "8", "fft_size": "2k",
     "mode": "64QPSK", "freq": "474", "G_I": "1/32", "code_rate": "5/6"},
    {"No": "35", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "8", "fft_size": "2k",
     "mode": "64QPSK", "freq": "474", "G_I": "1/4", "code_rate": "7/8"},
    {"No": "36", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "8", "fft_size": "2k",
     "mode": "16QPSK", "freq": "650", "G_I": "1/4", "code_rate": "1/2"},
    {"No": "37", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "8", "fft_size": "2k",
     "mode": "16QPSK", "freq": "650", "G_I": "1/8", "code_rate": "2/3"},
    {"No": "38", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "8", "fft_size": "2k",
     "mode": "16QPSK", "freq": "650", "G_I": "1/16", "code_rate": "3/4"},
    {"No": "39", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "8", "fft_size": "2k",
     "mode": "16QPSK", "freq": "650", "G_I": "1/32", "code_rate": "5/6"},
    {"No": "40", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "8", "fft_size": "2k",
     "mode": "16QPSK", "freq": "650", "G_I": "1/8", "code_rate": "7/8"},
    {"No": "41", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "8", "fft_size": "2k",
     "mode": "QPSK", "freq": "858", "G_I": "1/4", "code_rate": "1/2"},
    {"No": "42", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "8", "fft_size": "2k",
     "mode": "QPSK", "freq": "858", "G_I": "1/8", "code_rate": "2/3"},
    {"No": "43", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "8", "fft_size": "2k",
     "mode": "QPSK", "freq": "858", "G_I": "1/16", "code_rate": "3/4"},
    {"No": "44", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "8", "fft_size": "2k",
     "mode": "QPSK", "freq": "858", "G_I": "1/32", "code_rate": "5/6"},
    {"No": "45", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "8", "fft_size": "2k",
     "mode": "QPSK", "freq": "858", "G_I": "1/4", "code_rate": "7/8"},
    {"No": "46", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "8", "fft_size": "8k",
     "mode": "64QPSK", "freq": "474", "G_I": "1/4", "code_rate": "1/2"},
    {"No": "47", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "8", "fft_size": "8k",
     "mode": "64QPSK", "freq": "474", "G_I": "1/8", "code_rate": "2/3"},
    {"No": "48", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "8", "fft_size": "8k",
     "mode": "64QPSK", "freq": "474", "G_I": "1/16", "code_rate": "3/4"},
    {"No": "49", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "8", "fft_size": "8k",
     "mode": "64QPSK", "freq": "474", "G_I": "1/32", "code_rate": "5/6"},
    {"No": "50", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "8", "fft_size": "8k",
     "mode": "64QPSK", "freq": "474", "G_I": "1/4", "code_rate": "7/8"},
    {"No": "51", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "8", "fft_size": "8k",
     "mode": "16QPSK", "freq": "650", "G_I": "1/4", "code_rate": "1/2"},
    {"No": "52", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "8", "fft_size": "8k",
     "mode": "16QPSK", "freq": "650", "G_I": "1/8", "code_rate": "2/3"},
    {"No": "53", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "8", "fft_size": "8k",
     "mode": "16QPSK", "freq": "650", "G_I": "1/16", "code_rate": "3/4"},
    {"No": "54", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "8", "fft_size": "8k",
     "mode": "16QPSK", "freq": "650", "G_I": "1/32", "code_rate": "5/6"},
    {"No": "55", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "8", "fft_size": "8k",
     "mode": "16QPSK", "freq": "650", "G_I": "1/4", "code_rate": "7/8"},
    {"No": "56", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "8", "fft_size": "8k",
     "mode": "QPSK", "freq": "858", "G_I": "1/4", "code_rate": "1/2"},
    {"No": "57", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "8", "fft_size": "8k",
     "mode": "QPSK", "freq": "858", "G_I": "1/8", "code_rate": "2/3"},
    {"No": "58", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "8", "fft_size": "8k",
     "mode": "QPSK", "freq": "858", "G_I": "1/16", "code_rate": "3/4"},
    {"No": "59", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "8", "fft_size": "8k",
     "mode": "QPSK", "freq": "858", "G_I": "1/32", "code_rate": "5/6"},
    {"No": "60", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "8", "fft_size": "8k",
     "mode": "QPSK", "freq": "858", "G_I": "1/8", "code_rate": "7/8"}]
    # {"No": "61", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "6", "fft_size": "2k",
    #  "mode": "64QPSK", "freq": "473", "G_I": "1/4", "code_rate": "1/2"},
    # {"No": "62", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "6", "fft_size": "2k",
    #  "mode": "64QPSK", "freq": "473", "G_I": "1/8", "code_rate": "2/3"},
    # {"No": "63", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "6", "fft_size": "2k",
    #  "mode": "64QPSK", "freq": "473", "G_I": "1/16", "code_rate": "3/4"},
    # {"No": "64", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "6", "fft_size": "2k",
    #  "mode": "64QPSK", "freq": "473", "G_I": "1/32", "code_rate": "5/6"},
    # {"No": "65", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "6", "fft_size": "2k",
    #  "mode": "64QPSK", "freq": "473", "G_I": "1/4", "code_rate": "7/8"},
    # {"No": "66", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "6", "fft_size": "2k",
    #  "mode": "16QPSK", "freq": "473", "G_I": "1/4", "code_rate": "1/2"},
    # {"No": "67", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "6", "fft_size": "2k",
    #  "mode": "16QPSK", "freq": "473", "G_I": "1/8", "code_rate": "2/3"},
    # {"No": "68", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "6", "fft_size": "2k",
    #  "mode": "16QPSK", "freq": "473", "G_I": "1/16", "code_rate": "3/4"},
    # {"No": "69", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "6", "fft_size": "2k",
    #  "mode": "16QPSK", "freq": "473", "G_I": "1/32", "code_rate": "5/6"},
    # {"No": "70", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "6", "fft_size": "2k",
    #  "mode": "16QPSK", "freq": "473", "G_I": "1/8", "code_rate": "7/8"},
    # {"No": "71", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "6", "fft_size": "2k",
    #  "mode": "QPSK", "freq": "473", "G_I": "1/4", "code_rate": "1/2"},
    # {"No": "72", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "6", "fft_size": "2k",
    #  "mode": "QPSK", "freq": "473", "G_I": "1/8", "code_rate": "2/3"},
    # {"No": "73", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "6", "fft_size": "2k",
    #  "mode": "QPSK", "freq": "473", "G_I": "1/16", "code_rate": "3/4"},
    # {"No": "74", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "6", "fft_size": "2k",
    #  "mode": "QPSK", "freq": "473", "G_I": "1/32", "code_rate": "5/6"},
    # {"No": "75", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "6", "fft_size": "2k",
    #  "mode": "QPSK", "freq": "473", "G_I": "1/16", "code_rate": "7/8"},
    # {"No": "76", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "6", "fft_size": "8k",
    #  "mode": "64QPSK", "freq": "473", "G_I": "1/4", "code_rate": "1/2"},
    # {"No": "77", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "6", "fft_size": "8k",
    #  "mode": "64QPSK", "freq": "473", "G_I": "1/8", "code_rate": "2/3"},
    # {"No": "78", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "6", "fft_size": "8k",
    #  "mode": "64QPSK", "freq": "473", "G_I": "1/16", "code_rate": "3/4"},
    # {"No": "79", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "6", "fft_size": "8k",
    #  "mode": "64QPSK", "freq": "473", "G_I": "1/32", "code_rate": "5/6"},
    # {"No": "80", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "6", "fft_size": "8k",
    #  "mode": "64QPSK", "freq": "473", "G_I": "1/32", "code_rate": "7/8"},
    # {"No": "81", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "6", "fft_size": "8k",
    #  "mode": "16QPSK", "freq": "473", "G_I": "1/4", "code_rate": "1/2"},
    # {"No": "82", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "6", "fft_size": "8k",
    #  "mode": "16QPSK", "freq": "473", "G_I": "1/8", "code_rate": "2/3"},
    # {"No": "83", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "6", "fft_size": "8k",
    #  "mode": "16QPSK", "freq": "473", "G_I": "1/16", "code_rate": "3/4"},
    # {"No": "84", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "6", "fft_size": "8k",
    #  "mode": "16QPSK", "freq": "473", "G_I": "1/32", "code_rate": "5/6"},
    # {"No": "85", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "6", "fft_size": "8k",
    #  "mode": "16QPSK", "freq": "473", "G_I": "1/32", "code_rate": "7/8"},
    # {"No": "86", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "6", "fft_size": "8k",
    #  "mode": "QPSK", "freq": "473", "G_I": "1/4", "code_rate": "1/2"},
    # {"No": "87", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "6", "fft_size": "8k",
    #  "mode": "QPSK", "freq": "473", "G_I": "1/8", "code_rate": "2/3"},
    # {"No": "88", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "6", "fft_size": "8k",
    #  "mode": "QPSK", "freq": "473", "G_I": "1/16", "code_rate": "3/4"},
    # {"No": "89", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "6", "fft_size": "8k",
    #  "mode": "QPSK", "freq": "473", "G_I": "1/32", "code_rate": "5/6"},
    # {"No": "90", "video_name": "MPEG2_1_Service", "scan_format": "DVB-T", "band_width": "6", "fft_size": "8k",
    #  "mode": "QPSK", "freq": "473", "G_I": "1/16", "code_rate": "7/8"}]
# task_ids = ['Task{}({}, {}, {}, {}, {}, {}, {}, {}'.format(
#     t["No"], t["video_name"], t["scan_format"], t["band_width"], t["fft_size"], t["mode"], t["freq"],
#     t["G_I"].replace('/', '_'), t["code_rate"].replace('/', '_')) for t in scan_param]
# # scan_param_debug = [scan_param[0]]

scan_params = []
for t in scan_param:
    parameter = f'{t["code_rate"]}_{t["band_width"]}MHz_{t["mode"]}_G={t["G_I"]}_{t["fft_size"].upper()}_NATIVE'
    # new_scan_param = f'Task{t["No"]}({t["video_name"]}, {t["scan_format"]}, {t["freq"]}, {parameter}})'
    task_dict = {
        "No": t["No"],
        "video_name": t["video_name"],
        "scan_format": t["scan_format"],
        "freq": t["freq"],
        "parameters": parameter,
    }
    scan_params.append(task_dict)
task_ids = ['Task{}({}, {}, {}, {}'.format(
    t["No"], t["video_name"], t["scan_format"], t["freq"], t["parameters"]) for t in scan_params]


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
    dvb.dvbt_auto_scan()
    assert dvb_check.check_dvbt_auto_scan()
    dvb_check.check_play_status_main_thread()
