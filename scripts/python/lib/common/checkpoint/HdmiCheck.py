#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/4/13 16:37
# @Author  : chao.li
# @Site    :
# @File    : HdmiCheck.py
# @Software: PyCharm

import logging
import threading
import time

from lib.common.system.ADB import ADB
from lib.common.system.HdmiOut import HdmiOut

from . import Check


class HdmiCheck(ADB, Check):
    '''
    Singleton class,should not be inherited

    Attributes:
        HDMI_DEBUG_COMMAND : hdmi rx debug command
        HDCP_TX_KEY_CHECK_COMMAND : tx hdcp store command
        HDCP_TX_MODE_CHECK_COMMAND : tx mode command
        HDMI_TX_AUTHENTICATED_COMMAND : tx authenticated status command
        HDMI_RX_KEY_CHECK_COMMAND : rx key command
        HDMI_RX_AUTHENTICATED_COMMAND : rx authenticated status command
        HDMI_RX_MODE_CHECK_COMMAND : rx mode command
    '''

    _INSTANCE_LOCK = threading.Lock()

    HDMI_DEBUG_COMMAND = 'echo state > /sys/class/hdmirx/hdmirx0/debug'

    HDCP_TX_KEY_CHECK_COMMAND = 'cat /sys/class/amhdmitx/amhdmitx0/hdcp_lstore'
    HDCP_TX_MODE_CHECK_COMMAND = 'cat /sys/class/amhdmitx/amhdmitx0/hdcp_mode'
    HDMI_TX_AUTHENTICATED_COMMAND = 'cat /sys/module/hdmitx20/parameters/hdmi_authenticated'

    HDMI_RX_KEY_CHECK_COMMAND = 'cat /sys/module/tvin_hdmirx/parameters/hdcp22_on'
    HDMI_RX_AUTHENTICATED_COMMAND = 'echo state2 > /sys/class/hdmirx/hdmirx0/debug'
    HDMI_RX_MODE_CHECK_COMMAND = 'cat /sys/class/amhdmitx/amhdmitx0/hdcp_ver'

    def __init__(self):
        ADB.__init__(self, 'Player', unlock_code="", stayFocus=True)
        Check.__init__(self)

        self.hdmiout = HdmiOut()

    def __new__(cls, *args, **kwargs):
        if not hasattr(HdmiCheck, "_instance"):
            with HdmiCheck._INSTANCE_LOCK:
                if not hasattr(HdmiCheck, "_insatnce"):
                    HdmiCheck._instance = object.__new__(cls)
        return HdmiCheck._instance

    def get_hdmi_debug(self):
        '''
        get hdmi status
        command : echo state > /sys/class/hdmirx/hdmirx0/debug
        @return: hdmi hactive and vactive : dict
        '''
        self.popen("dmesg -c")
        time.sleep(10)
        self.run_shell_cmd(self.HDMI_DEBUG_COMMAND)
        hdmi_info = self.checkoutput('dmesg')
        logging.debug(f'hdmiInfo :{hdmi_info}')
        hactive = self.find_key_value(r'hactive\s(\d+)', hdmi_info)
        vactive = self.find_key_value(r'vactive\s(\d+)', hdmi_info)
        logging.info((hactive, vactive))
        return {
            'resolution': (hactive, vactive),
        }

    def get_tx_hdcp_key(self):
        '''
        get hdcp key
        command : cat /sys/class/amhdmitx/amhdmitx0/hdcp_lstore
        @return: key : str
        '''
        info = self.run_shell_cmd(self.HDCP_TX_KEY_CHECK_COMMAND)[1]
        hdcp_dict = {
            '14': 'HDCP1.4 KEY provisioned onl',
            '14+22': 'both HDCP1.4+2.2 key provisioned',
            '00': 'None HDCP key provisioned'
        }
        logging.info(hdcp_dict[info])
        return info

    def get_tx_hdcp_mode(self):
        '''
        get tx hdcp mode
        command : cat /sys/class/amhdmitx/amhdmitx0/hdcp_mode
        @return: mode : str
        '''
        info = self.run_shell_cmd(self.HDCP_TX_MODE_CHECK_COMMAND)[1]
        mode_info = {
            '14': 'work on HDCP 1.4 mode',
            '22': 'work on HDCP 2.2 mode'
        }
        logging.info(mode_info[info])
        return info

    def get_rx_hdcp_mode(self):
        '''
        get rx hdcp mode
        command : cat /sys/class/amhdmitx/amhdmitx0/hdcp_ver
        @return: mode : str
        '''
        info = self.run_shell_cmd(self.HDMI_RX_MODE_CHECK_COMMAND)[1].split()[0]
        resolution_list = self.hdmiout.get_ratio_list()
        resolution_4k = ('2160p50hz' and '2160p60hz') in resolution_list

        hdcp_dict = {
            '14': 'RX just support HDCP 1.4 mode,Resolution not support 4k' if resolution_4k else '',
            '22': 'RX support HDCP 2.2 mode,Resolution support 4k' if resolution_4k else ''
        }
        logging.info(hdcp_dict[info])
        return info

    def get_tx_hdmi_authenticated(self):
        '''
        get tx hdmi auth
        command : cat /sys/module/hdmitx20/parameters/hdmi_authenticated
        @return: authenticated status : str
        '''
        info = self.run_shell_cmd(self.HDMI_TX_AUTHENTICATED_COMMAND)[1]
        auth_info = {
            '1': 'authentication pass',
            '0': 'authentication fail'
        }
        logging.info(auth_info[info])

    def get_rx_hdcp_key(self):
        '''
        get rx hdcp key
        command : cat /sys/module/tvin_hdmirx/parameters/hdcp22_on
        @return: key : str
        '''
        info = self.run_shell_cmd(self.HDMI_RX_KEY_CHECK_COMMAND)
        key_info = {
            '0': '2.2 key not provisioned',
            '1': '2.2 key provisioned'
        }
        logging.info(key_info[info])
        return info

    def __repr__(self):
        return 'Hdmi check point'
