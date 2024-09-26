#!/usr/bin/env python
# Copyright 2020 Amlogic.com, Inc. or its affiliates. All rights reserved.
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
import platform
import re
import time
import subprocess
import sys
import random
import fcntl
import pytest
import datetime
import signal

from abc import ABCMeta, abstractmethod
from queue import Queue, Empty
from threading import Lock, Thread, Event

from tools.KpiAnalyze import KpiAnalyze
from . import AATSTarget, set_timer

from ..exceptions import CLIEndpointNotAvailableError, AATSRuntimeError, AATSDeviceNotFoundError
from util.errors import Errors
from past.builtins import basestring

log = logging.getLogger(__name__)


class ADBRuntimeError(Errors.DeviceUnavailableError):
    pass


class ProcBufferedReader(metaclass=ABCMeta):
    """
    Reader on adb shell output with buffering
    """

    def __init__(self, wait_cmd, logfile, kpifile):
        # def __init__(self, wait_cmd, logfile, logcatfile, kpifile):
        self._wait_cmd = wait_cmd
        self._sub_proc = None
        self._sub_proc_lock = Lock()
        self._stop = Event()
        self._read_buffer = Queue()
        self._buffering_thread = Thread(target=self._queue_loop, name='queue_loop')
        self._buffering_thread.daemon = True
        self._buffering_thread.start()
        self._logfile = logfile
        # self._logcatfile = logcatfile

    def wait_for_device(self):
        try:
            subprocess.check_output(self._wait_cmd, timeout=120)
            return True
        except Exception as exp:
            log.debug("reader: wait-for-device failed/timedout: {}".format(exp))
        return False

    def is_process_running(self):
        if self._sub_proc and not self._sub_proc.poll():
            try:
                os.kill(self._sub_proc.pid, 0)
            except (OSError, AttributeError):
                return False
            else:
                return True
        return False

    @abstractmethod
    def _read_once(self):
        pass

    def _queue_loop(self):
        while not self._stop.isSet():
            c = self._read_once()
            if not self._logfile:
                self._read_buffer.put(c)

    def read(self):
        content = b''
        while True:
            try:
                content += self._read_buffer.get_nowait()
            except Empty:
                break
        return content

    def close(self):
        self._stop.set()


class AdbShellReader(ProcBufferedReader):

    # def __init__(self, adb_cmd, wait_cmd, logfileobj=None, logcatfileobj=None, kpifileobj=None):
    def __init__(self, adb_cmd, wait_cmd, logfileobj=None, kpifileobj=None):
        self.adb_cmd = adb_cmd
        # super(AdbShellReader, self).__init__(wait_cmd, logfileobj, logcatfileobj, kpifileobj)
        super(AdbShellReader, self).__init__(wait_cmd, logfileobj, kpifileobj)
        self._logfile = logfileobj

    def start_sub_proc(self):
        self._sub_proc = subprocess.Popen(self.adb_cmd,
                                          stdin=subprocess.PIPE,
                                          stdout=subprocess.PIPE)

    def _read_once(self):
        c = b''
        if not self.is_process_running():
            with self._sub_proc_lock:
                # terminate process
                if self._sub_proc:
                    self._sub_proc.terminate()
                    self._sub_proc = None
                # wait for device and respawn
                if self.wait_for_device():
                    self.start_sub_proc()
                else:
                    return c
        c = self._sub_proc.stdout.read(1)
        return c

    def write(self, data):
        with self._sub_proc_lock:
            output = self._sub_proc.stdin.write(data)
            self._sub_proc.stdin.flush()
        return output

    def close(self):
        super(AdbShellReader, self).close()
        if self.is_process_running():
            self._sub_proc.terminate()
        self._sub_proc = None


class AdbLogcatReader(ProcBufferedReader):

    # def __init__(self, adb_cmd, wait_cmd, logfileobj=None, logcatfileobj=None, kpifileobj=None):
    def __init__(self, adb_cmd, wait_cmd, logfileobj=None, kpifileobj=None, kpi_dict=None):
        self.adb_cmd = adb_cmd
        # super(AdbLogcatReader, self).__init__(wait_cmd, logfileobj, logcatfileobj, kpifileobj)
        super(AdbLogcatReader, self).__init__(wait_cmd, logfileobj, kpifileobj)
        self.read_logcat = ""
        self._logfile = logfileobj
        # self._logcatfile = logcatfileobj

        if pytest.kpi_enable:
            self.kpi = KpiAnalyze(for_framework=True, kpifileobj=kpifileobj)
            # self._kpifile = kpifileobj
            # self._kpi_index = {}  # 用于记录kpi的log内容和出现时间
            # # kpi分析参数
            # self._kpi_name = ""  # kpi的xml文件名称（信息保存在config中）
            # self._id_dict = {}  # kpi分析用于记录需要获取的log内容的ID
            # self._res_dict = {}  # kpi分析用于存储计算结果的名称
            # self._id_list_keys = []  # kpi分析用于记录log内容的所有ID
            # self._id_list_key_max = ""
            # self.store_enable = False
            # self._kpi_name = pytest.kpi_config.get("kpi_debug")["name"]  # 获取需要分析的kpi名称
            # if self._kpi_name + "_config_id" in pytest.kpi_config:
            #     # 若存在相应的分析内容的json数据，则将其存入_id_dict中
            #     self._id_dict = pytest.kpi_config.get(self._kpi_name + "_config_id")
            #
            #     # get the last key in dictionary
            #     for key in self._id_dict.keys():
            #         self._id_list_keys.append(key)
            #     self._id_list_key_max = self._id_list_keys[-1]
            # if self._kpi_name + "_config_result" in pytest.kpi_config:
            #     # 若存在相应的分析内容的json数据，则将其存入_res_dict中
            #     self._res_dict = pytest.kpi_config.get(self._kpi_name + "_config_result")
            # self._kpi_dict = kpi_dict

    def start_sub_proc(self):
        self._sub_proc = subprocess.Popen(self.adb_cmd,
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.STDOUT)
        fcntl.fcntl(
            self._sub_proc.stdout.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)

    def _read_once(self):
        out = b''
        if not self.is_process_running():
            with self._sub_proc_lock:
                # terminate process
                if self._sub_proc:
                    self._sub_proc.terminate()
                    self._sub_proc = None
                # wait for device and respawn
                if self.wait_for_device():
                    self.start_sub_proc()
                else:
                    return out
        try:
            output = self._sub_proc.stdout.readline()
            out = output if output else b''
        except IOError:
            pass
        if self._logfile:
            log = AATSADBTarget._bytes_to_escaped_unicode(out).replace('\\r', '\r').replace('\\n', '\n').replace('\\t',
                                                                                                                 '\t')
            self._logfile.write(log)
            if ("stress" not in pytest.target.get("prj")) and (pytest.target.get("prj") != "ddr"):
                self._read_buffer.put(log)
            if pytest.target.get("prj") == "ott_hybrid_switch_audio_track_stress" or pytest.target.get("prj") == "ott_hybrid_switch_subtitle_track_stress":
                self._read_buffer.put(log)
        if pytest.kpi_enable:
            #  对每条输出的log结果，实时进入kpi分析
            self.kpi.kpi_analysis(out)
        return out

    def close(self):
        if pytest.kpi_enable:
            # 抓取log的线程关闭前，对已经获取的log进行时间计算
            self.kpi.kpi_calculate()
            # logging.info(pytest.config)

        super(AdbLogcatReader, self).close()
        if self.is_process_running():
            self._sub_proc.terminate()
        self._sub_proc = None


class AATSADBTarget(AATSTarget):
    """
    AATS Target for devices accessible over ADB
    """
    RE_IP_ADDR = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d+)?$")
    PROTOCOL = 'adb'
    _adbpath = None
    _write_ready = Event()

    AATS_CMD_MISSING = 'is not a valid command'

    DATA_FS = "/data"

    @classmethod
    def _check_rc(cls, rc, message=None):
        # Checks return code and raises if non-zero.
        if rc:
            raise ADBRuntimeError(message)

    @classmethod
    def _find_adb(cls):
        # Tries to find the path to adb.  If adb is not in PATH then get
        # it from the build image's bin directory.
        if cls._adbpath:
            return cls._adbpath
        try:
            cmd = ['which', 'adb']
            adbpath = os.path.abspath(subprocess.check_output(cmd)
                                      .decode('utf-8', errors='ignore').strip())
        except subprocess.CalledProcessError:
            # Get adb from build image bin directory
            # and let's try to be cross platform...
            filepath = os.path.dirname(os.path.abspath(__file__))
            system = platform.system().lower()
            if system in ['linux', 'darwin']:
                path_comps = [filepath, '..', 'bin', system, 'adb']
            elif system == 'windows':
                # NOTE: Should we support windows?
                path_comps = [filepath, '..', 'bin', 'win', 'adb.exe']
            else:
                raise RuntimeError("Not a supported platform: %s" % system)
            adbpath = os.path.abspath(os.path.join(*path_comps))
            if not os.path.isfile(adbpath):
                raise RuntimeError("Unable to find adb, is it in PATH?")
        cls._adbpath = adbpath
        return adbpath

    @classmethod
    def _run_adb_cmd(cls, cmd, adbpath=None, timeout=0, verbose=True):
        # Run adb command.
        adbpath = adbpath or cls._find_adb()
        cmd = [adbpath] + cmd
        rc = 1
        output = b''

        log.debug("<<<%s>>>", cmd)
        with set_timer(timeout):
            try:
                output = subprocess.check_output(cmd).strip()
                rc = 0
            except subprocess.CalledProcessError as e:
                output = e.output
                rc = e.returncode
            if verbose:
                log.debug("(%s){{{%s}}}", rc, output)
            return rc, output

    @classmethod
    def _get_adb_device_list(cls, adbpath=None, timeout=0):
        # Get a list of device names from adb
        cmd = ['devices']
        rc, output = cls._run_adb_cmd(cmd, adbpath=adbpath, timeout=timeout)
        if rc:
            log.error("unable to get device list")
            return []
        # NOTE: skip first line in output from adb devices
        return [x.split()[0].decode('utf-8', errors='ignore') for x in output.splitlines()[1:]]

    @classmethod
    def _get_target(cls, device_id, adbpath=None, timeout=0):
        target = cls(device_id=device_id, adbpath=adbpath)
        return target

    @classmethod
    def _get_targets(cls, device_ids, adbpath=None, timeout=0):
        targets = cls(device_id=device_ids, adbpath=adbpath)
        return targets

    @classmethod
    def get_target(cls, device_id, adbpath=None, timeout=10):
        """
        Retruns a single instance of an AATS enabled ADB device or None.
        """

        # Don't instantiate if device is not in adb devices list.
        def clock_handle(signum, frame):  # 收到信号 SIGALRM 后的回调函数，第一个参数是信号的数字，第二个参数是the interrupted stack frame.
            # signal.alarm(1)
            raise RuntimeError("You did not select any device")

        temp = 3
        if '.' in device_id:
            logging.info('Connect over network')
            from lib.common.system.SerialPort import SerialPort
            serial_port = SerialPort()
            serial_port.write("su")
            serial_port.write("stop adbd")
            serial_port.write("start adbd")
            while temp > 0:
                # subprocess.run('adb disconnect', shell=True, check=False)
                # subprocess.run('adb kill-server', shell=True, check=False)
                subprocess.run(f'adb connect {device_id}', shell=True, check=False)
                if device_id not in cls._get_adb_device_list(adbpath=adbpath, timeout=timeout):
                    logging.debug('Try to connect again ')
                    logging.debug(temp)
                    temp -= 1
                else:
                    logging.debug(cls._get_adb_device_list(adbpath=adbpath, timeout=timeout))
                    break
        devices = cls._get_adb_device_list(adbpath=adbpath, timeout=timeout)
        # if len(devices) > 1:
        #     logging.info('Devices list as below')
        #
        #     for i in range(len(devices)):
        #         logging.info(f'No.{int(i) + 1} : {devices[i]}')
        #     signal.signal(signal.SIGALRM, clock_handle)  # 设置信号和回调函数
        #     signal.alarm(10)  # 设置 num 秒的闹钟
        #     input('pls input No number\n')
        #     signal.alarm(0)  # 关闭闹钟
        #     return cls._get_target(devices[i], adbpath=adbpath, timeout=timeout)
        if '.' in device_id and ':5555' not in device_id:
            device_id += ':5555'
        if device_id not in devices:
            return
        return cls._get_target(device_id, adbpath=adbpath, timeout=timeout)

    @classmethod
    def get_targets(cls, adbpath=None):
        """
        Get list of AATSADBTarget devices
        """
        targets = []
        device_list = []
        try:
            for device_id in cls._get_adb_device_list(adbpath=adbpath, timeout=10):
                if device_id in pytest.multi_instance[0].split(','):
                    device_list.append(device_id)
                    try:
                        target = cls._get_target(device_id, adbpath=adbpath, timeout=10)
                        if target:
                            targets.append(target)
                    except RuntimeError as e:
                        log.debug(str(e))
                else:
                    pass
        except Exception as e:
            # Print warning if something goes wrong with listing devices,
            # e.g. if adb is not installed at PATH.
            log.warning("Unable to list adb devices: %s" % e.message)
        logging.debug(f"targets is {targets}")
        logging.debug(f"device_list is {device_list}")
        return targets
        # return cls._get_targets(device_list, adbpath=adbpath)

    def __init__(self, device_id, adbpath=None, lib_path=None, **kwargs):
        super(AATSADBTarget, self).__init__(self.PROTOCOL, **kwargs)
        """
        :param device_id: the device id of the adb device to connect to
        :param adbpath: the path to ADB on this system
        :param libpath: a path on the device such as /data/lib to set LD_LIBRARY_PATH to
        """
        self._device_output = b''
        self._adb_id = device_id  # could be an IP address
        # if path to adb not provided, assume it's in the system PATH
        self.adbpath = adbpath or self._find_adb()
        self._open = False
        self._read_thread = None
        self._device_output = b''
        self._device_output_lock = Lock()
        self._lib_path = lib_path
        self._adbshell_reader = None
        self._adblogcat_reader = None
        # self._adblog_catcher = None
        self.open()
        self.get_device_id()  # get real device device_id.
        self.reset_flags()
        #self.wait_for_bootcomplete()
        # self.get_platform()  # retrieve platform information early
        self.kpi_dict = {}
        self.su_device()
        self.version = kwargs.values()
        # log.info(f"self.version: {self.version}")

    def su_device(self):
        os.system(f'adb -s {self._adb_id} root')
        # os.system(f'adb -s {self._adb_id} disable-verity')
        # os.system(f'adb -s {self._adb_id} remount')
        # os.system(f'adb -s {self._adb_id} push {os.getcwd()}/tools/device_check /system/bin')

    def _run_adb_cmd_specific_device(self, cmd, timeout=0, verbose=True):
        """runs adb command specific to a device"""
        cmd = ['-s', self._adb_id] + cmd
        return self._run_adb_cmd(cmd, adbpath=self.adbpath, timeout=timeout, verbose=verbose)

    def __write_data_to_log_file(self, data):
        """writes data to log file if exists"""
        try:
            if self._output_f_obj is not None:
                self._output_f_obj.write(self._bytes_to_escaped_unicode(data)
                                         .replace('\\r', '\r')
                                         .replace('\\n', '\n')
                                         .replace('\\t', '\t'))
                self._output_f_obj.flush()
        except Exception as exp:
            logging.debug("data not written to log file")
            logging.exception(exp)

    def getprop(self, key, timeout=0):
        """
        Get property from device.
        """
        rc, output = self.shell('getprop %s' % key, timeout=timeout)
        self._check_rc(rc, 'can not getprop: %s' % key)
        return output

    def get_device_id(self):
        if not self.device_id:
            # If ADB device is an emulator or on IP, then device_id needs
            # to be taken from getprop.
            if self.RE_IP_ADDR.match(self._adb_id) or \
                    self._adb_id.startswith('emu'):
                # self.device_id = self.getprop('ro.serialno')
                self.device_id = self._adb_id
            else:
                self.device_id = self._adb_id
        return self.device_id

    def root(self, timeout=0):
        cmd = ['root']
        rc, output = self._run_adb_cmd_specific_device(cmd, timeout=timeout)
        self._check_rc(rc, "unable to set root")

    def reboot(self, bootloader=False, timeout=0,
               waitboot=True, waitboottimeout=120):
        cmd = ['reboot']
        if bootloader:
            cmd.append('bootloader')
        restart_aats_proc = waitboot and not bootloader
        if restart_aats_proc:
            self._stop_adb_shell_reader()
        self.stop_log_collect()
        self.reset_flags()
        rc, _ = self._run_adb_cmd_specific_device(cmd, timeout=timeout)
        self._check_rc(rc, "unable to reboot device")
        start_time = time.time()
        log.info("Waiting for device bootup")
        if '.' in self.device_id:
            while self.device_id not in str(subprocess.check_output('adb devices', shell=True, encoding='utf-8')):
                logging.info('Devices not exist')
                subprocess.check_output('adb connect {}'.format(self.device_id), shell=True, encoding='utf-8')
                time.sleep(3)
        self.wait_for_device(waitboottimeout)
        self._stats["boot_time"] = time.time() - start_time
        log.info("Device booted up")
        if restart_aats_proc:
            self._start_adb_shell_reader()
        self.start_log_collect()
        self.wait_for_bootcomplete()

    def standby(self, timeout=60):
        logging.debug("Standby device")
        self._stop_adb_shell_reader()
        if '.' in self.device_id:
            logging.debug("disconnect device")
            subprocess.check_output(f'adb disconnect {self.device_id}', shell=True, encoding='utf-8')
        log.info("Waiting for device bootup")
        if '.' in self.device_id:
            with set_timer(timeout):
                while self.device_id not in str(subprocess.check_output('adb devices', shell=True, encoding='utf-8')):
                    logging.info('device not found')
                    subprocess.check_output('adb connect {}'.format(self.device_id), shell=True, encoding='utf-8')
                    time.sleep(3)
        start_time = time.time()
        self.wait_for_device(timeout)
        self._stats["boot_time"] = time.time() - start_time
        log.info("Device booted up")
        self._start_adb_shell_reader()
        self.start_log_collect()
        self.wait_for_bootcomplete()

    def wait_for_bootcomplete(self, timeout=300):
        logging.info("Waiting for bootcomplete")
        self.wait_for_device()
        # count = 0
        # # while not self.shell('getprop sys.boot_completed')[1] == '1':
        # while not str(self.getprop("sys.boot_completed")) == "1":
        #     count += 1
        #     time.sleep(1)
        #     if count > 30:
        #         raise AATSDeviceNotFoundError()
        end_time = time.time() + timeout
        while True:
            if '31' in self.getprop("ro.odm_dlkm.build.version.sdk"):
                boot_completed = True if str(self.getprop("sys.boot_completed")) == "1" else False
                if boot_completed:
                    logging.debug("Device bootcompleted.")
                    return True
            else:
                boot_completed = True if str(self.getprop("sys.boot_completed")) == "1" else False
                bootanim_completed = True if str(self.getprop("service.bootanim.exit")) == "1" else False
                if boot_completed and bootanim_completed:
                # if not self.oobe and not self._oobe_disabled:
                #     self.terminate_oobe(timeout=60)
                    logging.debug("Device bootcompleted.")
                    return True
            if time.time() > end_time:
                break
            time.sleep(1)
        logging.warning("The device did not bootcomplete.")
        return False

    # def reset_flags(self):
    #     self._oobe_disabled = False

    def wait_and_stop_service(self, service, timeout=60):
        print(service)
        end_time = time.time() + timeout
        prop = "init.svc.{}".format(service)
        self.wait_for_device()
        while True:
            status = str(self.getprop(prop))
            stopped = True if status == "stopped" else False
            running = True if status == "running" else False
            if stopped or running:
                logging.info("service {} running({}) stopped({})".format(
                    service, running, stopped))
                if running:
                    self.stop_service(service)

                logging.info("service {} stopped".format(service))
                return True
            if time.time() > end_time:
                break
            time.sleep(3)
        logging.warning("failed to wait-stop the service {}".format(service))
        return False

    # def terminate_oobe(self, timeout=0):
    #     logging.debug("Terminating oobe process")
    #     service_stopped = self.wait_and_stop_service("oobed_on_boot", timeout=timeout)
    #     if service_stopped:
    #         self._oobe_disabled = True
    #     return service_stopped

    # @connect_again
    def wait_for_device(self, timeout=300):
        cmd = ['wait-for-device']
        rc, _ = self._run_adb_cmd_specific_device(cmd, timeout=timeout)
        self._check_rc(rc, "wait_for_device failed")

    def shell(self, cmd, timeout=0, reduce_log_level=False):
        """
        Provides shell like interface to device

        Args:
            cmd (str) : command to send
            timeout (int, optional) : timeout value
            reduce_log_level (bool, optional) : not used for this protocol.

        Return:
            tuple (int, str) : return value, output data
        """
        self._write_cmd_to_file(cmd)

        # read to clear any output from before sending this command
        self._read()
        shell_cmd = ['shell', cmd]
        rc, output = self._run_adb_cmd_specific_device(shell_cmd,
                                                       timeout=timeout)
        self.__write_data_to_log_file(output)
        return rc, output.decode('utf-8', errors='ignore')

    def wait_for_process_completion(self, outfile, timeout=60):
        """The function is supposed to wait for process complete,
        as a short term solution, we using lsof in conjuction with background_shell
        and the output file generated by it.
        Checks output file for active writers every X seconds or until timeout.
        *Args*:
            * outfile : file background process is writing to

        *Optional Args*:
            * timeout   : max timeout before returning with rc=-1

        *Returns*:
            * Output : 0/-1       : success/timeout
        """
        PROCESS_CHECK_SLEEP_DURATION = 3
        cmd = "lsof {}".format(outfile)
        while timeout > 0:
            try:
                rc, output = self.shell(cmd)
                if output.count(outfile) < 2:
                    return 0
            except Exception as exp:
                logging.exception("Exp: {} while trying to execute '{}'".format(exp, cmd))
                return -1
            time.sleep(PROCESS_CHECK_SLEEP_DURATION)
            timeout -= PROCESS_CHECK_SLEEP_DURATION
        logging.info("Timeout reached waiting for {} to be released".format(outfile))
        return -1

    def get_file_content_from_device(self, file_name, delete_file=True):
        """checks if file exists on device, return content if exists
        and delete file
        *Args*:
            * file_name           : name of file
        *Optional Args*:
            * delete_file         : deletes file after reading
        *Returns*:
            * Output(tuple) : rc       : return code of shell command
                              output(str): output of file
        """
        TEST_RESULT_FOUND_STR = "Test_Result_File_Found"
        try:
            cmd = "test -f {} && echo {}".format(file_name,
                                                 TEST_RESULT_FOUND_STR)
            rc, output = self.shell(cmd.encode())
            if output.count(TEST_RESULT_FOUND_STR) < 1:
                logging.error("File does not exist: {}".format(file_name))
                return rc, output
        except Exception as exp:
            logging.exception("Exp: {} while trying to find '{}'".format(exp, file_name))
            return rc, output

        try:
            rc, output = self.shell("cat {}".format(file_name))
            if delete_file:
                self.shell("rm {}".format(file_name))
            return rc, output
        except Exception as exp:
            logging.exception("Exp: {} while trying to read '{}'".format(exp, file_name))
        return rc, output

    def background_shell(self, cmd):
        """sends specified shell command to device to launch
        as background process and redirects output to output_file
        *Args*:set_keyword
            * cmd           : command to send to device (str or list of str)

        *Returns*:
            * Output(tuple) : rc       : rc of shell command
                              output(str): output filepath
        """
        output_file = os.path.join(self.DATA_FS, str(time.time()) + str(random.Random().getrandbits(128)))
        cmd = cmd + " >> " + output_file + " 2>&1 " + " &"
        cmd = cmd.encode()

        try:
            # attempt to remove file
            self.shell("rm {}".format(output_file))
        except Exception as exp:
            logging.warning("Exp: {} while trying to remove '{}'".format(exp, output_file))

        try:
            # Execute command
            rc, output = self.shell(cmd)
            logging.info("Remote command rc={} output={}".format(rc, output))
        except Exception as exp:
            logging.exception("Exp: {} while running `{cmd}`".format(exp, cmd))
            return rc, output
        return rc, output_file

    def send_cmd_read_until_pattern(self, cmd, pattern, timeout=0,
                                    reduce_log_level=False):
        """sends command to device using the timeout specified
        and looks for specified pattern in output.

        Args:
            cmd (str) : command to send
            pattern (bytes) : bytestring or regex pattern to look for
            timeout (int, optional) : timeout value in seconds
            reduce_log_level (bool, optional) : not used for this protocol.

        Returns:
            Tuple output representing read results:
            (0/-1/-2  : success/failure/exception,
             match    : re.compile search object or None,
             output   : read data)
        """
        try:

            rc, output = self.shell(cmd=cmd, timeout=timeout,
                                    reduce_log_level=reduce_log_level)
            output = output.encode('utf-8', errors='ignore')
            log.debug("looking for pattern: {}".format(pattern))
            pattern = re.compile(pattern)
            match = pattern.search(output)
            if match:
                return 0, match, output
            return -1, match, output
        except Exception as exp:
            log.error(exp)
            return -2, None, b''

    def send_cmd_read_syslog_until_pattern(self, cmd, pattern, timeout=0,
                                           reduce_log_level=False):
        """sends command to device using the timeout specified
        and looks for specified pattern in system logs.

        Args:
            cmd (str): Command to send
            pattern (bytes): bytestring or regex pattern to look for
            timeout (int, optional): timeout value in seconds
            reduce_log_level (bool, optional) : not used for this protocol.

        Returns:
            Tuple output representing read results:
            (0/-1/-2: success/failure/exception,
             match    : re.compile search object or None,
             output   : read data)
        """
        try:
            rc, output = self.shell(cmd=cmd, timeout=timeout,
                                    reduce_log_level=reduce_log_level)
            return self.read_syslog_until_pattern(pattern, timeout)
        except Exception as exp:
            log.error(exp)
            return -2, None, b''

    def read_syslog_until_pattern(self, pattern, timeout=0):
        """Keep reading on system log until a string pattern found

        Monitor current system log until a string pattern found or timeout
        reached. The function will return and drain buffered log content.

        Args:
            pattern: A regex in bytes array
            timeout: timeout in seconds if pattern not found yet

        Returns:
            A tuple representing the read-and-find result:

            (ret_code, match, output)
            ret_code:
                0: reading logs successfully, match shows whether pattern
                   found within timeout.
                -1: error reading logs
                -2: Unexcepted return due to exceptions
            match:
               None: when ret_code is 0, it means nothing found before timeout
               Otherwise it means a pattern found in log
            output:
               All captured from the system log during the function call
        """
        try:
            match = None
            output = b''
            sleep_interval = 0.05

            if self._adblogcat_reader is None:
                log.error("Can't read on adb logcat")
                return -1, None, output

            logging.debug("reading syslog for: {}".format(pattern))
            patobj = re.compile(pattern)
            end_time = time.time() + timeout
            while True:
                if self._adblogcat_reader is None:
                    log.info("logcat closed")
                    return -1, None, output

                data = self._adblogcat_reader.read()
                if data:
                    output += data
                    match = patobj.search(data)
                    if match:
                        return 0, match, output

                if timeout < sleep_interval:
                    return 0, None, output

                if time.time() > end_time:
                    return 0, None, output
                time.sleep(sleep_interval)

        except Exception as exp:
            log.exception('Unknown exception: {}'.format(exp))
            return -2, match, output

    def read_until_pattern(self, pattern, timeout=0):
        """reads data from device until specified pattern

        Args:
            pattern: string or regex pattern to look for
            timeout: timeout value in seconds

        Returns:
            Tuple output representing read results:
            (0/-1/-2  : success/failure/exception,
             match    : re.compile search object or None,
             output   : read data)
        """
        return self.read_syslog_until_pattern(pattern, timeout)

    def _start_adb_shell_reader(self):
        shellreader_cmd = [self.adbpath, '-s',
                           self._adb_id, 'shell', '-x']
        wait_cmd = [self.adbpath, '-s',
                    self._adb_id, 'wait-for-device']

        self._adbshell_reader = AdbShellReader(shellreader_cmd,
                                               wait_cmd,
                                               None)
        self._write_ready.set()

    def _stop_adb_shell_reader(self):
        self._write_ready.clear()
        self._adbshell_reader.close()

    def open(self):
        """
        Opens the device and starts consuming its output
        """
        if self._open:
            raise IOError("Device already open")

        if self._adbshell_reader:
            raise AATSRuntimeError("Unexpected att rpc proc")

        self._start_adb_shell_reader()

        self._open = True

        self._start_read_loop()
        self.start_log_collect()

    def close(self):
        """
        Releases handle on device so it can be used by other processes
        """
        log.info("Closing ATTADBTarget")
        if not self._open:
            raise IOError("Device already closed")
        self._open = False
        # don't join because the process stdout is blocking
        # self._read_thread.join()
        self._stop_adb_shell_reader()

        # stop log collection
        self.stop_log_collect()

        # check final result for kpi
        if pytest.kpi_enable:
            self.kpi_check()

        # write logcat file
        # self.write_anr_log()

        # write dmesg
        # self.write_dmesg()

        # write tombstone file
        # self.write_tombstone()

    def _read_from_device(self):
        """
        Reads from ADB process
        """
        content = self._adbshell_reader.read()

        if content != b'':
            log.debug("<<< %s" % content)
            content = content.replace(b'\r\n', b'\n')
        return content

    def _write(self, data):
        if (sys.version_info[0] < 3 and isinstance(data, basestring)) or \
                ((sys.version_info[0] >= 3) and isinstance(data, str)):
            data = data.encode()

        while self._open and not self._write_ready.wait(20):
            log.debug("Wait for device ready to write")

        log.debug("Writing to device[%s] >>> %s" %
                  (self._adb_id, self._bytes_to_escaped_unicode(data)))
        self.__write_data_to_log_file(data)
        rtn = self._adbshell_reader.write(data)
        return rtn

    def run_device_tests(self, cmd, timeout=30, privileged=False):
        rc, output = self.shell(cmd, timeout)
        if self.AATS_CMD_MISSING in output:
            raise CLIEndpointNotAvailableError("'{}' not found".format(cmd))
        return rc, output.encode('utf-8')

    def start_log_collect(self):
        if self._adblogcat_reader:
            log.warning("Log collection already started")
            return

        if self._log_file_obj is None:
            log.warning("log file object is None")
            return

        if pytest.kpi_enable and self._kpi_file_obj is None:
            log.warning("kpi file object is None")
            return

        # if self._adblog_catcher:
        # log.warning("Log catcher already started")
        # return

        # if self._logcat_file_obj is None:
        # log.warning("logcat file object is None")
        # return

        self.check_logfile_access()

        cmd = ['logcat', '-c']
        self._run_adb_cmd_specific_device(cmd)
        cmd = ['logcat', '-G', '40M']
        self._run_adb_cmd_specific_device(cmd)

        # -b option allows to choose buffers and 'all' is selected
        # to collect full logs from device which includes kmsg, dmesg

        logcat_cmd = [self.adbpath,
                      '-s',
                      self._adb_id,
                      'logcat',
                      '-b',
                      'all']

        wait_cmd = [self.adbpath, '-s',
                    self._adb_id, 'wait-for-device']

        self._adblogcat_reader = AdbLogcatReader(logcat_cmd, wait_cmd,
                                                 self._log_file_obj,
                                                 self._kpi_file_obj,
                                                 # self._logcat_file_obj,
                                                 self._kpi_dict,
                                                 )

    '''
    def write_anr_log(self):
        anr_error = False
        files = os.listdir(pytest.result_dir)
        anr_line = ''

        for i in range(len(files)):
            if ".syslog.txt" in files[i]:
                syslog = os.path.join(files[i])
                logcat = files[i].split(".")[0] + ".logcat.txt"
                if logcat in files:
                    sys_file = open(pytest.result_dir + '/' + syslog, 'r+')
                    cat_file = open(pytest.result_dir + '/' + logcat, 'r+')

                    for line in sys_file.readlines():
                        if "ANR " in line:
                            anr_line = line
                            logging.info("ANR found, Time: " + anr_line.split(" ")[0] + " " + anr_line.split(" ")[1])
                            anr_error = True
                    sys_file.seek(0)
                    for line in sys_file.readlines():
                        if line != anr_line:
                            cat_file.write(line)
                        else:
                            cat_file.write(line)
                            break
                    # logging.info(len(sys_file.readlines()), len(cat_file.readlines()))
                    logging.info(logcat + " wrote by " + syslog)
                if anr_error:
                    anr_error = False
                    os.system("adb pull sdcard/ " + pytest.result_dir)
                    # ADB.pull("data/anr/traces.txt", pytest.result_dir)
                    file = os.listdir(pytest.result_dir)
                    if "traces.txt" in file:
                        logging.info("traces.txt pulled")
                    else:
                        logging.info("traces.txt not found")

    def write_dmesg(self):
        panic = False
        result = os.popen('adb shell dmesg')
        context = result.read()
        with open(pytest.result_dir + "/dmesg.log.txt", mode='a', encoding='utf-8') as dmesg:
            for line in context:
                dmesg.write(line)
                if "kernel panic" in line.lower():
                    logging.info("Kernel panic found")
                    panic = True
        if panic:
            os.system("adb pull data/log/dontpanic " + pytest.result_dir)
            files = os.listdir(pytest.result_dir)
            if "apanic_console" in files and "apanic_threads" in files:
                logging.info("apanic files pulled")
            else:
                logging.info("apanic files not found")

    def write_tombstone(self):
        os.system("adb pull data/tombstones " + pytest.result_dir)
        files = os.listdir(pytest.result_dir)
        for i in range(len(files)):
            if "tombstone" in files[i]:
                logging.info("tombstone found")
    '''

    def stop_log_collect(self):
        if self._adblogcat_reader is None:
            log.warning("log collection not started")
            return

        self._adblogcat_reader.close()
        self._adblogcat_reader = None

    def kpi_check(self):
        kpi_ref_time = pytest.kpi_config.get("kpi_debug")["reference_time"]

        # save result to kpi_summary.txt
        test_name = pytest.result.get_name()
        # file_name = re.findall(r'(\w+)\[', test_name)
        # logging.debug(f'test_name:{test_name},file_name:{file_name}, file_name[0]:{file_name[0]} \n')
        kpi_summary_file = open(pytest.result_dir + '/' + test_name + '_summary.txt', "w")
        kpi_summary_file.write("====kpi_each_total:\n")
        for key, value in self._kpi_dict.items():
            if key == "total":
                for item in value:
                    kpi_summary_file.write(key + "[" + str(value.index(item)) + "]:" + str(item) + "\n")

        kpi_summary_file.write("\n")
        kpi_summary_file.write("\n")
        kpi_summary_file.write("====kpi_summary:\n")
        for key, value in self._kpi_dict.items():
            try:
                avg = sum(value) / len(value)
                logging.debug(f'key:{key}, avg:{avg}, value:{value} \n')
                kpi_summary_file.write(key + ",count:" + str(len(value)) + ",avg:" + str(avg) + "\n")
                if key == "total" and (avg == 0 or avg > kpi_ref_time):
                    kpi_summary_file.write("\n")
                    kpi_summary_file.write("\n")
                    kpi_summary_file.write("====kpi_summary fails:\n")
                    kpi_summary_file.write("kpi_fail:" + str(1) + "\n")
                    logging.info(
                        f'[kpi_check]total avg:{avg} is bigger than kpi_ref_time:{kpi_ref_time}, kpi check fail!!!\n')
            except Exception as exp:
                kpi_summary_file.write("\n")
                kpi_summary_file.write("\n")
                kpi_summary_file.write("====kpi_summary fails:\n")
                kpi_summary_file.write("kpi_fail:" + str(2) + "\n")
                logging.info(
                    f'[kpi_check]Exception, kpi check fail!!!\n')

        kpi_summary_file.close()

    def start_service(self, name, cmd=None):
        # read to clear any output from before sending this command
        self._read()
        if not cmd:
            if isinstance(name, bytes):
                name = name.decode('utf-8', errors='ignore')
            cmd = ['start', name]
        else:
            if isinstance(cmd, bytes):
                cmd = cmd.decode('utf-8', errors='ignore')
            cmd = cmd.split()
        shell_cmd = ['shell'] + cmd
        rc, output = self._run_adb_cmd_specific_device(shell_cmd)
        self.__write_data_to_log_file(output)
        return rc, output.decode('utf-8', errors='ignore')

    def stop_service(self, name, cmd=None):
        # read to clear any output from before sending this command
        self._read()
        if not cmd:
            if isinstance(name, bytes):
                name = name.decode('utf-8', errors='ignore')
            cmd = ['stop', name]
        else:
            if isinstance(cmd, bytes):
                cmd = cmd.decode('utf-8', errors='ignore')
            cmd = cmd.split()
        shell_cmd = ['shell'] + cmd
        rc, output = self._run_adb_cmd_specific_device(shell_cmd)
        self.__write_data_to_log_file(output)
        return rc, output.decode('utf-8', errors='ignore')
