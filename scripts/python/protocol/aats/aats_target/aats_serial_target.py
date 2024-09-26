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
import re
import time
from threading import Lock
from threading import Thread
import pytest

from . import AATSTarget, set_timer
from ..exceptions import AATSTimeoutException

log = logging.getLogger(__name__)

PERMISSION_DENIED_ERRNO = 13

_serial_imported = False


def _import_serial():
    """
    Import pyserial, but only if attempting to get serial targets
    """
    global _serial_imported, list_ports, Serial, SerialException
    if _serial_imported:
        return
    try:
        from serial.tools import list_ports
        from serial import Serial, SerialException
        _serial_imported = True
    except ImportError:
        log.error("Error: Couldn't import python module 'serial', " +
                  "please pip install pyserial")
        raise


class AATSSerialTarget(AATSTarget):
    """
    AATS target for Linux devices accessible over serial
    """
    BAUDRATE = 115200
    TIMEOUT = 1  # timeout reads after 1 second
    PROTOCOL = 'serial'
    LINE_FEED = b'\n'
    CLI_LONG_TIMEOUT = 120
    _AATS_BOOT_DEVICE_CHECK_CLI_CMD = b'\ncat /proc/version\n'

    CMD_REBOOT_DEVICE = b'reboot'
    CMD_BOOTLOADER_REBOOT_DEVICE = b'reset'
    CMD_CAT_PROC_VERSION = b'cat /proc/version'

    # message printed when reboot command executed
    REBOOT_MSG = b'Restarting system'
    # Time out for the reboot to complete or timedout
    REBOOT_TIMEOUT = 10

    # message printed when reset command executed
    RESET_MSG = b'resetting'
    # Time out for the reset to complete or timedout
    RESET_TIMEOUT = 10

    # message printed when cat command executed
    CAT_MSG = b'Unknown command'
    # Time out for the cat to complete or timedout
    CAT_TIMEOUT = 10

    LOGIN_PROMPT = b'audit: rate limit exceeded'
    BOOT_CHANGE = b'U-Boot'
    BOOT_PROMPT = b'#'
    TERMINATED = b'Terminated'
    REMOVE_ADDED_CRS = True
    DATA_FS = "/tmp"
    IFCONFIG = b'ifconfig'

    def __init__(self, port, baudrate=BAUDRATE, username="", password="", **kwargs):
        super(AATSSerialTarget, self).__init__(self.PROTOCOL, **kwargs)
        _import_serial()
        self.log_collection_in_progress = False
        self.session_id = None
        self._username = username
        self._password = password
        if isinstance(self._username, str):
            self._username = self._username.encode('utf-8')
        if isinstance(self._password, str):
            self._password = self._password.encode('utf-8')
        self._serial_device = None
        self._port = port
        self._baudrate = baudrate
        self._open = False
        self._boot = False
        self._read_thread = None
        self._device_output = b''
        self._device_output_lock = Lock()
        self._reconnect_lock = Lock()
        self._write_lock = Lock()
        self.last_read_char_was_newline = False
        self.open()
        self.wait_for_bootcomplete()
        # self.get_platform()  # retrieve platform information early

    @classmethod
    def _log_permission_denied(cls):
        log.error(
            """
            Received a permission denied error while trying to open device.
            Try adding yourself to the "dialout" and "plugdev" user groups with
            the following commands:
            $sudo adduser $USER plugdev
            $sudo adduser $USER dialout
            You must log out and back in for the changes to take effect.
            """)

    @classmethod
    def get_target(cls, port, baudrate=BAUDRATE, username="", password="", protocol_upgrade=False, timeout=10):
        """
        Returns an ATTSerialTarget wrapper around a serial device. Checks if
        the AATS cli is available.

        Args:
            port: serial port used to connect
            username: username to log in with
            password: password to log in with
            timeout: timeout value to wait on connecting
        """
        serial_target = None
        try:
            serial_target = cls(port, baudrate, username, password)
            # We may want to defer this check until RPC functionality is needed
            log.debug("get object.")
            serial_target.wait_for_device()
            # try:
            #     if protocol_upgrade:
            #         logging.debug("Attempting to upgrade protocol...")
            #         ip = serial_target.get_ip_address()
            #         if ip:
            #             username = serial_target._username
            #             password = serial_target._password
            #             logging.debug("Checking SshTarget: {}@{}".format(username, ip))
            #             ssh_target = ATTSshTarget.get_target(host=ip, username=username, password=password)
            #             if ssh_target:
            #                 ssh_target.wait_for_device()
            #                 serial_target.close()
            #                 ssh_target.log_collection_in_progress = False
            #                 ssh_target.start_log_collect()
            #                 ssh_target.wait_for_device()
            #                 logging.info("Successfully promoted to SshTarget: {}@{}".format(username, ip))
            #                 return ssh_target
            #             else:
            #                 logging.debug("Unable to connect to SshTarget: {}@{}".format(username, ip))
            #         else:
            #             logging.debug("Unable to find IP")
            # except Exception as e:
            #     log.warning("Failed to connect to ATTSshTarget. Please check ethernet is connected.")
            return serial_target
        except Exception as err:
            log.exception('Error opening target device: {}'.format(port))
            if isinstance(err, IOError) and \
                    err.errno == PERMISSION_DENIED_ERRNO:
                cls._log_permission_denied()
            if serial_target and serial_target._open:
                serial_target.close()
            raise

    @classmethod
    def follow_if_symlink(cls, path):
        """
        If the path is a symlink, resolve the symlink. Otherwise return
        the path
        """
        if not os.path.islink(path):
            return path

        target_path = os.readlink(path)
        if not os.path.isabs(target_path):
            target_path = os.path.join(os.path.dirname(path),
                                       target_path)
        return target_path

    def _reconnect_and_retry_if_fail(self, fn, timeout=120, retry_delay=.5):
        """
        Attempts to perform an action with the serial device. On failure will
        attempt to reconnect to the device and retry the command

        Args:
            fn: the function to try to execute against the serial device
            timeout: timeout in seconds
            retry_delay: retry delay in seconds

        Returns:
            Whatever fn returns

        Raises:
            ATTTimeoutException: Timedout run fn after trying to connect
                device
        """
        try:
            # Don't retry if serial has been closed explicitly
            if self._open:
                return fn()
        except SerialException:
            # another thread already has the lock?
            if not self._reconnect_lock.acquire(False):
                log.debug("another thread already attempting reconnect")
                # just to wait for the other thread to finish attempting
                # the reconnect
                with self._reconnect_lock:
                    pass
                return fn()

            self._open = False

            log.exception("Serial device connection error")
            log.info("Attempting to reconnect to device with a timeout "
                     "of %s seconds and a delay between retries of %s seconds",
                     timeout, retry_delay)
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    target_path = self.follow_if_symlink(self._port)
                    if self._serial_device:
                        self._serial_device.close()
                    self._serial_device = Serial(port=target_path,
                                                 baudrate=self._baudrate,
                                                 timeout=0.1,
                                                 exclusive=True)
                    self._open = True
                    # the first command sent seems to get included with some
                    # garbled input after reconnect, so flush out that
                    # input with a newline so the next command gets interpreted
                    self._serial_device.write(b'\n')
                    self._reconnect_lock.release()
                    log.info("successfully reconnected to device at: %s",
                             target_path)
                    log.info("retrying the call to device")
                    return fn()
                except SerialException:
                    time.sleep(retry_delay)

            self._reconnect_lock.release()
            raise pytest.errors.DeviceUnavailableError("Couldn't reconnect to device at '{}' "
                                                       "within timeout of {} seconds".format(self._port, timeout))

    def open(self):
        """
        Opens the device and starts consuming its output
        For serial devices, only one application can be reading/writing to the
        device at a time, so require that the device be opened/closed
        """
        if self._open:
            raise IOError("Device already open")
        if self._serial_device is None:
            port = self.follow_if_symlink(self._port)
            # from pyserial docs:
            # timeout = 0: non-blocking mode, return immediately in any case,
            # returning zero or more, up to the requested number of bytes
            # timeout = x: set timeout to x seconds (float allowed) returns immediately
            # when the requested number of bytes are available, otherwise wait until the
            # timeout expires and return all bytes that were received until then.
            # exclusive (bool) – Set exclusive access mode (POSIX only). A port cannot be
            # opened in exclusive access mode if it is already open in exclusive access mode.
            self._serial_device = Serial(port=port,
                                         baudrate=self._baudrate,
                                         timeout=0.1,
                                         exclusive=True)
        elif self._serial_device.is_open:
            log.debug(
                "AATSSerialTarget.open() called, but underlying "
                "serial device already opened")
        else:
            self._serial_device.open()

        self._open = True
        self._start_read_loop()

        self.wait_for_device()
        self.start_log_collect()

    def close(self):
        """
        Releases handle on device so it can be used by other processes
        """
        log.info("Closing AATSLinuxSerialTarget")
        if not self._open:
            raise IOError("Device already closed")
        self.stop_log_collect()
        self._open = False
        self._read_thread.join()

        # wait for write to complete
        if not self._write_lock.acquire():
            log.info("Waiting write lock timed out, closing anyway.")

        # flush the buffers
        if self._serial_device.is_open:
            self._serial_device.reset_input_buffer()
            self._serial_device.reset_output_buffer()
        # close the port
        self._serial_device.close()

    def get_device_id(self):
        return self.device_id

    def _read(self):
        """
        Returns device output buffer and clears buffer
        """
        with self._device_output_lock:
            rtn = self._device_output
            self._device_output = b''
            super()._check_err_index_reset()
        # RTOS implementation adds \n == \x0A after any \r == \x0D written out
        rtn = rtn.replace(b'\n\r', b'\n')
        rtn = rtn.replace(b'\r\n', b'\n')

        return rtn

    def _read_from_device(self):
        """
        Reads everything available from the attached serial device
        """

        def read():
            # log.info("read serial start")
            bytes_read = self._serial_device.read(1024)
            # log.info("read serial end")
            if self.REMOVE_ADDED_CRS:
                if (self.last_read_char_was_newline and
                        bytes_read[0:1] == b'\r'):
                    bytes_read = bytes_read[1:]

                bytes_read = bytes_read.replace(b'\n\r', b'\n')
                bytes_read = bytes_read.replace(b'\r\n', b'\n')
                # if last char read here is \n and the next is \r, remove the
                # \r. r[-1:] because indexing a bytes object returns an int in
                # py3 but a length 1 bytes string in py2
                self.last_read_char_was_newline = bytes_read[-1:] == b'\n'

            if bytes_read != b'':
                log.warning("<====={}".format(bytes_read))

            return bytes_read

        return self._reconnect_and_retry_if_fail(read, timeout=30, retry_delay=1)

    def _write(self, data):
        if self._output_f_obj:
            self._output_f_obj.write(self._bytes_to_escaped_unicode(data)
                                     .replace('\\r', '\r')
                                     .replace('\\n', '\n')
                                     .replace('\\t', '\t'))
            self._output_f_obj.flush()

        def write_fn():
            written = 0
            log.warning("=====>{}".format(data))

            with self._write_lock:
                written += self._serial_device.write(data)
                self._serial_device.flush()
                time.sleep(0.5)

            return written

        return self._reconnect_and_retry_if_fail(write_fn)

    def shell(self, cmd, timeout=30, reduce_log_level=False):
        """sends specified shell command to device.
        Waits for prompt until specified timeout
        Args:
            cmd (str) : command to send to device (str or list of str)
            timeout (int, optional) : timeout value in seconds
            reduce_log_level (bool, optional) :
                        True - will set device log level to Fatal
                        False - will not change device log level
        Returns:
            tuple : 0/-1: success/timeout, output(str): data read

        Raises:
            Exception if there is an internal error
        """
        if isinstance(cmd, list):
            cmd = ' '.join(cmd)
        if not isinstance(cmd, bytes):
            cmd = cmd.encode('utf-8', errors='ignore')
        if self._boot:
            cmd = cmd + self._AATS_BOOT_DEVICE_CHECK_CLI_CMD
            (rc, _, output) = self.send_cmd_read_until_pattern(
                cmd=cmd, pattern=self.CAT_MSG,
                timeout=timeout, reduce_log_level=reduce_log_level)
        else:
            cmd = cmd + self._AATS_DEVICE_CHECK_CLI_CMD
            (rc, _, output) = self.send_cmd_read_until_pattern(
                cmd=cmd, pattern=self.RE_AATS_TARGET_INFO,
                timeout=timeout, reduce_log_level=reduce_log_level)

        if rc == -2:
            raise Exception("shell command exception")
        elif rc == -1:
            logging.debug("shell command timedout")
        # please return rc value in future
        return 0, output.decode('utf-8', errors='ignore')

    def reboot(self, bootloader=False, timeout=None):
        """
        Reboots target and wait for terminal.
        """
        if timeout is None:
            timeout = self.REBOOT_TIMEOUT

        def write_reboot():
            self.stop_log_collect()
            self._write(
                self.CMD_REBOOT_DEVICE + self.LINE_FEED)

        def write_reset():
            self.stop_log_collect()
            self._write(
                self.CMD_BOOTLOADER_REBOOT_DEVICE + self.LINE_FEED)

        if self._boot:
            self._reconnect_and_retry_if_fail(write_reset)
            start_time = time.time()
            self.read_until_string(self.RESET_MSG, timeout=timeout)
        else:
            self._reconnect_and_retry_if_fail(write_reboot)
            start_time = time.time()
            self.read_until_string(self.REBOOT_MSG, timeout=timeout)

        self.read_until_string(self.LOGIN_PROMPT, timeout=90)
        self.wait_for_bootcomplete()
        self.wait_for_device(timeout=10)
        self._stats["boot_time"] = time.time() - start_time
        self.start_log_collect()
        self._boot = False

    def standby(self, timeout=60):
        pass

    def wait_for_device(self, timeout=60):
        """
        Waits for device terminal to be ready.
        """
        TERMINAL_TEST_CMD = b'echo "ping_wait_for_device"'
        TERMINAL_TEST_CMD_RESP = b'ping_wait_for_device'

        def check_bootstatus():
            self._read()

            self._write(self.CMD_CAT_PROC_VERSION + self.LINE_FEED)
            try:
                ret, match, output = self.read_until_pattern(self.CAT_MSG,
                                                             timeout=3)
                if match:
                    log.debug("set boot status")
                    self._boot = True
            except AATSTimeoutException:
                log.warning("Not a login screen.")

        def ping_device_terminal():
            # clear previous output if any
            self._read()

            self._write(b'\x03' + self.LINE_FEED)
            try:
                ret, match, output = self.read_until_pattern(self.LOGIN_PROMPT,
                                                             timeout=3)
                if match:
                    log.debug("Logging in")
                    self._login()
            except AATSTimeoutException:
                log.warning("Not a login screen.")

            # type Ctrl-C
            self._write(b'\x03' + self.LINE_FEED)
            self._write(TERMINAL_TEST_CMD + self.LINE_FEED)
            self.read_until_string(TERMINAL_TEST_CMD_RESP, timeout)

        self._reconnect_and_retry_if_fail(check_bootstatus, timeout=timeout)
        self._reconnect_and_retry_if_fail(ping_device_terminal, timeout=timeout)

    def get_hsinfo(self, emmc, timeout=30):
        '''
        获取hs 信息
        '''
        logging.info('Try to get hsinfo')
        if self._boot:
            return

        def write_reboot():
            for i in [emmc.TYPE_200, emmc.TYPE_400]:
                self._write(
                    self.CMD_REBOOT_DEVICE + self.LINE_FEED)
                ret, match, output = self.read_until_pattern(self.BOOT_CHANGE, timeout=3)
                if match:
                    ret, match, output = self.read_until_pattern(i, timeout=timeout)
                    if match:
                        emmc.type = match
                        emmc.result = 'Pass'
                        break
                    if ret == -1:
                        emmc.result = 'Fail'

        self._reconnect_and_retry_if_fail(write_reboot)
        self._boot = True

    def get_ip_address(self):
        '''
        获取ip地址
        :return:ip地址
        '''
        ip, ethoIp, wlanIp = '', '', ''
        logging.info('Getting ip info over serial')
        ipInfo = self._write(self.IFCONFIG + self.LINE_FEED)
        time.sleep(2)
        ipInfo = str(self._read())
        ipInfo = ipInfo.split('TX bytes:')
        if not ipInfo:
            logging.warning('no ip')
            return
        for i in ipInfo:
            if 'eth0' in i:
                ethoIp = re.findall(r'inet addr:(.*?)  Bcast', i, re.S)
            if 'wlan0' in i:
                wlanIp = re.findall(r'inet addr:(.*?)  Bcast', i, re.S)
        if ethoIp:
            ip = ethoIp[0]
        else:
            if wlanIp:
                ip = wlanIp[0]
            else:
                print('Devices no ip info')
        return str(ip)

    # def enter_uboot(self,key):
    #     '''
    #     进入uboot
    #     :return:
    #     '''
    #     self._write(self.CMD_REBOOT_DEVICE+self.LINE_FEED)
    #     self.send_cmd_read_until_pattern(b'\n')

    def get_launcher_timing(self, reboot, timeout=60):
        '''
        获取reboot 到桌面的时长
        '''

        if self._boot:
            return

        def write_reboot():
            start = time.time()
            # self._write(self.CMD_REBOOT_DEVICE + self.LINE_FEED)
            # # self.send_cmd_read_until_pattern(self.CMD_REBOOT_DEVICE, b'Starting kernel ...', timeout=timeout)
            # self.read_until_string(b'Starting kernel ...', timeout=60)
            self._write(
                self.CMD_REBOOT_DEVICE + self.LINE_FEED)
            ret, match, output = self.read_until_pattern(self.TERMINATED, timeout=3)
            if ret == -1:
                reboot.result = 'Fail'
                reboot.costTime = 'RunTimeError'
                return
            logging.info('reboot done')
            time.sleep(10)
            self._write(self.LINE_FEED)
            self._write(reboot.judgeLauncher + self.LINE_FEED)

            ret, match, output = self.read_until_pattern(reboot.signLauncherAble, timeout=timeout)
            if match:
                reboot.result = 'Pass'
                reboot.costTime = time.time() - start
            if ret == -1:
                reboot.result = 'Fail'
                reboot.costTime = 'RunTimeError'
            self._write(b'\x03' + self.LINE_FEED)

        logging.info('Try to get launcher info ')
        self._reconnect_and_retry_if_fail(write_reboot)
        self._boot = True

    def enter_bootloader(self, timeout=None):

        if self._boot:
            return

        if timeout is None:
            timeout = self.REBOOT_TIMEOUT

        def write_reboot():
            self._write(
                self.CMD_REBOOT_DEVICE + self.LINE_FEED)
            ret, match, output = self.read_until_pattern(self.BOOT_CHANGE, timeout=3)
            if match:
                self._write(b'\x03' + self.LINE_FEED)
                ret, match, output = self.read_until_pattern(self.BOOT_PROMPT, timeout=3)
                if match:
                    log.debug("Logging in bootloader")

        logging.info('Try to enter in uboot')
        self._reconnect_and_retry_if_fail(write_reboot)
        self._boot = True

    def echo_reset(self, timeout=None):
        if timeout is None:
            timeout = self.REBOOT_TIMEOUT
        logging.info('Try to enter in kernel')
        (rc, _, output) = self.send_cmd_read_until_pattern(self.CMD_BOOTLOADER_REBOOT_DEVICE, b'Starting kernel ...',
                                                           timeout=timeout)
        if rc == -2:
            raise Exception("shell command exception")
        elif rc == -1:
            logging.debug("shell command timedout")

    def read_until_pattern(self, pattern, timeout=0):
        """reads data from device until specified pattern

        Args:
            pattern: string or regex pattern to look for
            timeout: timeout value in seconds

        Returns:
            Tuple output representing read results:
            (0/-1/-2  : success/timeout/exception,
             match    : re.compile search object or None,
             output   : read data)
        """
        try:
            match = None
            output = b''
            log.debug("reading until pattern: '{}'".format(pattern))
            pattern = re.compile(pattern)
            # open port if not already opened
            if not self._open:
                self.open()
            end_time = time.time() + timeout
            while True:
                data = self._read()
                if data:
                    output += data
                    match = pattern.search(output)
                    if match:
                        return (0, match, output)
                if timeout > 0:
                    if time.time() > end_time:
                        return (-1, match, output)
                else:
                    return (-1, match, output)
                time.sleep(0.05)
        except Exception as exp:
            log.error("unexpected error: {}".format(exp))
            if self._open:
                self.close()
            return (-2, match, output)

    def send_cmd_read_until_pattern(self, cmd, pattern, timeout=0
                                    , reduce_log_level=False):
        """sends command to device and reads data until specified pattern

        Args:
            cmd    : string or bytes to send to the device
            pattern: string or regex pattern to look for
            timeout: timeout value in seconds
            reduce_log_level (bool, optional) :
                        True - will set device log level to Fatal
                        False - will not change device log level
        Returns:
            Tuple output representing read results:
            (0/-1/-2  : success/timeout/exception,
             match    : re.compile search object or None,
             output   : read data)
        """
        try:
            if reduce_log_level:
                # pytest.aats_log.set_logging_level("F")
                print("set_logging_level to F")
                pass
            if not isinstance(cmd, bytes):
                cmd = cmd.encode('utf-8')
            if not cmd.endswith(self.LINE_FEED):
                cmd += self.LINE_FEED
            self._write_cmd_to_file(cmd)
            # open port if not already opened
            if not self._open:
                self.open()
            log.debug("sending command: {}".format(cmd.rstrip(self.LINE_FEED)))

            def write_fn():
                # read to clear any output from before sending this command
                self._read()
                return self._serial_device.write(cmd)

            self._reconnect_and_retry_if_fail(write_fn)
            time.sleep(0.05)
            return self.read_until_pattern(pattern, timeout)
        except Exception as exp:
            log.error(exp)
            if self._open:
                self.close()
            return (-2, None, b'')
        finally:
            if reduce_log_level:
                # pytest.aats_log.set_logging_level("D")
                print("set_logging_level to D")
                pass

    def get_boot_status(self):
        return self._boot
