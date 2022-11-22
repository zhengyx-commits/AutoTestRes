#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2021/9/7 13:36
# @Author  : chao.li
# @Site    :
# @File    : DutCheckMointor.py
# @Software: PyCharm


import codecs
import fcntl
import logging
import os
import signal
import subprocess
import threading
import time

import _io
import pytest
import threadpool

from lib.common.system.ADB import ADB
from lib.common.system.CPU import CPU
from lib.common.system.MemInfo import MemInfo


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


class DutCheckMointor():
    '''
    dut device status check mointor
    start check if instanced
    check point :
        cpu
        meminfo
        network ping
        logcat key pattern
    Attributes:
        KERNEL_CRASH_LOG_KEY : kernel log key pattern list
        LOGCAT_CRASH_KEY_LIST : logcat log key pattern list

        kernel_result : kernel crash catch result dict
        logcat_result : logcat crash catch result dict
        catch_thread : logcat catch thread
    '''
    KERNEL_CRASH_KEY_LIST = ['sysrq: SysRq : Trigger a crash', 'Kernel panic - not syncing:',
                            'PC is at dump_throttled_rt_tasks', 'boot reason: kernel_panic,sysrq']
    LOGCAT_CRASH_KEY_LIST = ['ANR', 'NullPointerException', 'CRASH', 'Force Closed', 'Exception']

    def __init__(self):
        self._init()
        self.kernel_result = {i: 0 for i in self.KERNEL_CRASH_KEY_LIST}
        self.logcat_result = {i: 0 for i in self.LOGCAT_CRASH_KEY_LIST}
        self.result_file = self.adb.logdir + '/log_analyze.txt'
        pytest.pool = threadpool.ThreadPool(3)
        status_func_list = ['self.cpu.catch()', 'self.meminfo.catch()', 'self.ping()']
        pytest.requests = threadpool.makeRequests(self.status_check, status_func_list)
        [pytest.pool.putRequest(req) for req in pytest.requests]
        self.catch_thread = threading.Thread(target=self.start_catch_logcat,
                                             name='catch logcat -b all')
        self.catch_thread.setDaemon(True)
        self.catch_thread.start()

    def _init(self):
        self.adb = ADB()
        self.cpu = CPU()
        self.meminfo = MemInfo()

    def ping(self):
        self.adb.ping()
        time.sleep(5)

    def status_check(self, func):
        '''
        catch check point if adb is alive
        @param func: check point
        @return: None
        '''
        while True:
            if self.adb.live:
                logging.debug('dut live , start catch')
                eval(func)
            else:
                logging.debug('dut not live , stop catch')

    def start_catch_logcat(self):
        '''
        start logcat and save to logcat_xxxx.log
        @return: None
        '''
        self.logcat_file = open(os.path.join(self.adb.logdir, f'logcat_{self.adb.serialnumber}.log'), 'w',
                                encoding='utf-8')
        logging.info('start to catch logcat -b all')
        self.log = subprocess.Popen(f'adb -s {self.adb.serialnumber} logcat -b all'.split(),
                                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, preexec_fn=os.setsid)
        fcntl.fcntl(self.log.stdout.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
        while True:
            if self.log:
                line = self.log.stdout.readline().decode('utf-8', 'backslashreplace_backport') \
                    .encode('unicode_escape') \
                    .decode('utf-8', errors='ignore') \
                    .replace('\\r', '\r') \
                    .replace('\\n', '\n') \
                    .replace('\\t', '\t')
                self.check_logcat(line, self.logcat_file)
                if not self.logcat_file.closed: self.logcat_file.write(line)

    def check_logcat(self, log, logcat_file):
        '''
        detection of one line of rows
        if catch crash key pattern write result to logcat_xxxx.log
        @param log: logcat
        @param logcat_file: logcat file
        @return: None
        '''
        # check kernel crash
        for i in self.KERNEL_CRASH_KEY_LIST:
            if i in log:
                self.kernel_result[i] += 1
                str = '\n' + '*' * 50 + '\n' \
                      + '*' + f'Crash time : {time.asctime()}'.center(48) + '*' + '\n' \
                      + '*' + f'kernel crash : {i}'.center(48) + '*' + '\n' \
                      + '*' * 50 + '\n'
                with open(self.result_file, 'a') as f:
                    f.write(str)
                    f.write(log)
                if not logcat_file.closed: logcat_file.write(str)
        # check logcat crash
        for i in self.LOGCAT_CRASH_KEY_LIST:
            if i in log:
                self.logcat_result[i] += 1
                str = '\n' + '*' * 50 + '\n' \
                      + '*' + f'Crash time : {time.asctime()}'.center(48) + '*' + '\n' \
                      + '*' + f'logcat exception : {i}'.center(48) + '*' + '\n' \
                      + '*' * 50 + '\n'
                with open(self.result_file, 'a') as f:
                    f.write(str)
                    f.write(log)
                if not logcat_file.closed: logcat_file.write(str)

    def stop_catch_logcat(self):
        '''
        stop logcat
        kill popen
        kill adb
        stop file context
        @return:
        '''
        os.system("killall logcat")
        if not isinstance(self.log, subprocess.Popen):
            logging.warning('pls pass in the popen object')
            return 'pls pass in the popen object'
        if not isinstance(self.logcat_file, _io.TextIOWrapper):
            logging.warning('pls pass in the stream object')
            return 'pls pass in the stream object'
        logging.info('stop to catch logcat -b all')
        self.log.terminate()
        self.log.wait()
        self.log = None
        self.logcat_file.close()
        with open(self.result_file, 'a') as f:
            f.write('\nLogcat Catch Summary\n')
            for i in self.kernel_result:
                f.write(f'{i} : {self.kernel_result[i]}\n')
            for i in self.logcat_result:
                f.write(f'{i} : {self.logcat_result[i]}\n')
