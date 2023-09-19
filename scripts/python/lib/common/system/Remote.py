import logging
import re
import threading
import time

import pytest

from lib.common.system.ADB import ADB


class Remote(ADB):

    TIMER_TIMEOUT = 20
    DEMSG_CLEAR = 'dmesg -c'
    DEMSG_STR = 'dmesg | grep bl:'
    DMESG_HDCP_PWR = "dmesg | grep hdcp_pwr"
    ACTURAL_KEY_CODE_LOGCAT = []

    def __init__(self):
        super(Remote, self).__init__()
        self.run_shell_cmd(self.DEMSG_CLEAR)

    def power(self):
        logging.info("get power key")
        pytest.irremote.send_irkey(pytest.remotekeymap.KEYEVENT_POWER)

    def enter(self):
        logging.info("get enter key")
        pytest.irremote.send_irkey(pytest.remotekeymap.KEYEVENT_ENTER)

    def back(self):
        logging.info("get back key")
        pytest.irremote.send_irkey(pytest.remotekeymap.KEYEVENT_BACK)

    def right(self):
        logging.info("get right key")
        pytest.irremote.send_irkey(pytest.remotekeymap.KEYEVENT_RIGHT)

    def left(self):
        logging.info("get left key")
        pytest.irremote.send_irkey(pytest.remotekeymap.KEYEVENT_LEFT)

    def up(self):
        logging.info("get up key")
        pytest.irremote.send_irkey(pytest.remotekeymap.KEYEVENT_UP)

    def down(self):
        logging.info("get down key")
        pytest.irremote.send_irkey(pytest.remotekeymap.KEYEVENT_DOWN)

    def power_status(self, flag):
        power_status = ""
        if flag == "tv":
            str_info = self.run_shell_cmd(self.DEMSG_STR)[1]
            logging.info(str_info)
            power_status = re.findall(r'bl: backlight (\S* \S*)', str_info)
            if power_status:
                t = str(power_status[0]).replace(' ', '_')
                self.screenshot(t)
                if power_status[0] == 'power off':
                    logging.info('device standy by')
                if power_status[0] == 'power on':
                    logging.info('device awake')
            else:
                logging.info('no STR info,please check broadlink and device')
        elif flag == "ott":
            hdcp_pwr_info = self.run_shell_cmd(self.DMESG_HDCP_PWR)[1]
            logging.info(hdcp_pwr_info)
            power_status = re.findall(r"hdcp_pwr (\d+)", hdcp_pwr_info)
            logging.info(f"power_status: {power_status}")
            if power_status:
                self.screenshot("ott_power")

        return power_status

    def check_power(self, flag=None):
        str1 = ''
        str2 = ''
        sleeptimer = threading.Timer(self.TIMER_TIMEOUT, self.power)
        try:
            if not pytest.irremote.remote:
                pytest.skip("irremote not found.")
            self.run_shell_cmd(self.DEMSG_CLEAR)
            pytest.irremote.send_irkey(pytest.remotekeymap.KEYEVENT_POWER)
            time.sleep(3)
            str1 = self.power_status(flag)
            sleeptimer.start()
            time.sleep(25)
            str2 = self.power_status(flag)
            if str1 and str2 and str1 != str2:
                logging.info('standby and awake switch successfully')
            else:
                logging.info('standby and awake switch failed')
        except Exception as e:
            pytest.fail(str(e))
        finally:
            sleeptimer.cancel()
        return str1, str2

    def remote_key_status(self, timeout=60):
        start_time = time.time()
        self.clear_logcat()
        p = self.popen("logcat -s keyMonitor")
        while True:
            recv = p.stdout.readline()
            logging.debug(f"recv:{recv}")
            # "KeyMonitor: keycode 20 action true"
            regex = re.findall(r"keyMonitor: keycode (\d+) action true", recv)
            if len(regex) != 0:
                logging.info(f"regex[0]: {regex[0]}")
                self.ACTURAL_KEY_CODE_LOGCAT.append(regex[0])
            if time.time() - start_time > timeout:
                break
        return self.ACTURAL_KEY_CODE_LOGCAT

    def run(self):
        t = threading.Thread(target=self.remote_key_status,name='RemoteKey')
        t.setDaemon(True)
        t.start()
