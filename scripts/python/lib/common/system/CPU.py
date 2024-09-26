import fcntl
from lib.common.system.ADB import ADB
import logging
import re
import threading
import time
import pygal

class CPU():
    '''
    cpu status check test lib

    Attributes:
        CPU_CUR_COMMAND : catch cpu current freq command
        CPU_MAX_COMMAND : catch cpu max freq command
        CPU_MIN_COMMAND : catch cpu min freq command
        CPU_ONLINE_COMMAND : catch cpu online count command
        CPU_TEMPERATURE_COMMAND : catch cpu temperature command
        CPU_WORK_MODE_COMMAND : catch cpu work mode command
        GPU_MAX_COMMAND : catch gpu max freq command
        GPU_CUR_COMMAND : catch gpu current freq command

        serialnumber : device number
        temperature_control : temperature control status
        error_count : error catch count
        all_count : all catch count
        path : cpu_info file path
        cpu_thermal : cpu thermal file path

    '''
    CPU_CUR_COMMAND = 'cat /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_cur_freq'
    CPU_MAX_COMMAND = 'cat /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq'
    CPU_MIN_COMMAND = 'cat /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_min_freq'
    CPU_ONLINE_COMMAND = 'cat /sys/devices/system/cpu/online'
    CPU_TEMPERATURE_COMMAND = 'cat /sys/class/thermal/thermal_zone0/temp'
    CPU_WORK_MODE_COMMAND = 'cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor'
    CPU_MODEL_COMMAND = 'cat /proc/cpuinfo'

    GPU_MAX_COMMAND = 'cat /sys/class/mpgpu/max_freq'
    GPU_CUR_COMMAND = 'cat /sys/class/mpgpu/cur_freq'

    def __init__(self, serialnumber='', logdir=''):
        self.adb = ADB()
        # super().__init__(serialnumber=serialnumber, name='CPU', logdir=logdir, stayFocus=True, unlock_code="")
        self.serialnumber = serialnumber
        self.temperature_control = self.adb.run_shell_cmd(self.CPU_TEMPERATURE_COMMAND.replace('temp', 'mode'))
        self.error_count = 0
        self.all_count = 0
        self.path = f'{self.adb.logdir}/cpu_info.log'
        self.cpu_thermal = f'{self.adb.logdir}/cpu_thermal.log'
        self.cpu_actual_thermal_dict = {}

    def run(self):
        '''
        run thread to catch cpu info
        @return: thread : threading.Thread
        '''
        t = threading.Thread(target=self.get_cpu_temp(), name='CpuInfo')
        t.setDaemon(True)
        t.start()
        return t

    def generateCPUChart(self):
        '''
        create cpu info char , need /result/cpu_info.log
        :return:
        '''
        logging.info('Generating charts')
        iow, cur_freq, max_freq, min_freq, gpu_max_freq, online, gpu_cur_freq, top, temperature, memfree = [], [], [], [], [], [], [], [], [], []
        tempTop = {
            '0-1': 2,
            '0-2': 3,
            '0-3': 4,
        }
        with open(self.path) as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            for i in f.read().split('-' * 20)[:-1]:
                i = i.strip()
                iow.append(int(re.findall(r'(\d+)%iow', i, re.S)[0]))
                cur_freq.append(int(re.findall(r'current_freq: (\d+)', i, re.S)[0]) / 10000)
                max_freq.append(int(re.findall(r'max_freq: (\d+)', i, re.S)[0]) / 10000)
                min_freq.append(int(re.findall(r'min_freq: (\d+)', i, re.S)[0]) / 10000)
                gpu_max_freq.append(int(re.findall(r'gpu_max_freq: (\d+)', i, re.S)[0]))
                gpu_cur_freq.append(int(re.findall(r'gpu_cur_freq: (\d+)', i, re.S)[0]))
                online.append(tempTop[re.findall(r'cpu_online: (\d-\d)', i, re.S)[0]])
                temperature.append(int(re.findall(r'cpu_temperature: (\d+)', i, re.S)[0]) / 1000)
                topTempInfo = re.findall(r'ARGS(.*?)current_freq', i, re.S)[0]
                topName = re.findall(r'\d:\d\d\.\d\d (.*?)\n', topTempInfo, re.S)
                topLoad = list(map(lambda x: round(float(x)), re.findall(r'[A-Z] +(\d+\.?\d*) ', topTempInfo, re.S)))
                infoDict = [{'name': topName[i], 'load': topLoad[i]} for i in range(len(topName))]
                top.append(infoDict)
                memfree.append(int(re.findall(r'(\d+)k free', i, re.S)[0]) / 1024)
        # add cpu info line chart
        line_chart = pygal.Line()
        line_chart.title = 'Cpu info (10k)'
        line_chart.x_labels = map(str, range(len(iow)))
        line_chart.add('cpu_cur', cur_freq)
        line_chart.add('cpu_max', max_freq)
        line_chart.add('cpu_min', min_freq)
        line_chart.add('cpu_online', online)
        line_chart.render_to_file(f'{self.adb.logdir}/Cpu info.svg')

        # add hw info lline chart
        line_chart1 = pygal.Line()
        line_chart1.title = 'HW info'
        line_chart1.add('gpu_max', gpu_max_freq)
        line_chart1.add('gpu_cur (K)', gpu_cur_freq)
        line_chart1.add('temperature (℃)', temperature)
        line_chart1.add('memfree (M)', memfree)
        line_chart1.add('iow (%)', iow)
        line_chart1.render_to_file(f'{self.adb.logdir}/HW info.svg')

        # add top task stack bar
        bar_chart = pygal.StackedBar()
        bar_chart.title = 'Process Top info (%)'
        bar_chart.x_labels = map(str, range(len(top)))
        bar_chart.add('', [{'value': i[0]['load'], 'label': i[0]['name']} for i in top])
        bar_chart.add('', [{'value': i[1]['load'], 'label': i[1]['name']} for i in top])
        bar_chart.add('', [{'value': i[2]['load'], 'label': i[2]['name']} for i in top])
        bar_chart.add('', [{'value': i[3]['load'], 'label': i[3]['name']} for i in top])
        bar_chart.add('', [{'value': i[4]['load'], 'label': i[4]['name']} for i in top])
        bar_chart.render_to_file(f'{self.adb.logdir}/Process Top info.svg')

    def catch_temperature(self, counter, actual_thermal):
        # TODO @chao.li : add function comments
        key = "第" + str(counter) + "次"
        self.cpu_actual_thermal_dict[key] = actual_thermal
        return self.cpu_actual_thermal_dict

    def write_to_file(self, actual_thermals):
        # TODO @chao.li : add function comments
        with open(self.cpu_thermal, "a+", encoding="utf-8") as f:
            f.write(str(actual_thermals) + "\n")

    def get_cpu_info(self):
        '''
        infinite loop catch cpu info
        top task info
        cpu work mode
        cpu current freq
        cpu max freq
        cpu min freq
        gpu max freq
        gpu current freq
        cpu online count
        cpu temperature info
        @return: None
        '''
        # if not self.adb.live
        with open(self.path, 'a') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            self.all_count += 1
            topInfo = self.adb.run_shell_cmd('top -n 1 -m 5')[1]
            if topInfo:
                f.write(f'Time : {time.asctime()} \n')
                f.write('Top info:\n')
                f.write(topInfo)
                f.write('\n')
                f.write('cpu_work_mode: ')
                f.write(self.adb.run_shell_cmd(self.CPU_WORK_MODE_COMMAND)[1].strip())
                f.write('\n')
                f.write('current_freq: ')
                f.write(self.adb.run_shell_cmd(self.CPU_CUR_COMMAND)[1].strip())
                f.write('\n')
                f.write('max_freq: ')
                f.write(self.adb.run_shell_cmd(self.CPU_MAX_COMMAND)[1].strip())
                f.write('\n')
                f.write('min_freq: ')
                f.write(self.adb.run_shell_cmd(self.CPU_MIN_COMMAND)[1].strip())
                f.write('\n')
                f.write('gpu_max_freq: ')
                f.write(self.adb.run_shell_cmd(self.GPU_MAX_COMMAND)[1].strip())
                f.write('\n')
                f.write('gpu_cur_freq: ')
                f.write(self.adb.run_shell_cmd(self.GPU_CUR_COMMAND)[1].strip())
                f.write('\n')
                f.write('cpu_online: ')
                f.write(self.adb.run_shell_cmd(self.CPU_ONLINE_COMMAND)[1].strip())
                f.write('\n')
                f.write('-' * 20 + '\n')
                time.sleep(1)

    def get_cpu_temp(self):
        with open(self.path, 'a') as f:
            f.write('cpu_temperature: ')
            f.write(self.adb.run_shell_cmd(self.CPU_TEMPERATURE_COMMAND)[1].strip())
            f.write('\n')
            f.write('-' * 20 + '\n')

