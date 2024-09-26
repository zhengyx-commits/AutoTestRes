# !/usr/bin python3
# -*- coding: utf-8 -*-
# @author     : chao.li
# @software   : PyCharm
# @file       : test_OTT-Sanity_Func_023_HDCP.py
# @Time       : 2021/7/7 上午9:06
import logging
import pytest

from lib.common.checkpoint.HdmiCheck import HdmiCheck

hdmiCheck = HdmiCheck()
hdcp_file_path = '/home/amlogic/hdcp/'


@pytest.mark.skip
def test_Sanity_Func_023_HDCP():
    # assert hdmiCheck.get_tx_hdcp_mode() == '22', 'HDCP mode not match 2.2'
    if not hdmiCheck.check_tx_22():
        hdmiCheck.write_to_tx_22_key(hdcp_file_path)
    assert hdmiCheck.get_tx_hdcp_mode() == '22', 'HDCP mode not match 2.2'

