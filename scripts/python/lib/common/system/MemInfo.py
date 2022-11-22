#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/5/5 09:29
# @Author  : chao.li
# @Site    :
# @File    : coco.py
# @Software: PyCharm

import fcntl
import logging
import os
import re
import threading
import time
from collections import defaultdict

import numpy as np

from lib.common.system.ADB import ADB


class MemInfo(ADB):
    '''
    memory count test lib

    Attributes:
        DUMP_MEMINFO_COMMAND : dumpsys command
        CAT_MEMINFO_COMMAND : meminfo command
        CAT_PAGETRACE_COMMAND : pagetrace command
        FREE_COMMAND : free command

    '''

    DUMP_MEMINFO_COMMAND = 'dumpsys -t 60 meminfo'
    CAT_MEMINFO_COMMAND = 'cat /proc/meminfo'
    CAT_PAGETRACE_COMMAND = 'cat /proc/pagetrace'
    FREE_COMMAND = 'free -h'

    def __init__(self):
        super(MemInfo, self).__init__('Mem Info', unlock_code="", stayFocus=True)
        self.mem_info = f'{self.logdir}/memInfo.log'
        self.mem_info_res = f'{self.logdir}/memInfoRes.log'
        self.free_info = f'{self.logdir}/freeInfo.log'
        if os.path.exists(self.mem_info):
            os.remove(self.mem_info)
        if os.path.exists(self.free_info):
            os.remove(self.free_info)

    def run(self):
        '''
        start thread , catch info
        @return: None
        '''
        t = threading.Thread(target=self.get_mem_info, name='MemInfo')
        t.start()
        return t

    def get_mem_info(self):
        '''
        get memory info, pagetrace info, write to memInfo.log
        @return: None
        '''
        while True:
            with open(self.mem_info, 'a') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                mem = self.run_shell_cmd(self.DUMP_MEMINFO_COMMAND)[1].strip()
                if mem:
                    f.write(f'Time : {time.asctime()} \n')
                    f.write('Dump meminfo:\n')
                    f.write(mem)
                    f.write('\n')
                    f.write('Cat meminfo:\n')
                    f.write(self.run_shell_cmd(self.CAT_MEMINFO_COMMAND)[1].strip())
                    f.write("\n")
                    f.write('Cat pagetrace:\n')
                    f.write(self.run_shell_cmd(self.CAT_PAGETRACE_COMMAND)[1].strip())
                    f.write("\n")
                    time.sleep(1)

    def get_free_info(self):
        '''
        get free -h , write to freeInfo.log
        @return: data
        '''
        with open(self.free_info, 'a') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            free = self.run_shell_cmd(self.FREE_COMMAND)[1].strip()
            if free:
                f.write('Free info:\n')
                f.write(free)
                f.write("\n")
                time.sleep(1)
                logging.info("freeinfo is:")
                return free

    def format_num(self, num):
        '''
        re-format number xxxxxxxxx to xxx,xxx,xxx
        @param num: number
        @return: None
        '''
        num = str(num)
        result = ''
        count = 0
        for i in num[::-1]:
            count += 1
            result += i
            if count % 3 == 0:
                result += ','
        return result[::-1].strip(',')

    def sort_dict_by_value(self, dict_temp):
        '''
        the values of the dictionary are averaged and then sorted into dictionaries, arranged from largest to smallest
        :param dict_temp: dict data
        :return: result
        '''
        for key in dict_temp.keys():
            if len(dict_temp[key]) == 0:
                dict_temp[key] = 0
            else:
                dict_temp[key] = round(int(sum(dict_temp[key])) / len(dict_temp[key]), 2)
        return sorted(dict_temp.items(), key=lambda x: x[1], reverse=True)

    def generate_mem_average(self):
        '''
        handle meminfo data, get each process average value
        :return:
        '''
        logging.info('Processing meminfo data')
        split_list, split_process, split_oom, split_category, split_total, split_meminfo, split_pagetrace, avge_total = [], [], [], [], [], [], [], []
        avge_process, avge_category, avge_meminfo, avge_pagetrace = defaultdict(list), defaultdict(list), defaultdict(
            list), defaultdict(list)
        avge_oom = {'Native': [], 'System': [], 'Persistent': [], 'Persistent Service': [], 'Foreground': [],
                    'Visible': [], 'B Services': [], 'Cached': []}
        with open(self.mem_info) as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            temp = re.sub(r'\(pid.*?\)', '', f.read())  # remove pid number
            for i in temp.split('Dump meminfo:')[1:]:  # splite log
                split_list.append(i)
        for i in split_list:
            # group the data
            process = re.findall(r'Total PSS by process:(.*?)Total PSS by OOM adjustment:', i, re.S)[0]
            split_process.append(process)
            oom = re.findall(r'Total PSS by OOM adjustment:(.*?)Total PSS by category:', i, re.S)[0]
            split_oom.append(oom)
            category = re.findall(r'Total PSS by category:(.*?)Total RAM', i, re.S)[0]
            split_category.append(category)
            total = re.findall(r'(Total RAM:.*?)Cat meminfo:', i, re.S)[0]
            split_total.append(total)
            meminfo = re.findall(r'Cat meminfo:(.*?)Cat pagetrace:', i, re.S)[0]
            split_meminfo.append(meminfo)
            pagetrace = i.split('Cat pagetrace:')[1]
            split_pagetrace.append(pagetrace)
        # count average

        # count process average
        for i in split_process:
            for j in i.split('\n'):
                if j.strip():
                    value = j.split('K:')[0].replace(',', '').strip()
                    name = j.split('K:')[1].strip()
                    avge_process[name].append(int(value))
        avge_process = self.sort_dict_by_value(avge_process)

        # print('Process_Average: ', avge_process)

        # count oom average
        # avge_oom = {'Native': [], 'System': [], 'Persistent': [], 'Persistent Service': [], 'Foreground': [],
        #             'Visible': [], 'B Services': [], 'Cached': []}
        def add_oom_not_null(value, type):
            '''
            determine whether it is empty, not empty before adding to the method
            :param value: value
            :param type: type
            :return:
            '''
            if value:
                value = value[0].replace(',', '')
                avge_oom[type].append(int(value))

        for i in split_oom:
            # print(i)
            Native = re.findall(r'(\d*,\d+)K: Native', i, re.S)
            add_oom_not_null(Native, 'Native')
            System = re.findall(r'(\d*,\d+)K: System', i, re.S)
            add_oom_not_null(System, 'System')
            Persistent = re.findall(r'(\d*,\d+)K: Persistent', i, re.S)
            add_oom_not_null(Persistent, 'Persistent')
            Persistent_Service = re.findall(r'(\d*,\d+)K: Persistent Service', i, re.S)
            add_oom_not_null(Persistent_Service, 'Persistent Service')
            Foreground = re.findall(r'(\d*,\d+)K: Foreground', i, re.S)
            add_oom_not_null(Foreground, 'Foreground')
            Visible = re.findall(r'(\d*,\d+)K: Visible', i, re.S)
            add_oom_not_null(Visible, 'Visible')
            B_Services = re.findall(r'(\d*,\d+)K: B Services', i, re.S)
            add_oom_not_null(B_Services, 'B Services')
            Cached = re.findall(r'(\d*,\d+)K: Cached', i, re.S)
            add_oom_not_null(Cached, 'Cached')
        avge_oom = self.sort_dict_by_value(avge_oom)
        # print('OOM_Average: ', avge_oom)
        # count category average
        for i in split_category:
            for j in i.split('\n'):
                if j.strip():
                    value = j.split('K:')[0].replace(',', '').strip()
                    name = j.split('K:')[1].strip()
                    avge_category[name].append(int(value))
        avge_category = self.sort_dict_by_value(avge_category)

        # print('Category_Average: ', avge_category)
        # count total average
        def count_lost_rom_avge():
            temp_sum = 0
            for i in ram_list:
                i = i.replace(',', '').strip()
                if '-' in i:
                    temp_sum -= int(i[1:])
                else:
                    temp_sum += int(i)
            return int(temp_sum / len(ram_list))

        ram_list = []
        for i in split_total:
            value_list = re.findall(r'-?([\d*\,*]*\d+)', i, re.S)
            ram_temp = re.findall(r'Lost RAM:   (-?.*?)K', i, re.S)[0]
            ram_list.append(ram_temp)
            avge_total.append([int(i.replace(',', '')) for i in value_list])
        ram_avge = count_lost_rom_avge()
        avge_total = np.array(avge_total)  # change data into  np.array
        avge_total = [int(i) for i in avge_total.mean(axis=0)]  # avg each data
        avge_total[8] = ram_avge  # copy ram_avge
        avge_total = [self.format_num(i) for i in avge_total]
        total_temp = re.sub(r'([\d*\,*]*\d+)', '{}', split_total[0])  # get total info template
        avge_total = total_temp.format(*avge_total)  # re-format average value
        # print('Total_Average: \n', avge_total)
        # count meminfo average
        for i in split_meminfo:
            for j in i.split('\n'):
                if j.strip():
                    value = j.split(':')[1].replace('kB', '').strip()
                    name = j.split(':')[0].strip()
                    avge_meminfo[name].append(int(value))
        avge_meminfo = self.sort_dict_by_value(avge_meminfo)
        # print('Total_Meminfo: \n', avge_meminfo)
        # count pagetrace average
        for i in split_pagetrace:
            pagetrace_normall = i.split('count(KB)            kaddr, function')[1]
            pagetrace_high = i.split('count(KB)            kaddr, function')[2]
            normall_type = re.findall(r'type:(\w+)', pagetrace_normall, re.S | re.I)
            high_type = re.findall(r'type:(\w+)', pagetrace_high, re.S | re.I)
            for i in normall_type:
                value = re.findall(r',(.*?) kB, type:{}'.format(i), pagetrace_normall)[0].strip()
                avge_pagetrace['Normall' + i].append(int(value))
            for i in high_type:
                value = re.findall(r',(.*?) kB, type:{}'.format(i), pagetrace_high)[0].strip()
                avge_pagetrace['High' + i].append(int(value))
            normanaged = re.findall(r'managed:(.*?) KB', pagetrace_normall)[0].strip()
            norfree = re.findall(r'free:(.*?) kB', pagetrace_normall)[0].strip()
            norused = re.findall(r'used:(.*?) KB', pagetrace_normall)[0].strip()
            avge_pagetrace['Normallmanaged'].append(int(normanaged))
            avge_pagetrace['Normallfree'].append(int(norfree))
            avge_pagetrace['Normallused'].append(int(norused))
            highmanaged = re.findall(r'managed:(.*?) KB', pagetrace_high)[0].strip()
            highfree = re.findall(r'free:(.*?) kB', pagetrace_high)[0].strip()
            highused = re.findall(r'used:(.*?) KB', pagetrace_high)[0].strip()
            avge_pagetrace['Highmanaged'].append(int(highmanaged))
            avge_pagetrace['Highfree'].append(int(highfree))
            avge_pagetrace['Highused'].append(int(highused))
        avge_pagetrace = self.sort_dict_by_value(avge_pagetrace)

        def get_value(regu):
            return int(re.findall(regu, avge_total)[0].strip().replace(',', ''))

        def oom_get(key):
            for i in avge_oom:
                if key == i[0]:
                    return i[1]
            return 0

        # print('total', get_value(r'Total RAM:(.*?)K'))
        # print('used', get_value(r'\+   (.*?)K kernel'))
        # print('cached', get_value(r'\+   (.*?)K cached kernel'))
        # print('free', get_value(r'kernel \+   (.*?)K free'))
        # print('lost', get_value(r'Lost RAM:    -?(.*?)K'))
        # print('Native', oom_get('Native'))
        # print('System', oom_get('System'))
        # print('Persistent', oom_get('Persistent'))
        # print('Persistent Service', oom_get('Persistent Service'))
        total_temp = get_value(r'Total RAM:(.*?)K')
        used_temp = get_value(r'\+   (.*?)K kernel')
        cached_temp = get_value(r'\+   (.*?)K cached kernel')
        free_temp = get_value(r'kernel \+   (.*?)K free')
        lost_temp = get_value(r'Lost RAM:\s+-?(.*?)K')
        native_temp = oom_get('Native')
        system_temp = oom_get('System')
        persistent_temp = oom_get('Persistent')
        persistent_service_temp = oom_get('Persistent Service')
        foreground_temp = oom_get('Foreground')
        visible_temp = oom_get('Visible')
        perceptible_temp = oom_get('Perceptible')
        a_services_temp = oom_get('A Services')
        HeadRoom_Fore = total_temp - used_temp - cached_temp - free_temp - lost_temp - native_temp - system_temp - persistent_temp - persistent_service_temp
        HeadRoom_Back = HeadRoom_Fore - foreground_temp - visible_temp - perceptible_temp - a_services_temp
        logging.info(f"Fore: Total :{total_temp} - Kernel Used :{used_temp} "
                     f"- Kernel Cached :{cached_temp} - free :{free_temp} "
                     f"- Lost Ram :{lost_temp} - Native :{native_temp} - "
                     f"System :{system_temp} - Persistent :{persistent_temp} "
                     f"- Persistent Service: {persistent_service_temp} = {HeadRoom_Fore:.2f}")
        logging.info(f"Back: Headroom(Foreground) :{HeadRoom_Fore:.2f} "
                     f"- Foreground :{foreground_temp} - Visible :{visible_temp} "
                     f"- Perceptible :{perceptible_temp} - A Services :{a_services_temp} = {HeadRoom_Back:.2f}")
        # data write to memInfoRes.log
        with open(self.mem_info_res, 'w') as f:
            for i in [avge_process, avge_oom, avge_category, avge_meminfo, avge_pagetrace]:
                for key, value in i:
                    f.write('{:<50} : {} kb'.format(key, value))
                    f.write('\n')
                f.write('\n')
            f.write(avge_total)
            f.write('\n')
            f.write(f"Fore: Total :{total_temp} - Kernel Used :{used_temp} "
                    f"- Kernel Cached :{cached_temp} - free :{free_temp} "
                    f"- Lost Ram :{lost_temp} - Native :{native_temp} - "
                    f"System :{system_temp} - Persistent :{persistent_temp} "
                    f"- Persistent Service: {persistent_service_temp} = {HeadRoom_Fore:.2f}")
            f.write('\n')
            f.write(f"Back: Headroom(Foreground) :{HeadRoom_Fore} "
                    f"- Foreground :{foreground_temp} - Visible :{visible_temp} "
                    f"- Perceptible :{perceptible_temp} - A Services :{a_services_temp} = {HeadRoom_Back:.2f}")
