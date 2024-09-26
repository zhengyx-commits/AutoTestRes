#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/4/28 09:28
# @Author  : chao.li
# @Site    :
# @File    : MemEater.py
# @Software: PyCharm

import fcntl
import logging
import os
import re
import threading
from collections import defaultdict
from time import sleep

import xlwt

from lib.common.system.ADB import ADB


class MemEater(ADB):
    '''
    memmory eater test lib

    Attributes:
        TINY_MIX_COMMAND : tinymix command
        VOLUME_COMMAND : media volume command

    '''
    DUMP_MEMINFO_COMMAND = 'dumpsys -t 60 meminfo'
    CAT_MENINFO_COMMAND = 'cat /proc/meminfo'
    CAT_PAGETRACE_COMMAND = 'cat /proc/pagetrace'
    CAT_SLAB_COMMAND = 'cat /proc/slabinfo'
    EAT_SH_PATH = '/data/eater.sh'
    TARGET_PROCESS = 'com.bestv.ott.baseservices'
    LAUNCHER_BY_SCRIPT_FILE = 'launcher_by_script.log'
    TEMP_TXT = 'temp.txt'

    def __init__(self):
        super(MemEater, self).__init__()
        self.eat_mem_info = f'{self.logdir}/eat_memory_info.log'
        self.launcher, self.stress, self.count = '', '', 0

    def setup(self):
        '''
        test set up
        1. install apk
        2. push eater sh
        3. chmod eater sh
        @return: None
        '''
        self.install_eater()
        # self.push(f'{os.curdir}/multimediaplayer/res/sh/eater.sh', '/data/')
        self.push(self.res_manager.get_target('sh/eater.sh'), '/data/')
        self.run_shell_cmd('chmod a+x /data/eater.sh')

    def eat_memory(self):
        '''
        eat memory
        @return: None
        '''
        logging.info('Start increased pressure')
        self.popen('shell nohup sh %s &' % self.EAT_SH_PATH)

    def get_mem_info(self):
        '''
        catch meminfo , write into /result/eat_memory_info.log
        @return: None
        '''
        while True:
            with open(self.eat_mem_info, 'a') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                mem = self.run_shell_cmd(self.DUMP_MEMINFO_COMMAND)[1].strip()
                if mem:
                    f.write('Dump meminfo:\n')
                    f.write(mem)
                    f.write('\n')
                    f.write('Cat meminfo:\n')
                    f.write(self.run_shell_cmd(self.CAT_MENINFO_COMMAND)[1].strip())
                    f.write("\n")
                    f.write('Cat pagetrace:\n')
                    f.write(self.run_shell_cmd(self.CAT_PAGETRACE_COMMAND)[1])
                    f.write("\n")
                    f.write('Cat slabinfo:\n')
                    f.write(self.run_shell_cmd(self.CAT_SLAB_COMMAND)[1])
                    f.write("\n")
                    sleep(3)

    def run(self):
        '''
        run thread catch info
        @return: thread : threading.Thread
        '''
        t = threading.Thread(target=self.get_mem_info, name='MemEater')
        t.setDaemon(True)
        t.start()
        return t

    def get_process_mem(self):
        '''
        handle eat_memory_info data
        :return:
        '''
        logging.info('In process')
        log = ''
        total_title = 'Total PSS by process:'
        with open(self.eat_mem_info, 'r') as f:
            log_list = f.read().split(total_title)
        with open(self.TEMP_TXT, 'w') as f:
            for info in log_list[1:]:
                info = total_title + info
                try:
                    process_info = re.search(r'(Total PSS by process:.*?).*Total PSS by OOM adjustment:', info,
                                             re.S).group(0)
                    process_info = re.sub(r'\(.*?\)', '', process_info)
                    memory_status = re.search(r'(MemTotal:.*kB)\nCat pagetrace', info, re.S).group(1)
                except AttributeError:
                    continue
                f.write(process_info)
                f.write('\n\n')
                f.write(memory_status)
                f.write('\n\n')
        with open(self.TEMP_TXT, 'r') as f:
            log = f.read()
        memory_unit = re.split(total_title, log)[1:]
        for i in range(len(memory_unit)):
            if self.TARGET_PROCESS not in memory_unit[i]:
                if self.TARGET_PROCESS in memory_unit[i - 1]:
                    self.launcher += 'Total PSS by process:'
                    self.launcher += memory_unit[i - 1].replace('MemTotal:', '\nMemTotal:')
                    self.count += 1
        logging.info('Launcher被kill次数：{}'.format(self.count))
        self.launcher = self.launcher.replace('Total PSS by OOM adjustment:\n\n', '')
        with open(self.LAUNCHER_BY_SCRIPT_FILE, 'w') as f:
            f.write(self.launcher)

    def get_average(self):
        '''
        calculate average
        @return: average result : dict
        '''
        memDict = defaultdict(list)
        with open(self.LAUNCHER_BY_SCRIPT_FILE, 'r') as f:
            for i in f.readlines():
                if 'K:' in i:  # handle K: char
                    tempValue1 = re.search(r'(.*?)K:', i).group(1).strip().replace(',', '')
                    tempKey = i.split(':')[1].strip()
                elif 'kB' in i:  # handle kB char
                    tempValue1 = re.search(r':(.*?) kB', i).group(1).strip().replace(',', '')
                    tempKey = i.split(':')[0].strip()
                else:
                    raise ValueError('Dirty data')
                if tempKey in memDict:
                    memDict[tempKey].append(int(tempValue1))
            for key in memDict.keys():  # calculate average
                memDict[key] = int(sum(memDict[key]) / len(memDict[key]))
            memDict = sorted(memDict.items(), key=lambda x: x[1], reverse=True)
            return memDict

    def output_excel(self, info):
        '''
        data write into excel Meminfo.xls
        @param info: data
        @return: None
        '''
        wb = xlwt.Workbook(encoding='ascii')
        ws = wb.add_sheet('Meminfo')
        for i in range(len(info)):
            ws.write(i, 0, info[i][0])
            ws.write(i, 1, info[i][1])
        wb.save(f'{self.logdir}/Meminfo.xls')

    def install_eater(self):
        '''
        check if recovery.sh exists
        :return: None
        '''
        self.root()
        if 'com.amazon.stress' in ''.join(self.popen('shell ls /data/app').stdout.readlines()):
            logging.info('已安装')
            return
        # self.popen(f'install {os.curdir}/multimediaplayer/res/apk/PFXStress.apk')
        self.popen(f"install {self.res_manager.get_target('apk/PFXStress.apk')}")
        while True:
            if 'com.amazon.stress' in ''.join(self.popen('ls /data/app').stdout.readlines()):
                logging.info('安装成功')
                break

    def clean(self):
        '''
        clean temp file , temo.txt and launcher_by_script.log
        @return:
        '''
        if os.path.exists(self.TEMP_TXT):
            os.remove(self.TEMP_TXT)
        if os.path.exists(self.LAUNCHER_BY_SCRIPT_FILE):
            os.remove(self.LAUNCHER_BY_SCRIPT_FILE)
