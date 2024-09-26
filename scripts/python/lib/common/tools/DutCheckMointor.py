import codecs
import logging
import threading
import time
import pytest
import threadpool
import datetime
from lib.common.system.ADB import ADB
from lib.common.system.CPU import CPU
from lib.common.system.MemInfo import MemInfo
import paramiko
import os
import subprocess


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
    remote_dir = "/home/amlogic/FAE/AutoTest/OTT_BASIC"
    remote_host = "10.18.11.98"
    remote_username = "amlogic"
    remote_password = "Linux2023"

    def __init__(self):
        self._init()
        self._stop_event = threading.Event()
        self.kernel_result = {i: 0 for i in self.KERNEL_CRASH_KEY_LIST}
        self.logcat_result = {i: 0 for i in self.LOGCAT_CRASH_KEY_LIST}
        self.result_file = self.adb.logdir + '/log_analyze.txt'
        self.run_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        pytest.pool = threadpool.ThreadPool(3)
        status_func_list = ['self.cpu.get_cpu_temp()', 'self.cpu.get_cpu_info()', 'self.meminfo.get_free_info()', 'self.meminfo.get_mem_info()', 'self.ping()']
        pytest.requests = threadpool.makeRequests(self.status_check, status_func_list)
        [pytest.pool.putRequest(req) for req in pytest.requests]

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
        while not self._stop_event.is_set():
            if self.adb.live:
                logging.debug('dut live , start catch')
                eval(func)
            else:
                logging.debug('dut not live , stop catch')

    def catch_logcat(self):
        '''
        start logcat and save to logcat_xxxx.log
        @return: None
        '''
        if not pytest.device._log_file_obj:
            return
        with open(pytest.device._log_file_obj.name, 'r') as f:
            lines = f.readlines()
            for line in lines:
                self.check_logcat(line, self.result_file)
        if 'JENKINS_HOME' in os.environ or 'JENKINS_UPL' in os.environ or 'BUILD_ID' in os.environ:
        # if 1==1:
            self.capture_bug_report()
            self.catch_edid_info()
            if os.path.exists(self.result_file):
                local_file_path = [self.adb.logdir+"/cpu_info.log", self.adb.logdir+'/freeInfo.log', self.adb.logdir+"/memInfo.log", self.adb.logdir+"/bugreport.zip", self.adb.logdir+"/edid_info.log", self.result_file]
            else:
                local_file_path = [self.adb.logdir+"/cpu_info.log", self.adb.logdir+'/freeInfo.log', self.adb.logdir+"/memInfo.log", self.adb.logdir+"/bugreport.zip", self.adb.logdir+"/edid_info.log"]
            self.send_file_to_remote(local_file_path, self.remote_dir, self.remote_host, self.remote_username, self.remote_password)

    def capture_bug_report(self):
        try:
            result = subprocess.run(['adb', 'bugreport', f'{self.adb.logdir}/bugreport.zip'], capture_output=True, text=True)
            if result.returncode == 0:
                print("Bug report captured successfully.")
            else:
                print("Error occurred while capturing bug report.")
                print("Error message:", result.stderr)
        except Exception as e:
            print(f"Error occurred while capturing bug report: {e}")

    def catch_edid_info(self):
        edid_info = self.adb.run_shell_cmd("cat /sys/class/amhdmitx/amhdmitx0/hdmirx_info")[1]
        with open(self.adb.logdir + "/edid_info.log", 'w') as f:
            f.write(edid_info)

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

    def send_file_to_remote(self, local_file_path, remote_file_path, remote_host, remote_username, remote_password):
        try:
            # 建立 SSH 连接
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(remote_host, username=remote_username, password=remote_password)

            scp_client = paramiko.SFTPClient.from_transport(ssh_client.get_transport())
            run_time_dir = os.path.join(remote_file_path, self.run_time)
            mkdir_command = f'mkdir -p {run_time_dir}'
            ssh_client.exec_command(mkdir_command)
            print("run_time_dir", run_time_dir)
            # 通过 SFTP 将文件发送到远程 PC
            for local_file in local_file_path:
                remote_file = f"{run_time_dir}/{os.path.basename(local_file)}"
                scp_client.put(local_file, remote_file)
                _, stdout, _ = ssh_client.exec_command(f'mv {remote_file} {run_time_dir}/{pytest.result.get_name()}_{os.path.basename(local_file)}')
            scp_client.close()
            ssh_client.close()

            print(f"File {local_file_path} sent to remote PC successfully.")
        except Exception as e:
            print(f"Error occurred while sending file to remote PC: {e}")




