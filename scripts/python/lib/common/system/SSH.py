#!/usr/bin/env python
# Copyright 2021 Amlogic.com, Inc. or its affiliates. All rights reserved.
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
from __future__ import print_function

import logging
import os
import signal
import subprocess
import threading
import time
from builtins import range

import paramiko
import pexpect


class SSH(object):
    """
    Class containing all ssh related method
    """

    def __init__(self, ip, uname="amlogic", passwd="Linux2017", platform="Linux"):
        """
        Constructor to create open and connection
        Args:
            ip: remote IP
            uname: Username used for login
            passwd: Password used for login
            platform: Platform to which connection needs to be made
        """
        self.ip = ip
        self.uname = uname
        self.passwd = passwd
        self.client = None
        self.platform = platform
        if "win" in platform.lower():
            self.platform = "Windows"
        self.export_prefix = {
            "Linux": "export PATH=$PATH:/usr/local/bin:/sbin;",
            "Windows": "",
            "Mac": "export PATH=$PATH:/usr/local/bin:/sbin;"
        }

    def open_connection(self, retries=1):
        """
        Open Connection
        Args:
            retries: default 10
        Returns:
            None
        Raises:
            RuntimeError
        """
        for i in list(range(0, retries)):
            try:
                self.client = paramiko.SSHClient()
                self.client.load_system_host_keys()
                self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self.client.connect(self.ip, username=self.uname, password=self.passwd)
                logging.info("Connection established")
            except paramiko.BadHostKeyException as e:
                logging.exception(e)
                self.remove_old_ssh_key()
                continue
            except:
                logging.exception("Open ssh connection to device %s at attempt %i failed" % (self.ip, i))
                self.client = None
                time.sleep(3)
                continue
            else:
                logging.debug("Connection established for device %s" % self.ip)
                return
        raise RuntimeError("Connection not established")

    def send_cmd(self, cmd, retries=1, timeout=20, accepted_ret_codes=[0, 1]):
        """
        send command to the device with reities time and timeout. After failure, will redo the connection. If accepted_
        ret_codes is not empty, The software will check whether the return code is inside the accepted_ret_codes
        Args:
            cmd: command to execute
            retries: Number attempts to send cmd
            timeout: Timeout for a single attempt
            accepted_ret_codes: list
        Returns:
            The stdout + \n + stderr
        Raises:
            When failed either due to timeout or failed all attempts
        """
        if not self.client:
            self.open_connection()
            logging.info("Open conneciton dne")
        for i in list(range(0, retries)):

            try:
                logging.debug("executing command %s " % cmd)
                exported_cmd = self.export_prefix[self.platform] + cmd
                _, stdout, stderr = self.client.exec_command(exported_cmd, timeout=timeout)
            except:
                logging.info("failed to execute %s in attempt %s, tries to reopen the connection" % (cmd, i))
                self.open_connection()
                continue
            logging.info("Status code %s" % stdout.channel.recv_exit_status())
            if stdout.channel.recv_exit_status() not in accepted_ret_codes:
                logging.debug("return status for command %s is %s which is non zero in attempt %s" % (
                    cmd, stdout.channel.recv_exit_status(), i))
            else:
                if self.platform == 'Windows':
                    return (stdout.read().decode('gbk'), stderr.read().decode('gbk'))
                return (stdout.read().decode('utf-8'), stderr.read().decode('utf-8'))
        raise RuntimeError("Failed to execute command %s after %s tries" % (cmd, retries))

    def do_scp(self, user, password, host, local_path, remote_path, is_pull, compress=False, timeout=30):
        """
        copy files and directories between to local_path from remote_path
        Args:
            user: username to be used on remote machine
            password: password to be used on remote machine
            host: string ip address of remote machine
            local_path: string local path on the host
            remote_path: string remote path on the remote machine
            is_pull:
            compress: copy compressed version or not
            timeout: Timeout for a single attempt
        Returns:
            none
        """
        if is_pull:
            cmd = 'scp %s@%s:%s %s' % (user, host, remote_path, local_path)
        else:
            if not compress:
                cmd = 'scp %s %s@%s:%s ' % (local_path, user, host, remote_path)
            else:
                cmd = 'scp -c 3des-cbc -C %s %s@%s:%s ' % (
                    local_path, user, host, remote_path)
        logging.info(cmd)
        child = pexpect.spawn(cmd, timeout=timeout)
        i = child.expect(['assword:', r"yes/no"], timeout=30)
        if i == 0:
            child.sendline(password)
        elif i == 1:
            child.sendline("yes")
            child.expect("assword:", timeout=30)
            child.sendline(password)
        data = child.read()
        logging.debug(data)
        child.close()

    def pull(self, remote_path, local_path, retries=2):
        """
        Pull file from remote_path on device to local_path on host. Between retries will re-establish ssh connection
        Args:
            remote_path: string remote path on the device
            local_path: string local path on the host
            retries: number of retries will be attempted at most
        Raises:
            Any exception generated
        """
        for _ in list(range(0, retries)):
            try:
                is_pull = True
                self.do_scp(self.uname, self.passwd, self.ip, local_path, remote_path, is_pull)
                return
            except Exception as e:
                logging.exception(e)

    def push(self, local_path, remote_path, retries=2, timeout=30, compress=False):
        """
        Push file from local_path on host to remote_path on device. Between retries will re-establish ssh connection
        Args:
            remote_path: string remote path on the device
            local_path: string local path on the host
            retries: number of retries will be attempted at most
        Raises:
            Any exception generated
        """
        for _ in list(range(0, retries)):
            try:
                is_pull = False
                print(local_path)
                self.do_scp(self.uname, self.passwd, self.ip, local_path, remote_path, is_pull, compress=compress,
                            timeout=timeout)
                return
            except Exception as e:
                logging.exception(e)

    def reboot(self):
        """
        Send the reboot command to device
        Returns:
            The stdout + \n + stderr
        """
        return self.send_cmd("reboot")

    def wait_for_device(self, timeout=5):
        """
        Wait for device to respond to ping traffic
        Args:
            timeout: timeout for the device to respond
        Returns:
            0 if device is reachable, else 1
        Note: These values are for making it consistent with adb library's wait_for_device method
        """
        ping_ret = ""
        for _ in list(range(0, timeout)):
            ping_ret = self.is_device_reachable()
            if ping_ret.find("1 received") > 0:
                return ping_ret
            else:
                time.sleep(1)
        return ping_ret

    def is_device_reachable(self, retries=10):
        """
        Check if device is reachable via ping
        Returns:
            The stdout + \n + stderr
        """
        stdout, stderr = self.subprocess_timeout("ping -c 1 " + self.ip, retries=retries)
        return "%s\n%s" % (stdout, stderr)

    def remove_old_ssh_key(self):
        """
        Remove the old ssh key
        Returns:
            The stdout + \n + stderr
        """
        stdout, stderr = self.subprocess_timeout("ssh-keygen -f ~/.ssh/known_hosts -R " + self.ip)
        return "%s\n%s" % (stdout, stderr)

    def close_connection(self):
        """
        Close existing ssh connection
        Raises:
            Exception if any
        """
        try:
            self.client.close()
        except Exception as ex:
            raise ConnectionError("Captured exception during close ssh connection, exception message {}".format(ex))

    def subprocess_timeout(self, cmd, retries=2, timeout=5, accepted_ret_codes=[0]):
        """
        Execute cmd with timeout and retries. If accepted_ret_codes is not empty, The software will check whether the
        return code is inside the accepted_ret_codes
        :param cmd: The cmd to execute
        :param retries: Number of retries when failed
        :param timeout: Timeout for a single retry
        :param accepted_ret_codes: list
        :return: The output string of the command
        """

        class nested_shared_var:
            proc = None

        logging.debug("Executing the command %s " % cmd)

        def subprocess_thread(subproc_cmd, outputs):
            """
            Thread for executing subprocess.
            Args:
                subproc_cmd: Cmd to execute, with shell = True
                outputs: a list. Parsed in am empty list, when finish successfully, first element will be stdout,
                second element will be stderr, and third will be the return code. When failed, the list will be empty, and
                exception will be logged
            """
            try:
                # The os.setsid() is passed in the argument preexec_fn so
                # it's run after the fork() and before  exec() to run the shell.
                nested_shared_var.proc = subprocess.Popen(subproc_cmd, shell=True,
                                                          stdout=subprocess.PIPE,
                                                          stderr=subprocess.PIPE,
                                                          preexec_fn=os.setsid)
                output, error = nested_shared_var.proc.communicate()
            except:
                logging.exception("Executing adb cmd %s failed" % subproc_cmd)
            else:
                outputs.append(output)
                outputs.append(error)
                outputs.append(nested_shared_var.proc.returncode)

        for i in list(range(0, retries)):
            logging.debug("Executing cmd %s at attempt %s " % (cmd, i))
            output_list = []
            t = threading.Thread(target=subprocess_thread, args=(cmd, output_list))
            t.start()
            if timeout is not None:
                t.join(timeout=timeout)
            else:
                t.join()
            if t.is_alive():
                os.killpg(os.getpgid(nested_shared_var.proc.pid), signal.SIGTERM)
                t.join()
            if len(output_list) == 0 or (
                    len(accepted_ret_codes) > 0 and output_list[
                2] not in accepted_ret_codes):
                time.sleep(2)
                continue
            return output_list[0], output_list[1]

        raise RuntimeError("Command %s executed failed" % cmd)

# ssh = SSH('10.18.7.30')
# print(ssh.send_cmd('ls')[0])
