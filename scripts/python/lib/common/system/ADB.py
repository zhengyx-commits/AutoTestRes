#
# Copyright 2021 Amlogic.com, Inc. or its affiliates. All rights reserved.
#
# AMLOGIC PROPRIETARY/CONFIDENTIAL
#
# You may not use this file except in compliance with the terms and conditions
# set forth in the accompanying LICENSE.TXT file.
#
# THESE MATERIALS ARE PROVIDED ON AN "AS IS" BASIS. AMLOGIC SPECIFICALLY
# DISCLAIMS, WITH RESPECT TO THESE MATERIALS, ALL WARRANTIES, EXPRESS,
# IMPLIED, OR STATUTORY, INCLUDING THE IMPLIED WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT.
#

import logging
import os
import re
import signal
import subprocess
import threading
import time
from contextlib import contextmanager
from xml.dom import minidom

import _io
import pytest

from lib import CheckAndroidVersion
from lib.common import config_yaml
from tools.UiautomatorTool import UiautomatorTool
from tools.resManager import ResManager


def connect_again(func):
    '''
    if connect wifh network , connect again
    :param serialnumber:
    :return:
    '''

    def inner(self, *args, **kwargs):
        if ':5555' in self.serialnumber:
            subprocess.check_output('adb connect {}'.format(self.serialnumber), shell=True, encoding='utf-8')
            self.wait_devices()
        else:
            self.wait_devices()
        return func(self, *args, **kwargs)

    return inner


@contextmanager
def set_timer(timeout, handler=None):
    # NOTE: signals only work in the main thread, so set_timer only works
    # in the main thread
    def _sig_handler(signum, frame):
        # Signal handler for handling signals during operations.
        if signum == signal.SIGALRM:
            raise TimeoutError("operation timed out")

    if timeout:
        logging.debug('in timer with timeout of %s seconds', timeout)
        orig_handler = signal.getsignal(signal.SIGALRM)
        signal.signal(signal.SIGALRM, handler or _sig_handler)
        signal.setitimer(signal.ITIMER_REAL, timeout)
    try:
        yield
    finally:
        # Restore original timer configuration
        if timeout:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, orig_handler)


class PeriodicTimer(threading.Thread):
    """
    Periodic Timer
    """

    def __init__(self, interval, execute, *args, **kwargs):
        threading.Thread.__init__(self)
        self.daemon = False
        self.stopped = threading.Event()
        self.interval = interval
        self.execute = execute
        self.args = args
        self.kwargs = kwargs

    def stop(self):
        if self.is_alive():
            logging.debug("Stopping timer")
            self.stopped.set()
            self.join()

    def run(self):
        while not self.stopped.wait(self.interval):
            self.execute(*self.args, **self.kwargs)


class ADB:
    """
    ADB class Provide common device control functions over the ADB bridge

    Attributes:
        ADB_S : adb multi devices command flags
        DUMP_FILE : ui dump file name

        serialnumber : adb number : str
        name : sub-class name
        unlock_code :
        logdir : testcase result log path
        stay_focus : thread detection flag : boolean
        res_manger : ResManager instance
        live : thread flag , adb status : boolean
        lock : threading.Lock
        build_version : sdk version : str
        p_config_wifi : conf_wifi test data

    """

    ADB_S = 'adb -s '
    DUMP_FILE = '/view.xml'
    OSD_VIDEO_LAYER = 'osd+video'
    DMESG_COMMAND = 'dmesg -S'
    CLEAR_DMESG_COMMAND = 'dmesg -c'

    def __init__(self, name="", unlock_code="", logdir="", stayFocus=False, serialnumber=""):
        self.serialnumber = serialnumber or pytest.config['device_id']
        self.name = name
        self.unlock_code = unlock_code
        self.logdir = logdir or pytest.result_dir
        self.timer = None
        self.stay_focus = stayFocus
        self.res_manager = ResManager()
        self.live = False
        self.lock = threading.Lock()
        self.wait_devices()
        self.build_version = self.getprop(CheckAndroidVersion().get_android_version())
        self.p_config_wifi = config_yaml.get_note('conf_wifi')

    def set_status_on(self):
        '''
        set live to True
        @return: None
        '''
        if not self.live:
            self.lock.acquire()
            self.live = True
            logging.debug(f'Adb status is on')
            self.lock.release()

    def set_status_off(self):
        '''
        set live to False
        @return:
        '''
        if self.live:
            self.lock.acquire()
            self.live = False
            logging.debug(f'Adb status is Off')
            self.lock.release()

    # @property
    def u(self, type="u2"):
        '''
        uiautomater instance
        @return: instance
        '''
        # if not hasattr(self, '_u'):
        self._u = UiautomatorTool(self.serialnumber, type)
        return self._u

    def getUUID(self):
        '''
        get u-disk uuid
        @return: uuid : str
        '''
        self.root()
        UUID = self.run_shell_cmd("ls /storage/ |awk '{print $1}' |head -n 1")[1]
        return UUID

    def getUUIDs(self):
        '''
        get u-disk uuid list
        @return: uuid : list [str]
        '''
        self.root()
        UUIDs = self.run_shell_cmd("ls /storage/ |awk '{print $1}'")[1].split("\n")
        return UUIDs

    def getUUIDSize(self):
        '''
        get u-disk size
        @return: size : [int]
        '''
        uuid = self.getUUID()
        logging.info(f'uuid {uuid}')
        size = self.checkoutput(f"df -h |grep {uuid}|cut -f 3 -d ' '").strip()[:-1]
        return int(float(size))

    def getUUIDAvailSize(self):
        '''
        get u-disk avail size
        @return: size %  : [int]
        '''
        uuid = self.getUUID()
        size = self.checkoutput(f"df -h |grep {uuid}|cut -f 7 -d ' '").strip()[:-1]
        unit = re.findall(r'[A-Za-z]', self.checkoutput(f"df -h |grep {uuid}|cut -f 7 -d ' '"))
        if len(size) == 0:
            size = self.checkoutput(f"df -h |grep {uuid}|cut -f 8 -d ' '").strip()[:-1]
            unit = re.findall(r'[A-Za-z]', self.checkoutput(f"df -h |grep {uuid}|cut -f 8 -d ' '"))
            if len(size) == 0:
                size = 0
                return size
        logging.info(f'213 : {size}')
        if unit[0] == 'G':
            size = int(float(size)) * 1024
        elif unit[0] == 'K':
            size = int(float(size)) / 1024
        return int(float(size))

    def keyevent(self, keycode):
        '''
        input keyevent
        @param keycode: keyevent
        @return: None
        '''
        if isinstance(keycode, int):
            keycode = str(keycode)
        os.system(self.ADB_S + self.serialnumber +
                  " shell input keyevent " + keycode)

    def home(self):
        '''
        ui home button
        @return: None
        '''
        self.keyevent("KEYCODE_HOME")

    def enter(self):
        '''
        ui enter button
        @return: None
        '''
        self.keyevent("KEYCODE_ENTER")

    def root(self):
        '''
        set adb root
        @return: None
        '''
        self.run_adb_cmd_specific_device('root')

    def remount(self):
        '''
        set adb remount
        @return: None
        '''
        self.run_adb_cmd_specific_device('remount')

    def reboot(self):
        '''
        set adb reboot
        @return:
        '''
        self.run_adb_cmd_specific_device('reboot')

    def back(self):
        '''
        ui back button
        @return:
        '''
        self.keyevent("KEYCODE_BACK")

    def app_switch(self):
        '''
        ui app switch button
        @return:
        '''
        self.keyevent("KEYCODE_APP_SWITCH")

    def app_stop(self, app_name):
        '''
        am force stop app
        if timer is setup cancel it
        @param app_name:
        @return:
        '''
        logging.debug("Stop app(%s)" % app_name)
        self.shell("am force-stop %s" % app_name)
        if self.timer is not None:
            logging.debug("Cancel stay focus timer")
            self.timer.stop()
            self.timer = None
        self.kill_logcat_pid()

    def clear_app_data(self, app_name):
        self.run_shell_cmd(f"pm clear {app_name}")

    def expand_logcat_capacity(self):
        self.run_shell_cmd("logcat -G 40M")
        self.run_shell_cmd("renice -n -50 `pidof logd`")

    def delete(self, times=1):
        '''
        ui del button
        @param times: click del times
        @return: None
        '''
        remain = times
        batch = 64
        while remain > 0:
            # way faster delete
            self.keyevent("67 " * batch)
            remain -= batch

    def tap(self, x, y):
        '''
        simulate screen tap
        @param x: x index
        @param y: y index
        @return: None
        '''
        os.system(self.ADB_S + self.serialnumber + " shell input tap " + str(x) + " " + str(y))

    def swipe(self, x_start, y_start, x_end, y_end, duration):
        '''
        simulate swipe screen
        @param x_start: x start index
        @param y_start: y start index
        @param x_end: x end index
        @param y_end: y end index
        @param duration: action time duration
        @return: None
        '''
        os.system(self.ADB_S + self.serialnumber + " shell input swipe " + str(x_start) +
                  " " + str(y_start) + " " + str(x_end) + " " + str(y_end) + " " + str(duration))

    def text(self, text):
        '''
        edittext input text
        @param text: text
        @return: None
        '''
        if isinstance(text, int):
            text = str(text)
        os.system(self.ADB_S + self.serialnumber + " shell input text " + text)

    def clear_logcat(self):
        '''
        clear logcat
        @return: None
        '''
        os.system(self.ADB_S + self.serialnumber + " logcat -b all -c")

    def save_logcat(self, filepath, tag=''):
        '''
        save logcat
        @param filepath: file path for logcat
        @param tag: tag for -s
        @return: log : subprocess.Popen , logcat_file : _io.TextIOWrapper
        '''
        filepath = self.logdir + '/' + filepath
        logcat_file = open(filepath, 'w+')
        if tag and ("grep -E" not in tag) and ("all" not in tag):
            tag = f'-s {tag}'
            log = subprocess.Popen(f"adb -s {self.serialnumber} shell logcat -v time {tag}".split(), stdout=logcat_file, preexec_fn=os.setsid)
        else:
            log = subprocess.Popen(f"adb -s {self.serialnumber} shell logcat -v time {tag}", stdout=logcat_file,
                                   shell=True, stdin=subprocess.PIPE, preexec_fn=os.setsid)
        return log, logcat_file

    def stop_save_logcat(self, log, filepath):
        '''
        stop logcat ternimal , close logcat file
        @param log: logcat popen
        @param filepath: logcat file
        @return: None
        '''
        if not isinstance(log, subprocess.Popen):
            logging.warning('pls pass in the popen object')
            return 'pls pass in the popen object'
        if not isinstance(filepath, _io.TextIOWrapper):
            logging.warning('pls pass in the stream object')
            return 'pls pass int the stream object'
        log.terminate()
        # os.kill(log.pid, signal.SIGTERM)
        filepath.close()

    def start_activity(self, packageName, activityName, intentname=""):
        '''
        start activity over am start
        @param packageName: apk package name
        @param activityName: activity name
        @param intentname: intent name
        @return: None
        '''
        logging.debug("Start activity %s/%s" % (packageName, activityName))
        return_code = os.system(self.ADB_S + self.serialnumber +
                                " shell am start -a " + intentname + " -n " + packageName + "/" + activityName)
        time.sleep(1)

        if self.stay_focus is True and self.timer is None:
            self.timer = PeriodicTimer(5, execute=self._touch)

        if self.timer is not None:
            logging.debug("Start stay focus timer")
            self.timer.start()
        return return_code

    def pull(self, filepath, destination):
        '''
        pull file from DUT to pc
        @param filepath: file path
        @param destination: target path
        @return: None
        '''
        os.system(self.ADB_S + self.serialnumber +
                  " pull " + filepath + " " + destination)

    def push(self, filepath, destination):
        '''
        push file from pc to DUT
        @param filepath: file path
        @param destination: target path
        @return: None
        '''
        os.system(self.ADB_S + self.serialnumber +
                  " push " + filepath + " " + destination)

    def shell(self, cmd):
        '''
        run adb -s xxx shell
        @param cmd: command
        @return: None
        '''
        os.system(self.ADB_S + self.serialnumber + " shell " + cmd)

    def ping(self, interface=None, hostname="www.baidu.com",
             interval_in_seconds=1, ping_time_in_seconds=5,
             timeout_in_seconds=10, size_in_bytes=None):
        """Can ping the given hostname without any packet loss

        Args:
            hostname (str, optional): ip or URL of the host to ping
            interval_in_seconds (float, optional): Time interval between
                                                   pings in seconds
            ping_time_in_seconds (int, optional)  : How many seconds to ping
            timeout_in_seconds (int, optional): wait time for this method to
                                                finish
            size_in_bytes (int, optional): Ping packet size in bytes

        Returns:
            dict: Keys: 'sent' and 'received', values are the packet count.
                  Empty dictionary if ping failed
        """
        ping_output = {}
        if not (hostname and isinstance(hostname, str)):
            logging.error("Must supply a hostname(non-empty str)")
            return False
        p_conf_wifi_ping_count = 5
        try:
            # ping_time_in_seconds = pytest.config.get("wifi")['ping_count']
            p_conf_wifi_ping_count = self.p_config_wifi['wifi']['ping_count']
        except Exception as e:
            logging.error("Failed.Reason: " + repr(e) +
                          " in config doesn't exist, so use the default value " + str(p_conf_wifi_ping_count))
        count = int(p_conf_wifi_ping_count / interval_in_seconds)
        timeout_in_seconds += p_conf_wifi_ping_count
        # Changing count based on the interval, so that it always finishes
        # in ping_time seconds

        try:
            # ping_percentge = pytest.config.get("wifi")['ping_pass_percentage']
            p_conf_wifi_ping_pass_percentage = self.p_config_wifi['wifi']['ping_pass_percentage']
        except Exception as e:
            p_conf_wifi_ping_pass_percentage = 0
            logging.error("Failed.Reason: " + repr(e) +
                          " in config doesn't exist, so use the default value " +
                          str(p_conf_wifi_ping_pass_percentage))
        ping_pass_percentage = int(count * p_conf_wifi_ping_pass_percentage * 0.01)
        # if "rtos" in pytest.device.get_platform():
        #     hostname = "8.8.8.8"
        #     cmd = "%s %s %s" % (pytest.wifi.ACE_CLI_PING_RTOS, hostname,
        #                         count)
        # else:
        if interface:
            if size_in_bytes:
                cmd = "ping -i %s -I %s -c %s -s %s %s" % (
                    interval_in_seconds, interface, count, size_in_bytes, hostname)
            else:
                cmd = "ping -i %s -I %s -c %s %s" % (interval_in_seconds, interface, count, hostname)
        else:
            if size_in_bytes:
                cmd = "ping -i %s -c %s -s %s %s" % (
                    interval_in_seconds, count, size_in_bytes, hostname)
            else:
                cmd = "ping -i %s -c %s %s" % (interval_in_seconds, count, hostname)
        logging.debug("Ping command: %s" % cmd)
        output = self.run_shell_cmd(cmd)
        if output[0]:
            logging.debug(output[0])
            return False
        else:
            logging.debug(output[0])
        # rc, result = self.run_shell_cmd(cmd,  timeout=timeout_in_seconds)
        RE_PING_STATUS = re.compile(
            r".*(---.+ping statistics ---\s+\d+ packets transmitted, \d+ received, "
            r"(?:\+\d+ duplicates, )?(\d+)% packet loss, time.+ms\s*?rtt\s+?"
            r"min/avg/max/mdev)\s+?=\s+?(\d+(\.\d+)?)/(\d+(\.\d+)?)/(\d+(\.\d+)?)"
            r"/(\d+(\.\d+)?)\s+?ms.*?")
        match = RE_PING_STATUS.search(output[1])
        # logging.info(output)
        # logging.info(match)
        ping_output['duplicates'] = 0
        if match:
            stats = match.group(1).split('\n')[1].split(',')
            ping_output['transmitted'] = int(
                stats[0].split()[0].strip())
            ping_output['received'] = int(stats[1].split()[0].strip())
            if 'duplicates' in match.group(1):
                ping_output['duplicates'] = int(
                    stats[2].split()[0].strip().split('+')[1])
            ping_output['packet_loss'] = int(match.group(2))
            logging.debug("Ping Stats Dictionary:-{}".format(ping_output))
            expected_pkt_loss = int(((count - ping_pass_percentage) /
                                     count) * 100)
            if ping_output['packet_loss'] <= expected_pkt_loss:
                return True

    def check_apk_exist(self, package_name):
        return True if package_name in self.checkoutput('pm list packages') else False

    def install_apk(self, apk_path):
        '''
        install apk from pc
        @param apk_path: apk path
        @return: install status : boolean
        '''
        apk_path = self.res_manager.get_target(apk_path)
        cmd = ['install', '-r', '-t', apk_path]
        logging.info(cmd)
        output = self.run_adb_cmd_specific_device(cmd)[1].decode().strip().split('\n')
        time.sleep(5)
        logging.info(output)
        if 'Success' in output:
            logging.info('APK install successful')
            return True
        else:
            logging.info('APK install failed')
            return False

    def uninstall_apk(self, apk_name):
        '''
        uninstall apk
        @param apk_name: apk name
        @return: uninstall status : boolean
        '''
        cmd = ['uninstall', apk_name]
        logging.info(cmd)
        output = self.run_adb_cmd_specific_device(cmd)[1].decode().strip().split('\n')
        time.sleep(5)
        logging.info(output)
        if 'Success' in output:
            logging.info('APK uninstall successful')
            return True
        else:
            logging.info('APK uninstall failed')
            return False

    @classmethod
    def check_rc(cls, rc, message=None):
        '''
        Checks return code and raises if non-zero
        @param rc: return code
        @param message: error message
        @return:
        '''
        if rc:
            raise RuntimeError(message)

    def check_terminal_cmd(cls, cmdcheck):
        '''
        run terminal command and check return code
        @param cmdcheck: command
        @return: command status : boolean
        '''
        with set_timer(3):
            try:
                output = subprocess.Popen(cmdcheck.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)
                output_lines = output.stdout.readlines()
                for line in output_lines:
                    ret = re.findall(r'bin', line.decode('utf-8'))
                    if ret:
                        logging.info(f"check_terminal_cmd pass! cmdcheck:{cmdcheck}, line:{line}")
                        return True
            except subprocess.CalledProcessError as e:
                output = e.output
                logging.debug(f"CalledProcessError output:{output}")
        return False

    def run_terminal_cmd(cls, cmd, timeout=0, verbose=True, output_stderr=False):
        '''
        run terminal command and return rt and feedback
        @param cmd: command
        @param timeout: timeout
        @param verbose: debug info output control
        @param output_stderr: stderr feedback control
        @return: return code , output : tuple
        '''
        # Run command on current terminal.
        rc = 1
        output = b''
        logging.debug("<<<%s>>>", cmd)
        cmdlist = cmd.split()
        if cmdlist:
            cmdcheck = "which " + cmdlist[0]
            ret = cls.check_terminal_cmd(cmdcheck)
            if ret:
                with set_timer(timeout):
                    try:
                        output = subprocess.Popen(cmdlist, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)
                        rc = 0
                    except subprocess.CalledProcessError as e:
                        output = e.output
                        rc = e.returncode
                    if verbose:
                        logging.debug("(%s){{{%s}}}", rc, output)
                    if output_stderr:
                        return rc, output.stderr.readlines()
                    else:
                        return rc, output.stdout.readlines()

    @classmethod
    def run_adb_cmd(cls, cmd, timeout=0, verbose=True):
        '''
        run adb command
        @param cmd: command
        @param timeout: time out
        @param verbose: debug info output control
        @return: return code , feedback : tuple
        '''
        # Run adb command.
        # adbpath = adbpath or cls.find_adb()
        cmd = ['adb'] + cmd
        rc = 1
        output = b''
        logging.debug("<<<%s>>>", cmd)
        with set_timer(timeout):
            try:
                output = subprocess.check_output(cmd).strip()
                rc = 0
            except subprocess.CalledProcessError as e:
                output = e.output
                rc = e.returncode
            if verbose:
                logging.debug("(%s){{{%s}}}", rc, output)
            return rc, output

    # @connect_again
    def run_adb_cmd_specific_device(self, cmd, timeout=0, verbose=True):
        '''
        runs adb command specific to a device
        @param cmd: command
        @param timeout: time out
        @param verbose: debug info output control
        @return: return code , feedback : tuple
        '''
        if isinstance(cmd, str):
            cmd = [cmd]
        cmd = ['-s', self.serialnumber] + cmd

        return self.run_adb_cmd(cmd, timeout=timeout, verbose=verbose)

    def run_shell_cmd(self, cmd, timeout=0):
        '''
        run shell command
        @param cmd: command
        @param timeout: time out
        @return: return code , feedback : tuple
        '''
        shell_cmd = ['shell', cmd]
        rc, output = self.run_adb_cmd_specific_device(shell_cmd, timeout=timeout)
        return rc, output.decode('utf-8', errors='ignore')

    def setprop(self, key, value, timeout=0):
        '''
        Set property to device
        @param key: prop key
        @param value: prop value
        @param timeout: time out
        @return: command feedback
        '''
        rc, output = self.run_shell_cmd('setprop %s %s' % (key, value), timeout=timeout)
        self.check_rc(rc, 'can not setprop: %s %s' % (key, value))
        return output

    def getprop(self, key, timeout=0):
        '''
        Get property from device
        @param key: prop key
        @param timeout: time out
        @return: feedback output
        '''
        rc, output = self.run_shell_cmd('getprop %s' % key, timeout=timeout)
        self.check_rc(rc, 'can not getprop: %s' % key)
        return output

    def rm(self, flags, path):
        '''
        rm file
        @param flags: flags such as -r
        @param path: file path
        @return: None
        '''
        os.system(self.ADB_S + self.serialnumber + " shell rm " + flags + " " + path)

    def uiautomator_dump(self, filepath='', uiautomator_type='u2'):
        '''
        dump ui xml over uiautomator
        @param filepath: file path
        @return: None
        '''
        if not filepath:
            filepath = self.logdir
        logging.debug('doing uiautomator dump')
        if uiautomator_type == 'u2':
            xml = self.u().d2.dump_hierarchy()
        else:
            uiautomator_type = 'u1'
            xml = self.u(type=uiautomator_type).d1.dump()
        if not filepath.endswith('view.xml'):
            filepath += self.DUMP_FILE
        logging.debug(filepath)
        with open(filepath, 'w') as f:
            f.write(xml)
        logging.debug('uiautomator dump done')

    def get_dump_info(self):
        '''
        get ui dump info
        @return: dumo info : str
        '''
        path = self.logdir + self.DUMP_FILE if os.path.exists(
            self.logdir + self.DUMP_FILE) else self.logdir + '/window_dump.xml'
        with open(path, 'r') as f:
            temp = f.read()
        if '错误代码' in temp:
            logging.warning('Server Exception')
            self.find_and_tap('返回重试', 'text')
        return temp

    def expand_notifications(self):
        '''
        expand android notification bar
        @return: None
        '''
        os.system(self.ADB_S + self.serialnumber + " shell cmd statusbar expand-notifications")

    def _screencap(self, filepath, layer="osd", app_level=28):
        '''
        screencap cmd get png style picture
        screencatch -m cmd get bmp style picture
        pngtest cmd get jpeg style picture layer default osd
        can set video or osd+video type
        @param filepath: file path
        @param layer: layer
        @param app_level: sdk version
        @return: None
        '''

        if layer == "osd":
            os.system(self.ADB_S + self.serialnumber + " shell screencap -p " + filepath)
        else:
            png_type = 1
            if layer == "video" or layer == self.OSD_VIDEO_LAYER:
                if app_level > 28:
                    self.screencatch(layer)
                else:
                    if layer == "video":
                        png_type = 0
                    cmd = "pngtest " + str(png_type)
                    self.run_shell_cmd(cmd)
            else:
                logging.info("please check the set screen layer arg")

    def screenshot(self, destination, layer="osd", app_level=28):
        '''
        pull screen catch file to logdir
        @param destination: target path
        @param layer: screen layer type
        @param app_level: sdk version
        @return: None
        '''
        app_level = int(self.build_version)
        if layer == "osd":
            devicePath = "/sdcard/screen.png"
            destination = self.logdir + "/" + "screencap_" + destination + ".png"
        else:
            dirs = self.mkdir_temp()
            if app_level > 28:
                devicePath = dirs + "/1.bmp"
                destination = self.logdir + "/" + "screencatch_" + destination + ".bmp"
            else:
                devicePath = dirs + "/1.jpeg"
                destination = self.logdir + "/" + "pngtest_" + destination + ".jpeg"
        self._screencap(devicePath, layer, app_level)
        time.sleep(2)
        self.pull(devicePath, destination)
        time.sleep(2)
        if layer == "osd":
            self.rm("", devicePath)
        else:
            self.rm("-r", dirs)

    def continuous_screenshot(self, destination, layer="osd+video", app_level=30, screenshot_counter=3):
        '''
        continuous screenshot just for Android Q/R, set counter >1
        @param destination: target path
        @param layer: screen layer type
        @param app_level: sdk version
        @param screenshot_counter: screen shot times
        @return: None
        '''
        app_level = int(self.build_version)
        dirs = self.mkdir_temp()
        if app_level > 28 and screenshot_counter > 1 and (layer == "video" or layer == self.OSD_VIDEO_LAYER):
            self.screencatch(layer, screenshot_counter)
            time.sleep(5)
            for i in range(screenshot_counter):
                i = i + 1
                devicePath = dirs + "/" + str(i) + ".bmp"
                logging.info(devicePath)
                destination_temp = self.logdir + "/" + "screencatch_" + destination + "_" + str(i) + ".bmp"
                self.pull(devicePath, destination_temp)
                time.sleep(2)
        else:
            logging.info('you can use screenshot cmd')
        self.rm("-r", dirs)

    def screencatch(self, layer="osd+video", counter=1):
        '''
        screencatch [-p/-j/-m/-b] [-c <counter>] [-t <type>] [left  top  right  bottom  outWidth  outHeight]
            Args:
               -m  :  save as bmp file(android R not support png/jpeg)
               -c <counter> : continually save file with counter, default as 1
               -t <type> : set capture type:
                  0 -- video only
                  1 -- video+osd (default)
        @param layer: screen layer type
        @param counter: screen shot times
        @return: None
        '''

        if layer == self.OSD_VIDEO_LAYER:
            capture_type = "1"
        else:
            capture_type = "0"
        cmd = "screencatch -m " + " -t " + capture_type + " -c " + str(counter)
        logging.info(cmd)
        self.run_shell_cmd(cmd)

    def video_record(self, destination, app_level=28, record_time=30, sleep_time=30,
                     frame=30, bits=4000000, type=1):
        '''
        video record 后pull到logdir目录下 (the command maybe is not ok when record security video,
                                          example youtube/googleMovies DRM security video)
        Android R support args, Android P not support args just can use tspacktest command
        tspacktest [-h] [-f <framerate>] [-b <bitrate>] [-t <type>] [-s <second>] [<width> <height>]
            Args:
               -f <framerate>: frame per second, unit bps, default as 30
               -b <bitrate>  : bits per second, unit bit, default as 4000000
               -t <type>     : select video-only(0) or video+osd(1), default as video+osd
               -s <second>   : record times, unit second(s), default as 30
        '''
        app_level = int(self.build_version)
        destination = self.logdir + "/" + "video_record_" + destination + ".ts"
        dirs = self.mkdir_temp()
        if app_level <= 28:
            video_record = self.popen("shell tspacktest")
            time.sleep(sleep_time)
            os.kill(video_record.pid, signal.SIGTERM)
        else:
            cmd = "tspacktest -f " + str(frame) + " -b " + str(bits) + " -t " + str(type) + " -s " + str(record_time)
            logging.info(cmd)
            self.run_shell_cmd(cmd)
        time.sleep(2)
        video = dirs + "/video.ts"
        self.pull(video, destination)
        time.sleep(5)
        self.rm("-r", dirs)

    def mkdir_temp(self):
        '''
        mkdir temp folder , chmod 777
        @return: folder path
        '''
        self.root()
        dirs = '/data/temp'
        temp = self.run_shell_cmd("ls /data")[1]
        if "temp" not in temp:
            self.run_shell_cmd("mkdir " + dirs)
        self.run_shell_cmd("chmod 777 " + dirs)
        return dirs

    def unlock(self):
        '''
        unlock devices
        @return: None
        '''
        logging.debug("Try unlock the device")
        if self.check_lock_status():
            logging.debug("Device is locked")
            time.sleep(1)
            self.shell("input keyevent 82")
            time.sleep(1)
            self.shell("input text %s" % (self.unlock_code))
            self.shell("input keyevent 66")
        else:
            logging.debug("Device is unlocked")

    def check_lock_status(self):
        '''
        check devices lock status
        @return: lock status : boolean
        '''
        self.shell("input keyevent 82")
        command = "adb -s %s shell dumpsys nfc | grep 'mScreenState='" % (
            self.serialnumber)
        cmd = command.split()
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        output = proc.communicate()[0].decode()
        return output.find("_LOCKED") != -1 or output.find("OFF_UNLOCKED") != -1

    def _touch(self):
        self.shell("input keyevent mouse")
        return True

    def check_adb_status(self, waitTime=100):
        '''
        check adb status
        @param waitTime: the time of detection
        @return: adb status : boolean
        '''
        i = 0
        waitCnt = waitTime / 5
        while i < waitCnt:
            command = "adb devices"
            cmd = command.split()
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
            adb_devices = proc.communicate()[0].decode()
            rc = proc.returncode
            if rc == 0 and self.serialnumber in adb_devices and \
                    len(self.serialnumber) != 0:
                return True
            i = i + 1
            time.sleep(5)
            logging.debug("Still waiting..")
        return False

    def wait_and_tap(self, searchKey, attribute, times=5):
        '''
        wait for android widget then tap it , wait 5 seconds
        @param searchKey: widget key
        @param attribute: widget attr
        @return:
        '''
        for _ in range(times):
            if self.find_element(searchKey, attribute):
                self.find_and_tap(searchKey, attribute)
                return 1
            time.sleep(1)

    def wait_element(self, searchKey, attribute):
        '''
        wait for android widget , wait 5 seconds
        @param searchKey: widget key
        @param attribute: widget attr
        @return:
        '''
        for _ in range(5):
            if self.find_element(searchKey, attribute):
                return 1
            time.sleep(1)

    def find_element(self, searchKey, attribute, extractKey=None):
        '''
        find element in the ui dump info
        @param searchKey: element key
        @param attribute: element attr
        @param extractKey:
        @return:
        '''
        logging.info('find_element')
        filepath = self.logdir + self.DUMP_FILE
        self.uiautomator_dump(filepath)
        xml_file = minidom.parse(filepath)
        itemlist = xml_file.getElementsByTagName('node')
        for item in itemlist:
            # print(item.attributes[attribute].value)
            if searchKey == item.attributes[attribute].value:
                return item.attributes[attribute].value if extractKey is None else item.attributes[extractKey].value
        return None

    def find_pos(self, searchKey, attribute):
        '''
        find widget position
        @param searchKey: widget key
        @param attribute: widget attr
        @return: position x , position y : tuple
        '''
        logging.info('find_pos')
        filepath = self.logdir + self.DUMP_FILE
        self.uiautomator_dump(filepath)
        xml_file = minidom.parse(filepath)
        itemlist = xml_file.getElementsByTagName('node')
        bounds = None
        for item in itemlist:
            logging.debug(f'try to find {searchKey} - {item.attributes[attribute].value}')
            if searchKey == item.attributes[attribute].value:
                bounds = item.attributes['bounds'].value
                break
        if bounds is None:
            logging.error("attr: %s not found" % attribute)
            return -1, -1
        bounds = re.findall(r'\[(\d+)\,(\d+)\]', bounds)
        # good for debugging button press coordinates
        # print(bounds)
        x_start, y_start = bounds[0]
        x_end, y_end = bounds[1]
        x_midpoint, y_midpoint = (int(x_start) + int(x_end)) / 2, (int(y_start) + int(y_end)) / 2
        logging.debug(f'{x_midpoint} {y_midpoint}')
        return (x_midpoint, y_midpoint)

    def find_and_tap(self, searchKey, attribute):
        '''
        find widget and tap
        @param searchKey: widget key
        @param attribute: widget attr
        @return: position x , position y : tuple
        '''
        logging.info(f'find_and_tap {searchKey}')
        x_midpoint, y_midpoint = self.find_pos(searchKey, attribute)
        if (x_midpoint, y_midpoint) != (-1, -1):
            self.tap(x_midpoint, y_midpoint)
            # time.sleep(1)
        return x_midpoint, y_midpoint

    def text_entry(self, text, searchKey, attribute, delete=64):
        '''
        find edittext and input text
        @param text: input text
        @param searchKey: edittext key
        @param attribute: edittext attr
        @param delete: del 退格
        @return: position x , position y : tuple
        '''
        filepath = self.logdir + self.DUMP_FILE
        self.uiautomator_dump(filepath)
        xml_file = minidom.parse(filepath)
        itemlist = xml_file.getElementsByTagName('node')
        bounds = None
        for item in itemlist:
            if searchKey.upper() in item.attributes[attribute].value.upper():
                if "EditText" in item.attributes['class'].value:
                    bounds = item.attributes['bounds'].value
                    break
        if bounds is None:
            return None
        bounds = re.findall(r'\[(\d+)\,(\d+)\]', bounds)
        x_start, y_start = bounds[0]
        x_end, y_end = bounds[1]
        x_midpoint, y_midpoint = (int(x_start) + int(x_end)) / 2, (int(y_start) + int(y_end)) / 2

        self.tap(x_midpoint, y_midpoint)

        # move to the end, and delete characters
        # TODO. This should be a select-all and delete but there is no easy way
        # to do this
        self.keyevent("KEYCODE_MOVE_END")
        self.delete(delete)

        # enter the text
        self.text(text)

        # hit enter
        self.keyevent("KEYCODE_ENTER")
        return x_midpoint, y_midpoint

    def wait_devices(self):
        '''
        check adb exists if not wait for one minute
        @return: None
        '''
        if subprocess.run(f'adb -s {self.serialnumber} shell getprop sys.boot_completed', shell=True,
                          encoding='utf-8', stdout=subprocess.PIPE).returncode == 1:
            logging.info('devices exists')
        else:
            count = 0
            while subprocess.run(f'adb -s {self.serialnumber} shell getprop sys.boot_completed', shell=True,
                                 encoding='utf-8', stdout=subprocess.PIPE).returncode != 0:
                if count % 10 == 0:
                    logging.info('devices not exists')
                self.set_status_off()
                # subprocess.check_output('adb connect {}'.format(self.serialnumber), shell=True, encoding='utf-8')
                time.sleep(3)
                count += 1
                if count > 20:
                    raise EnvironmentError('Lost Device')
            self.set_status_on()

    def kill_logcat_pid(self):
        '''
        kill all logcat in pc
        @return: None
        '''
        self.run_shell_cmd("killall logcat")

    # @connect_again
    def popen(self, command):
        '''
        run adb command over popen
        @param command: command
        @return: subprocess.Popen
        '''
        logging.debug(f"command:{self.ADB_S + self.serialnumber + ' ' + command}")
        cmd = self.ADB_S + self.serialnumber + ' ' + command
        return subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8', preexec_fn=os.setsid)

    def checkoutput(self, command):
        '''
        run adb command over check_output
        raise error if not success
        @param command: command
        @return: feedback
        '''
        command = self.ADB_S + self.serialnumber + ' shell ' + command
        return self.checkoutput_term(command)

    def checkoutput_term(self, command):
        '''
        run pc command over check_output
        raise error if not success
        @param command: command
        @return: feedback
        '''
        logging.debug(f"command:{command}")
        return subprocess.check_output(command, shell=True, encoding='utf-8')

    # @connect_again
    def subprocess_run(self, command):
        '''
        run adb command over subporcess.run
        @param command: command
        @return: subprocess.CompletedProcess
        '''
        return subprocess.run(self.ADB_S + self.serialnumber + ' shell ' + command,
                              shell=True, encoding='utf-8', check=False)

    def open_omx_info(self):
        '''
        open omx logcat
        @return: None
        '''
        self.run_shell_cmd("setprop media.omx.log_levels 255")
        self.run_shell_cmd("setprop vendor.media.omx.log_levels 255")

    def close_omx_info(self):
        '''
        close omx logcat
        @return: None
        '''
        self.run_shell_cmd("setprop media.omx.log_levels 0")
        self.run_shell_cmd("setprop vendor.media.omx.log_levels 0")

    def factory_reset(self):
        '''
        factory reset over adb
        @return:
        '''
        self.checkoutput_term('adb reboot bootloader')
        self.set_status_off()
        for i in range(10):
            if 'fastboot' in self.checkoutput_term('fastboot devices'):
                break
            time.sleep(3)
        try:
            self.checkoutput_term('fastboot flashing unlock_critical')
            time.sleep(1)
            self.checkoutput_term('fastboot flashing unlock')
            time.sleep(1)
            self.checkoutput_term('fastboot -w')
            time.sleep(2)
        except subprocess.CalledProcessError as e:
            logging.info('Error occur')
        self.checkoutput_term('fastboot reboot')
        time.sleep(120)
