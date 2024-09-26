import time
import pytest
from lib.common.system.CPU import CPU
from lib import get_device
import logging
import fcntl

for g_conf_device_id in get_device():
    cpu = CPU(serialnumber=g_conf_device_id)
p_result_path = f'{pytest.result_dir}/../../cpu_gpu_info.log'


def test_get_cpu_info():
    with open(p_result_path, 'a') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        cpu.all_count += 1
        topInfo = cpu.run_shell_cmd('top -n 1 -m 5')[1]
        if topInfo:
            f.write(f'Time : {time.asctime()} \n')
            f.write('cpu&gpu info:\n')
            # f.write(topInfo)
            # f.write('\n')
            cpu_work_mode = cpu.run_shell_cmd(cpu.CPU_WORK_MODE_COMMAND)[1].strip()
            logging.info(f'cpu_work_mode : {cpu_work_mode}')
            f.write('cpu_work_mode: ')
            f.write(cpu_work_mode)
            f.write('\n')
            current_freq = cpu.run_shell_cmd(cpu.CPU_CUR_COMMAND)[1].strip()
            logging.info(f'current_freq : {current_freq}')
            f.write('cpu_current_freq: ')
            f.write(current_freq)
            f.write('\n')
            max_freq = cpu.run_shell_cmd(cpu.CPU_MAX_COMMAND)[1].strip()
            logging.info(f'cpu_max_freq : {max_freq}')
            f.write('cpu_max_freq: ')
            f.write(max_freq)
            f.write('\n')
            min_freq = cpu.run_shell_cmd(cpu.CPU_MIN_COMMAND)[1].strip()
            logging.info(f'cpu_min_freq: {min_freq} ')
            f.write('cpu_min_freq: ')
            f.write(min_freq)
            f.write('\n')
            gpu_max_freq = cpu.run_shell_cmd(cpu.GPU_MAX_COMMAND)[1].strip()
            logging.info(f'gpu_max_freq: {gpu_max_freq} ')
            f.write('gpu_max_freq: ')
            f.write(gpu_max_freq)
            f.write('\n')
            gpu_cur_freq = cpu.run_shell_cmd(cpu.GPU_CUR_COMMAND)[1].strip()
            logging.info(f'gpu_max_freq: {gpu_cur_freq} ')
            f.write('gpu_max_freq: ')
            f.write(gpu_cur_freq)
            f.write('\n')
            cpu_online = cpu.run_shell_cmd(cpu.CPU_ONLINE_COMMAND)[1].strip()
            logging.info(f'cpu_online: {cpu_online} ')
            f.write('cpu_online: ')
            f.write(cpu_online)
            f.write('\n')
            cpu_temperature = cpu.run_shell_cmd(cpu.CPU_TEMPERATURE_COMMAND)[1].strip()
            logging.info(f'cpu_temperature: {cpu_temperature} ')
            f.write('cpu_temperature: ')
            f.write(cpu_temperature)
            f.write('\n')
            f.write('-' * 20 + '\n')
            time.sleep(1)
        else:
            assert False
