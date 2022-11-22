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
import os
import re
import regex
import signal
import time
import logging
import pytest
import codecs
from abc import ABCMeta, abstractmethod
from contextlib import contextmanager
from threading import Thread
from ..exceptions import AATSTimeoutException
from future.utils import with_metaclass

log = logging.getLogger(__name__)


@contextmanager
def set_timer(timeout, handler=None):
    # NOTE: signals only work in the main thread, so set_timer only works
    # in the main thread
    def _sig_handler(signum, frame):
        # Signal handler for handling signals during operations.
        if signum == signal.SIGALRM:
            raise AATSTimeoutException("operation timed out")

    if timeout:
        log.debug('in timer with timeout of %s seconds', timeout)
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


def _bytes_repr(c):
    """py2: bytes, py3: int"""
    if not isinstance(c, int):
        c = ord(c)
    return '\\x{:x}'.format(c)


def _text_repr(c):
    d = ord(c)
    if d >= 0x10000:
        return '\\U{:08x}'.format(d)
    else:
        return '\\u{:04x}'.format(d)


def backslashreplace_backport(ex):
    s, start, end = ex.object, ex.start, ex.end
    c_repr = _bytes_repr if isinstance(ex, UnicodeDecodeError) else _text_repr
    return ''.join(c_repr(c) for c in s[start:end]), end


codecs.register_error('backslashreplace_backport', backslashreplace_backport)


class AATSTarget(with_metaclass(ABCMeta, object)):
    """
    Base class for AATS target communicators. This class contains the AATS logic
    for composing requests to the target and interpretting the response. The
    acceptable variant of descendants will implement the specifics of communicating over a given
    protocol (ADB, serial)
    """

    _ESCAPE_BINARY_IN_OUTPUT = True
    TIMEOUT = 5
    _AATS_DEVICE_CHECK_CLI_CMD = b'\ndevice_check\n'

    RE_AATS_TARGET_INFO = re.compile(br'dutplatform:(\w+)')

    # Error and warning signatures
    SIGNS = {
        "error": [b"Stack Corruption",
                  b"Heap Corruption",
                  b"Stack Overflow"],
        "warning": [b"Malloc Failure",
                    b"NULL pointer",  # Following signs are borrowed from crash lib
                    b"Divide by zero",
                    b"Mem Manage Exception",
                    b"SW Assertion",
                    b"avc:.*denied"]}  # SELinux policy check

    DEVICE_TARGET_RTOS = 'rtos'
    DEVICE_TARGET_LINUX = 'linux'
    DEVICE_TARGET_NOART = 'noart'

    def __init__(self, protocol, output_f_obj=None, timeout=TIMEOUT,
                 escape_binary=_ESCAPE_BINARY_IN_OUTPUT, **kwargs):
        """
        :param protocol: eg. adb, serial
        :param output_f_obj: if provided, a file-like object to stream stdout
            and stderr from the device
        :param escape_binary: if True, escapes the non-printable characters
            read from the stdout and stderr output from the device when writing
            to the output_f_obj
        """
        self.device_id = None
        self.protocol = protocol
        self.timeout = timeout
        self.pid = os.getpid()
        self.tag = type(self).__name__
        self._output_f_obj = output_f_obj
        self._log_file_obj = None
        self._cmd_file_obj = None
        self._kpi_file_obj = None
        self._kpi_dict = {}
        # self._logcat_file_obj = None
        # error checker index
        self.__check_err_index = 0
        # statistics information
        self._stats = dict()
        # target device platform
        self.platform = None
        self.escape_binary = escape_binary
        self.version = kwargs.values()
        # self.oobe = True

    def __enter__(self):
        return self

    def __del__(self):
        if self._open:
            self.close()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._open:
            self.close()

    def get_platform(self):
        """
        Returns target platform collected using "device_check" command
        """
        if not self.platform:
            _, match, output = self.send_cmd_read_until_pattern(
                self._AATS_DEVICE_CHECK_CLI_CMD, self.RE_AATS_TARGET_INFO, timeout=10)
            if match:
                target = match.group(1).decode("utf-8", errors="ignore")
                log.debug("target platform: %s", target)
                self.platform = target
        return self.platform

    def set_timeout(self, timeout):
        """
        Sets the file-like obj as the destination to write output of
        communication with device
        """
        self.timeout = timeout

    def set_output_file(self, output_f_obj):
        """
        Sets the file-like obj as the destination to write output of
        communication with device
        """
        self._output_f_obj = output_f_obj

    def _start_read_loop(self):
        self._read_thread = Thread(target=self._read_loop,name='read_loop')
        self._read_thread.daemon = True
        self._read_thread.start()

    def _check_err_index_reset(self):
        """Resets the err signrature index to zero
           Note: This needs to be done by the function which flushes
                 device_output buffer.
        """
        self.__check_err_index = 0

    def __check_err_signatures(self, buffer=None, skip=None):
        """
        Checks for early error or warning signatures from
        the device logs
        """
        if not buffer:
            return
        for key in self.SIGNS.keys():
            for data in buffer.splitlines()[self.__check_err_index:]:
                for sign in self.SIGNS.get(key):
                    # Captures case insensitive fuzzy matching of sign in data
                    # with error cost < 3
                    match = regex.search(b"(?i)(?:%s){e<3}" % sign, data)
                    if match:
                        if hasattr(pytest, 'crash') and pytest.crash.is_under_use:
                            pytest.result.log_warn("{}: {} detected when crash lib in use.\n \
                                                Refer device log in result directory \
                                                (*.txt for RTOS device, otherwise *.log)".format(key, data))
                        else:
                            if key == "warning":
                                pytest.result.log_warn("{}: {} detected as warning.\n \
                                                Refer device log in result directory \
                                                (*.txt for RTOS device, otherwise *.log)".format(key, data))
                            else:
                                pytest.fail("{}: {} detected.\n \
                                                Refer device log in result directory \
                                                (*.txt for RTOS device, otherwise *.log)".format(key, data))

        self.__check_err_index = len(buffer.splitlines()) - 1

    @classmethod
    def _bytes_to_escaped_unicode(cls, bytes_str):
        """
        Converts a bytes object to a unicode string with non-printables escaped
        """
        if isinstance(bytes_str, bytes):
            return bytes_str.decode('utf-8', 'backslashreplace_backport') \
                .encode('unicode_escape').decode('utf-8', errors='ignore')
        else:
            return bytes_str.encode('unicode_escape').decode('utf-8', errors='ignore')

    def _read_loop(self):
        """
        Intended as the target of a thread. Reads one byte at a time from
        device in a loop until self._open is false
        """
        while self._open:
            data = self._read_from_device()
            if data == b'':
                time.sleep(0.05)
                continue
            try:
                if self._output_f_obj is not None:
                    self._output_f_obj.write(self._bytes_to_escaped_unicode(data)
                                             .replace('\\r', '\r')
                                             .replace('\\n', '\n')
                                             .replace('\\t', '\t')
                                             if self.escape_binary else data)
                    self._output_f_obj.flush()
            except Exception as exp:
                log.debug("data not written to log file")
                log.exception(exp)
            with self._device_output_lock:
                self._device_output += data
                self.__check_err_signatures(buffer=self._device_output)

    def _read(self):
        """
        Returns device output buffer and clears buffer
        """
        with self._device_output_lock:
            rtn = self._device_output
            self._device_output = b''
        if rtn != b'':
            log.debug("device output: <<<%s>>>" %
                      self._bytes_to_escaped_unicode(rtn)
                      .replace('\\r', '\r')
                      .replace('\\n', '\n')
                      .replace('\\t', '\t'))
        return rtn

    @abstractmethod
    def _write(self):
        """
        Write to device
        """
        pass

    def get_device_id(self):
        """
        Returns the target's true serial number
        """
        return self.device_id

    def root(self, timeout=0):
        """
        Set privileged access to target
        """
        pass

    def reboot(self, bootloader=False, timeout=0):
        """
        Reboots target.
        Raises exception if reboot command not sent successfully
        """
        self.wait_for_bootcomplete()
        return False

    def standby(self, timeout=60):
        """
        Standby device.
        """
        pass

    def wait_for_device(self, timeout=0):
        """
        Blocks waiting for device to become available.
        """
        pass

    def wait_and_stop_service(self, service, timeout=60):
        """
        Wait service starts and then stop it.
        This is to stop service started late during boot.
        """
        log.info("skip stopping service {}".format(service))
        return True

    def wait_for_bootcomplete(self, timeout=150):
        """
        Blocks waiting for device to boot.
        Waits for two consecutive 0.5second of no change in buffer to determine bootcomplete.
        """
        log.debug("Waiting for bootcomplete")
        try:
            is_idle_state = []
            last_output_buffer = self._device_output
            with set_timer(timeout):
                while True:
                    current_output_buffer = self._device_output
                    if current_output_buffer == last_output_buffer:
                        is_idle_state.append(True)
                        if len(is_idle_state) >= 2:
                            logging.debug("Device bootcompleted.")
                            return True
                    else:
                        is_idle_state.clear()
                    last_output_buffer = current_output_buffer
                    time.sleep(0.5)
        except Exception as e:
            log.debug("Failed to bootcomplete within {}s. error={}".format(timeout, e))
        logging.warning("The device did not bootcomplete.")
        return False

    # def terminate_oobe(self, timeout=60):
    #     """
    #     Terminate oobe process that is currently running.
    #     """
    #     return True
    #
    # def disable_oobe(self):
    #     """
    #     Disable oobe from current session and subsequent reboots
    #     """
    #     self.oobe = False
    #     self.wait_for_bootcomplete()

    def reset_flags(self):
        """
        Flags to initialize on device and on reboot
        """
        pass

    def shell(self, cmd, timeout=0, reduce_log_level=False):
        """
        Performs a shell-like command
        """
        return 0, b''

    def run_device_tests(self, cmd, timeout=10, privileged=False):
        """
        Executes the device tests on the target.
        :param cmd: test execution command
        :param timeout: default timeout before the command exits
        :param privileged: run device tests with privileged permission
        :return: rc, output
        :raises
                NotImplementedError - If the target has not implemented this
                CLIEndpointNotAvailableError - when the requested cmd is not
                    exposed in the device target
        """
        raise NotImplementedError()

    def read_until_string(self, string, timeout=0.1):
        """
        Reads from device until pattern is matched and returns output
        captured until that point.
        :param string: string to look for in output
        :param timeout: time to read output before giving up
        """
        output = b''
        log.debug('reading until %s', string)
        try:
            with set_timer(timeout):
                while True:
                    new_output = self._read()
                    # only check at most n-1 characters of previously searched
                    # output
                    if string in output[-len(string) - 1:] + new_output:
                        return output + new_output
                    output += new_output
                    time.sleep(0.1)
        except AATSTimeoutException:
            log.debug("Failed to find '{}' in output={}".format(string, output))
            raise
        return output

    def _write_cmd_to_file(self, cmd):
        if self._cmd_file_obj:
            content = cmd
            suffix_cmd = ""
            # if self.get_platform() == self.DEVICE_TARGET_RTOS:
            #     suffix_cmd = self._AATS_CLI_CMD
            if isinstance(content, bytes):
                content = content.decode('utf-8', errors='ignore')
            if isinstance(suffix_cmd, bytes):
                suffix_cmd = suffix_cmd.decode('utf-8', errors='ignore')
            suffix_cmd = [i for i in suffix_cmd.splitlines() if i]  # remove empty strings
            content_list = content.splitlines()
            if content_list[-1] in suffix_cmd:
                content_list = content_list[:-1]
            content = "\n".join(content_list)
            if isinstance(content, bytes):
                content = content.decode('utf-8', errors='ignore')
            logging.debug("#: {}".format(content))
            self._cmd_file_obj.write(content + "\n")
            self._cmd_file_obj.flush()

    def check_logfile_access(self):
        """Checks log file access permissions"""
        LOG_WRITE_CHECK = ""
        try:
            if self._output_f_obj:
                self._output_f_obj.write(LOG_WRITE_CHECK)
            if self._log_file_obj:
                self._log_file_obj.write(LOG_WRITE_CHECK)
            if self._cmd_file_obj:
                self._cmd_file_obj.write(LOG_WRITE_CHECK)
            if self._kpi_file_obj and pytest.kpi_enable:
                self._kpi_file_obj.write(LOG_WRITE_CHECK)
            # if self._logcat_file_obj:
            #     self._logcat_file_obj.write(LOG_WRITE_CHECK)
        except Exception as exp:
            raise Exception("Cannot use logfile(s): access/permission err: {}".format(exp))

    def start_log_collect(self):
        self.check_logfile_access()

    def stop_log_collect(self):
        pass

    def login_to_device(self, *args, **kwargs):
        pass

    def getprop(self, *args, **kwargs):
        raise NotImplementedError()

    def start_service(self, *args, **kwargs):
        pass

    def stop_service(self, *args, **kwargs):
        pass

    @property
    def stats(self):
        return self._stats
