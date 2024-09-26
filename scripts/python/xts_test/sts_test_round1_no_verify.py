import re
import subprocess
import os
import signal
import paramiko
import time
from datetime import datetime

run_command = '/home/amlogic/Desktop/android-sts/tools/sts-tradefed run sts-dynamic-full -s ap2225c9589716052b3b8 --test-arg com.android.compatibility.common.tradefed.testtype.JarHostTest:set-option:android.security.sts.KernelLtsTest:acknowledge_kernel_update_requirement_warning_failure:true\n'
retry_command_regu = '/home/amlogic/Desktop/android-sts/tools/sts-tradefed run retry --retry {} -s ap2225c9589716052b3b8\n'

fail_list = []
last_fail_num = 0
MAX_RETRY = 2


def catch_logcat(pipe):
    global last_fail_num, fail_list
    while True:
        log = pipe.stdout.readline()
        if not log:
            continue
        print(log.strip())
        if 'FAILED            :' in log or 'PASSED            :' in log:
            print(log)
            num = int(log.strip()[-1])
            fail_list.append(num)
            last_fail_num = num
        if 'End of Results' in log:
            break
        pipe.terminate()
        os.kill(pipe.pid, signal.SIGTERM)


def count_last_result_num(log):
    last_session_info = re.findall(r"\n(\d+)\s+\d+\s+\d+", log)
    last_module_info = re.findall(r"\n\d+\s+\d+\s+\d+\s+(\d+)\sof\s(\d+)\s+", log)
    if last_module_info:
        last_module = last_module_info[-1]
        if all(module_num == "0" for module_num in last_module):
            raise Exception("Last loop failed,can't retry")
    if last_session_info:
        last_num = last_session_info[-1]
        print("Last session number:", last_num)
        if last_num.isdigit():
            return last_num
        else:
            raise Exception("Can't find last session number,can't retry")
    else:
        raise Exception("Can't find last session number,can't retry")


def get_last_failed(log):
    last_failed = re.findall(r"\n\d+\s+\d+\s+(\d+)\s+", log)
    last_module_info = re.findall(r"\n\d+\s+\d+\s+\d+\s+(\d+)\sof\s(\d+)\s+", log)
    if last_failed:
        last_module = last_module_info[-1]
        last_failed_num = int(last_failed[-1])
        if last_module[0] == last_module[1]:
            return last_failed_num
        else:
            if last_failed_num == 0:
                return -1
            else:
                return last_failed_num
    else:
        return -1

def run_remote_command(channel, command):
    """

    :type channel: object
    """
    global last_fail_num
    print(command)
    channel.send(command)
    while True:
        log = str(channel.recv(1024), 'utf-8', 'ignore').strip()
        print(log)
        if 'FAILED            :' in log or 'PASSED            :' in log:
            # num = int(re.findall(r'FAILED\s+:\s+([\d+])',log)[0])
            # fail_list.append(num)
            # last_fail_num = num 当FAILED与数字分开会报错
            return log


if __name__ == '__main__':
    # /home/amlogic/Desktop/XTS_TEST/T-XTS/android-cts/tools
    # os.system(run_command)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('127.0.0.1', 22, 'amlogic', 'Linux2017')
    channel = ssh.get_transport().open_session()
    channel.get_pty()
    channel.invoke_shell()
    run1 = run_remote_command(channel, run_command)
    time.sleep(300)
    channel.close()
    print('-' * 40)
    print('First loop done')
    print(time.strftime("%Y-%m-%d-%H_%M_%S", time.localtime()))  # retry
    count = 0
    while count < MAX_RETRY:
        channel = ssh.get_transport().open_session()
        channel.get_pty()
        channel.invoke_shell()
        print('-' * 40)
        print('Retry count ', '-' * 10, f'{count + 1}')
        print(time.strftime("%Y-%m-%d-%H_%M_%S", time.localtime()))
        result_info = subprocess.check_output('/home/amlogic/Desktop/android-sts/tools/sts-tradefed l r'.split(),
                                              encoding='utf-8')
        print(result_info)
        last_report_num = count_last_result_num(result_info)
        print(last_report_num)
        last_report_failed = get_last_failed(result_info)
        if last_report_failed == 0:
            print('Last Test has cleaned,exit Test!!!!!!!!')
            break
        else:
            retry = run_remote_command(channel, retry_command_regu.format(last_report_num))
        time.sleep(300)
        channel.close()
        count += 1
    ssh.close()
