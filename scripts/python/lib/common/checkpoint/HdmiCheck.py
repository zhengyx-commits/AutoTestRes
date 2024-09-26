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
    KERNEL_VERSION = 'uname -r'
    HDMI_DEBUG_COMMAND = 'echo state > /sys/class/hdmirx/hdmirx0/debug'
    EDID_COMMAND = 'cat /sys/class/amhdmitx/amhdmitx0/rawedid'
    ANALYZED_EDID_COMMAND = 'cat /sys/class/amhdmitx/amhdmitx0/edid'
    EDID_PARSING_COMMAND = 'cat /sys/class/amhdmitx/amhdmitx0/edid_parsing'

    HDCP_TX_KEY_CHECK_COMMAND = 'cat /sys/class/amhdmitx/amhdmitx0/hdcp_lstore'
    HDCP_TX_MODE_CHECK_COMMAND = 'cat /sys/class/amhdmitx/amhdmitx0/hdcp_mode'
    HDMI_TX_AUTHENTICATED_KERNEL4_COMMAND = 'cat /sys/module/hdmitx20/parameters/hdmi_authenticated'
    HDMI_TX_AUTHENTICATED_KERNEL5_COMMAND = 'cat /sys/module/aml_media/parameters/hdmi_authenticated'

    HDMI_RX_KEY_CHECK_COMMAND = 'cat /sys/module/tvin_hdmirx/parameters/hdcp22_on'
    HDMI_RX_AUTHENTICATED_COMMAND = 'echo state2 > /sys/class/hdmirx/hdmirx0/debug'
    HDMI_RX_MODE_CHECK_COMMAND = 'cat /sys/class/amhdmitx/amhdmitx0/hdcp_ver'
    HDMI_TX_MODE = 'cat /sys/class/amhdmitx/amhdmitx0/hpd_state'

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

    def get_raw_edid(self):
        info = self.run_shell_cmd(self.EDID_COMMAND)[1]
        return info

    def get_edid_parsed(self):
        info = self.run_shell_cmd(self.EDID_PARSING_COMMAND)[1]
        return info

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
        version = self.run_shell_cmd(self.KERNEL_VERSION)[1]
        if ("5.15" or "5.4") in version:
            info = self.run_shell_cmd(self.HDMI_TX_AUTHENTICATED_KERNEL5_COMMAND)[1]
        else:
            info = self.run_shell_cmd(self.HDMI_TX_AUTHENTICATED_KERNEL4_COMMAND)[1]
        auth_info = {
            '1': 'authentication pass',
            '0': 'authentication fail'
        }
        logging.info(auth_info[info])
        print("11111111", auth_info)
        return info

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

    def check_tx_mode(self):
        '''
        check_tx_mode
        command : cat /sys/class/amhdmitx/amhdmitx0/hpd_state
        @return: key : str
        '''
        info = self.run_shell_cmd(self.HDMI_TX_MODE)[1]
        mode_info = {
            '0': 'TX is not connected',
            '1': 'TX is connected'
        }
        logging.info(mode_info[info])
        return info

    def check_tx_22(self):
        """
        check_tx_22_key
        command : tee_provision -q -t 0x32
        @return: key : str
        """
        check_tx_22_key = str(self.subprocess_run('tee_provision -q -t 0x32'))
        logging.info(f'check_tx_22_key is {check_tx_22_key}')
        check_vendor_tx22 = str(self.subprocess_run('ls -la /vendor/bin/hdcp_tx22'))
        logging.info(f'check_vendor_tx22 is {check_vendor_tx22}')
        if 'returncode=1' in check_vendor_tx22:
            return False
        else:
            return True

    def write_to_tx_22_key(self, path):
        """
        write_to_tx_22_key
        command :
        adb push path/firmware.le /odm/etc/firmware/; chmod 644 /odm/etc/firmware/firmware.le
        adb push path/hdcp_tx22 /vendor/bin/ ; chmod 755 /vendor/bin/hdcp_tx22
        # adb push path/hdcp22_fw_private.bin.factory-user.enc; /storage/emulated/0/
        # tee_provision -i /storage/emulated/0/hdcp22_fw_private.bin.factory-user.enc
        restorecon /vendor/bin/hdcp_tx22
        reboot
        @return: key : str
        """
        self.remount()
        self.push(filepath=path + '/firmware.le', destination='/odm/etc/firmware/')
        self.run_shell_cmd('chmod 644 /odm/etc/firmware/firmware.le')
        self.push(filepath=path + '/hdcp_tx22', destination='/vendor/bin/hdcp_tx22')
        self.run_shell_cmd('chmod 755 /vendor/bin/hdcp_tx22')
        self.run_shell_cmd('restorecon /vendor/bin/hdcp_tx22')
        self.reboot()
        time.sleep(30)
        self.wait_devices()
        self.root()
        self.remount()

