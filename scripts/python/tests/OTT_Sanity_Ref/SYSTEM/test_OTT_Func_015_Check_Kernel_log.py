# !/usr/bin python3
# -*- coding: utf-8 -*-
# @author     : chao.li
# @software   : PyCharm
# @file       : test_OTT-Sanity_Func_023_HDCP.py
# @Time       : 2021/7/7 上午9:06
import logging
import pytest


def test_Sanity_Func_015_Check_Kernel_Log():
    log_contain_disagrees = False
    with open(pytest.result_dir + "/dmesg.log.txt", mode='r', encoding='utf-8') as file:
        for line in file:
            if "disagrees" in line.lower():
                logging.info(f"checked disagrees log: {line}")
                log_contain_disagrees = True
    assert not log_contain_disagrees

