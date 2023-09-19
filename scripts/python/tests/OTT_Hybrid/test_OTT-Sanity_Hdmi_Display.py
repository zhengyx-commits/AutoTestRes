from lib.common.system.HdmiOut import HdmiOut
from lib.common.checkpoint.HdmiCheck import HdmiCheck
import logging
import os
import time
import pytest

hdmi = HdmiCheck()
hdmiout = HdmiOut()


def test_display_hdmiout():
    hdmi.check_rx_hdcp_mode()
    hdmiout.run_shell_cmd(hdmiout.ENABLE_DEBUG_COMMAND)
    hdmiout.switch_resolution()
    hdmiout.run_shell_cmd(hdmiout.DISABLE_DEBUG_COMMAND)
    assert hdmiout.resolution
    logging.info('total switch{},failed{}, failed to switch{}'.format(hdmiout.switch_times, hdmiout.switch_error_times
                                                                      , hdmiout.switch_error_list))
    logging.info('cannot switch{}, failed{}'.format(hdmiout.switch_fail_list, hdmiout.switch_fail_times))
    assert hdmiout.switch_error_times == 0
    assert hdmiout.switch_fail_times == 0


def test_reboot_check_displayermode():
    os.system('adb reboot;sleep 30')
    time.sleep(10)
    os.system('adb root')
    time.sleep(10)
    reboot_current = hdmi.run_shell_cmd(hdmiout.GET_RATIO_COMMAND)[1]
    logging.info(f'After reboot Current radio: {reboot_current}')
