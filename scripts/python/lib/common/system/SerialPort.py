#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/25 13:43
# @Author  : chao.li
# @Site    : SH #5-389
# @File    : SerialPort.py
# @Email   : chao.li@amlogic.com
# @Software: PyCharm

'''
测试通用方法模块,
包含
adb交互封装类
串口交互封装类
'''

import logging
import os
import re
import signal
import subprocess
import time
from time import sleep
import threading
import pytest
import serial

from util.Decorators import set_timeout


class SerialPort:
    '''
    serial command control

    Attributes:
        serial_port : serial port
        baud : baud
        ser : serial.Serial instance
        ethernet_ip : ip address
        status : serial statuc
    '''

    reboot_wait_time = 200
    board_list = ["t5m_ay301#", "sc2_ah212#", "s4_ap222#", "t3x_bc302#", "s7_bh201#", "gxl_p211_v1#", "s4_aq222",
                  "ay30a5#", "t5m_ay30a1#"]

    def __init__(self, serial_port='', baud=''):
        self.serial_port = serial_port or self.get_serial_port()
        self.baud = baud or self.get_serial_baud()
        logging.info(f"self.serial_port: {self.serial_port},self.baud: {self.baud}")
        self.ser = ''
        self.ethernet_ip = ''
        self.uboot_time = 0
        self.power_on_signal = True
        self.method_lock = threading.Lock()
        try:
            self.ser = serial.Serial(self.serial_port, self.baud, timeout=0.25)
            logging.info('the serial port %s-%s is opened' % (self.serial_port, self.baud))
            self.write('su')
            assert self.recv_until_pattern(b'#'), 'The serial port cannot to communicate to device'
            # self.ser.write(chr(0x03))
            if "t5m" in pytest.target.get("prj") or "xiaomi" in pytest.target.get("prj"):
                logging.info("No need to setprop")
            else:
                self.write('setprop persist.sys.usb.debugging y')
                self.write('setprop service.adb.tcp.port 5555')
        except serial.serialutil.SerialException as e:
            logging.info(f'not found serial:{e}')
        if isinstance(self.ser, serial.Serial):
            self.status = self.ser.isOpen()
        else:
            self.status = False
        if self.ethernet_ip:
            logging.info('get ip ：%s' % self.ethernet_ip)
        logging.info('the status of serial port is {}'.format(self.status))

    def get_serial_port(self):
        serial_ports = []
        if isinstance(pytest.config, list):
            for serial_port in pytest.config:
                serial_ports.append(serial_port['serial_port'])
            return serial_ports
        else:
            return pytest.config['serial_port']

    def get_serial_baud(self):
        serial_bauds = []
        if isinstance(pytest.config, list):
            for serial_port in pytest.config:
                serial_bauds.append(serial_port['baudrate'])
            return serial_bauds
        else:
            return pytest.config['baudrate']

    def get_ip_address(self, inet='ipv4'):
        '''
        get ip address
        @param inet: inet type ipv4 or ipv6
        @return:
        '''
        ip, eth0Ip, wlanIp, ppp0Ip = '', '', '', ''
        logging.info('getting ip info through the serial port')
        self.write('ifconfig')
        time.sleep(2)
        ipInfo = ''.join([i.decode('utf-8') for i in self.ser.readlines()]).split('TX bytes:')
        logging.info(ipInfo)
        if ipInfo == ['']:
            logging.info('no ip')
            return None
        for i in ipInfo:
            if 'eth0' in i:
                if inet == 'ipv4':
                    eth0Ip = re.findall(r'inet addr:(.*?)  Bcast', i, re.S)
                if inet == 'ipv6':
                    eth0Ip = re.findall(r'inet6 addr:(.*?)  Bcast', i, re.S)
                return eth0Ip[0]
            if 'wlan0' in i:
                wlanIp = re.findall(r'inet addr:(.*?)  Bcast', i, re.S)
                return wlanIp[0]
            if 'ppp0' in i:
                ppp0Ip = re.findall(r'inet addr:(.*?)  P-t-P', i, re.S)
                return ppp0Ip[0]
        logging.info('Devices no ip info')
        return None

    def write_pipe(self, command):
        '''
        execute the command , get feecback
        @param command: command
        @return: feedback
        '''
        self.ser.write(bytes(command + '\r', encoding='utf-8'))
        logging.info(f'=> {command}')
        sleep(0.1)
        data = self.recv()
        logging.debug(data.strip())
        return data

    def get_power_relay_bin(self):
        workspace = os.environ.get("WORKSPACE")
        if not workspace:
            workspace = re.findall(r"(.*?)/AutoTestRes", os.getcwd())[0]
        power_relay_bin = f"{workspace}/AutoTestRes/bin/powerRelay"
        return power_relay_bin

    def enter_uboot(self, keyboard="enter", power_relay=None, time_out=60):
        uboot_status = False
        info = ""
        try:
            self.write("version")
            info = self.ser.read(5000).decode('utf-8', errors="ignore")
        except UnicodeDecodeError as decode_error:
            logging.info(decode_error)
        if 'U-Boot' in info or any(board in info for board in self.board_list):
            logging.info("In uboot")
            uboot_status = True
            return uboot_status
        else:
            if power_relay:
                try:
                    power_relay_bin = self.get_power_relay_bin()
                    subprocess.run([power_relay_bin, power_relay, "1", "off"], check=True)
                    time.sleep(3)
                    subprocess.run([power_relay_bin, power_relay, "1", "on"], check=True)
                    time.sleep(2)
                except subprocess.CalledProcessError as call_error:
                    logging.info(f"Call power relay bin failed:{call_error}")
            else:
                self.write("reboot")
                # time.sleep(1)
            start = time.time()
            while time.time() - start < time_out:
                for _ in range(10):
                    time.sleep(0.05)
                    if keyboard == 'enter':
                        self.write("\r")  # keyboard enter
                    else:
                        self.write("\x03")  # keyboard ctrl+c
                time.sleep(0.5)
                self.write("version")
                info = self.ser.read(5000).decode('utf-8', errors="ignore")
                # if 'U-Boot' in info or any(board in info for board in self.board_list):
                if any(board in info for board in self.board_list):
                    logging.info("Enter uboot success")
                    uboot_status = True
                    return uboot_status
            logging.info("Enter uboot timeout")
            return uboot_status

    def enter_kernel(self):
        '''
        enter in kernel
        @return: kernel status : boolean
        '''
        self.write('reset')
        sleep(2)
        start = time.time()
        info = ''
        while time.time() - start < 60:
            try:
                info = self.ser.read(10000).decode('utf-8')
                logging.info(info)
            except UnicodeDecodeError as e:
                logging.warning(e)
            if 'uboot time: ' in info:
                logging.debug(f"uboot log line is: {info}")
                matches = re.findall(".*uboot time: (.*) us?.*", info, re.S)
                logging.debug(f"matches: {matches}")
                if matches:
                    logging.debug(f"Matched content: {matches[0]}")
                    match = re.search(r'\b(\d+)\b', matches[0]).group(1)
                    # 尝试提取整数部分
                    try:
                        self.uboot_time = int(match)
                        logging.info(f"Converted to integer: {self.uboot_time}")
                    except ValueError as e:
                        logging.error(f"Error converting to integer: {e}")
                else:
                    logging.info("No match found")
            if 'Starting kernel ...' in info:
                self.write('\n\n')
            if 'console:/ $' in info:
                logging.info('now is in kernel')
                return True

        logging.info('no kernel message captured,please confirm manually')

    def write(self, command):
        '''
        enter in kernel
        @param command: command
        @return:
        '''
        self.ser.write(bytes(command + '\r', encoding='utf-8'))
        logging.info(f'=> {command}')
        sleep(0.1)

    def recv(self):
        '''
        get feedback from buffer
        @return: feedback
        '''
        while True:
            data = self.ser.read_all()

            time.sleep(5)
            if data == '':
                continue
            else:
                break
        return data.decode('utf-8')

    def recv_until_pattern(self, pattern=b'', timeout=90):
        '''
        keep get feedback from buffer until pattern has been catched
        @param pattern: pattern
        @param timeout: timeout
        @return: contains the printing of keywords
        '''
        start = time.time()
        result = []
        while True:
            if time.time() - start > timeout:
                if pattern:
                    raise TimeoutError('Time Out')
                return result
            log = self.ser.readline()
            if not log:
                continue
            logging.info(log)
            result.append(log)
            if pattern and pattern in log:
                return result

    def receive_file_via_serial(self, output_file):
        try:
            # 打开输出文件以写入数据
            with open(output_file, 'wb') as file:
                while True:
                    # 从串口读取数据
                    data = self.ser.read(1024)
                    if not data:
                        break

                    # 将数据写入输出文件
                    file.write(data)

            print("文件传输完成")
        except serial.SerialException as e:
            print("串口连接错误:", str(e))
        except Exception as e:
            print("发生错误:", str(e))

    def execute_commands(self, commands):
        """
        Execute a series of commands on the serial port and check for successful execution.

        This function performs the following steps:
        1. Split the input commands by semicolons, allowing multiple commands to be executed.
        2. For each command:
           a. Clear the input buffer of the serial port.
           b. Send the command to the serial port.
           c. Handle special cases (e.g., commands starting with "echo").
           d. Check for specific success conditions.
        3. Return True if all commands were executed successfully; otherwise, return False.

        Args:
            commands (str): A string containing one or more commands to execute, separated by semicolons.

        Returns:
            bool: True if all commands are executed successfully, False if any command fails.
        """
        with self.method_lock:
            # Check if the input commands contain semicolons and split them into a list
            if ';' in commands:
                command_list = commands.split(';')
            else:
                command_list = [commands.strip()]

            for cmd in command_list:
                # Clear the input buffer to ensure clean reading
                time.sleep(2)
                self.ser.flushInput()
                # Remove leading and trailing whitespace from the command
                cmd = cmd.strip()
                # Send the command
                self.write(cmd)
                time.sleep(1)

                # Check if the command format starts with "echo"
                if cmd.startswith("echo"):
                    parts = cmd.split('>')
                    if len(parts) == 2:
                        # Get the expected value
                        expected_value = parts[0].replace('echo', '').strip()
                        # Get the property path
                        property_cmd = parts[1].strip()
                        # Handle special case for '/sys/kernel/debug/aml_reg/paddr'
                        if property_cmd == '/sys/kernel/debug/aml_reg/paddr':
                            # Transform expected value into the format: [0xFE058004] = 0x22
                            expected_value_parts = expected_value.split()
                            expected_value = f"[0x{expected_value_parts[0]}] = 0x{expected_value_parts[1].lstrip('0').upper()}"

                        # Read the property contents
                        self.write(f'cat {property_cmd}')
                        try:
                            file_output = self.ser.readall().decode('utf-8')
                        except UnicodeDecodeError:
                            logging.info(f"Serial communication is abnormal, Command execution failed: {cmd}")
                            return False

                        # Check if the expected value is in the file output
                        if expected_value not in file_output:
                            logging.info(file_output)
                            logging.info(f"Command execution failed: {cmd}")
                            return False

                # Check if the command is "su"
                elif cmd == "su":
                    try:
                        file_output = self.ser.readall().decode('utf-8')
                    except UnicodeDecodeError:
                        logging.info("Serial communication is abnormal, su fail")
                        return False

                    if "#" in file_output:
                        logging.info("su success")
                    else:
                        logging.info(file_output)
                        logging.info("su fail")
                        return False

                # Check if the command is "mount -t debugfs none /sys/kernel/debug/"
                elif cmd == "mount -t debugfs none /sys/kernel/debug/":
                    self.write("cd /sys/kernel/debug/aml_reg/")
                    try:
                        file_output = self.ser.readall().decode('utf-8')
                    except UnicodeDecodeError:
                        logging.info("Serial communication is abnormal, mount fail")
                        return False

                    if "No such file or directory" not in file_output:
                        logging.info("mount success")
                    else:
                        logging.info(file_output)
                        logging.info("mount fail")
                        return False

                elif cmd.startswith("md"):
                    try:
                        file_output = self.ser.readall().decode('utf-8')
                    except UnicodeDecodeError:
                        logging.info("Serial communication is abnormal, mount fail")
                        return False
                    if cmd.split(" ")[1][2:] not in file_output:
                        logging.info("md success")
                    else:
                        logging.info(file_output)
                        logging.info("md fail")
                        return False
                elif cmd.startswith("mw"):
                    reg_address = cmd.split(" ")[1][2:]
                    reg_value = cmd.split(" ")[2]
                    md_cmd = f"md {reg_address} 1"
                    self.write(md_cmd)
                    try:
                        file_output = self.ser.readall().decode('utf-8')
                    except UnicodeDecodeError:
                        logging.info("Serial communication is abnormal, mount fail")
                        return False
                    if f"{reg_address} :{reg_value}" not in file_output:
                        logging.info("mw success")
                    else:
                        logging.info(file_output)
                        logging.info("mw fail")
                        return False
            # All commands were successfully executed
            logging.info("All commands executed successfully")
            return True

    def verify_serial_output(self, command, expected_value):
        """
        Verify serial output against an expected value after sending a command.

        This function performs the following steps:
        1. Clears the input buffer of the serial port.
        2. Sends a command to the serial port.
        3. Reads the serial output, decodes it, and logs it.
        4. Optionally handles special cases (e.g., for the "top" command).
        5. Checks if the expected value is present in the serial output.

        Args:
            command (str): The command to send to the serial port.
            expected_value (str): The expected value to check for in the serial output.

        Returns:
            bool: True if the expected value is found in the serial output, indicating successful communication; False otherwise.
        """
        # Clear the input buffer to ensure clean reading
        time.sleep(5)
        self.ser.flushInput()

        # Send the specified command
        self.write(command)

        # Read the serial output, decode it, and log it
        time.sleep(2)
        try:
            output = self.ser.readall().decode('utf-8')
        except UnicodeDecodeError:
            logging.info(f"Serial communication is abnormal, {command} fail")
            return False

        # Handle special cases, e.g., for the "top" command
        if command == "top":
            self.write("q")
            time.sleep(10)
            self.ser.flushInput()

        # Check if the expected value is present in the serial output
        if expected_value in output:
            # Serial communication is normal
            return True
        else:
            # Serial communication is abnormal
            logging.info(f"Serial communication is abnormal, {command} fail")
            return False

    def check_file_existence(self, command):
        """
        Check the existence of a file on the device using a specified command.

        This function performs the following steps:
        1. Clear the input buffer of the serial port.
        2. Send the provided command to the serial port, typically a "test" command to check file existence.
        3. Read the output from the serial port and decode it.
        4. Check if the output indicates the existence of the file.
        5. Return True if the file exists, and False if the file does not exist.

        Args:
            command (str): A command used to check the existence of a file on the device.

        Returns:
            bool: True if the file exists, False if the file does not exist.
        """
        # Clear the input buffer to ensure clean reading
        time.sleep(2)
        self.ser.flushInput()
        # Send the provided command to check file existence
        self.write(command)
        # Read and decode the output from the serial port
        try:
            output = self.ser.readall().decode('utf-8')
        except UnicodeDecodeError:
            logging.info(f"Serial communication is abnormal, {command} fail")
            return False

        # Check if the output contains "No such file or directory" to determine file existence
        if "No such file or directory" in output:
            # File does not exist
            return False
        else:
            # File exists
            return True

    def getprop_node_value(self, command, pattern, attempts=3):
        """
        Retrieve a value from a property node using a specified command and pattern.

        This function performs the following steps:
        1. Execute the provided command to retrieve information.
        2. Read the output from the serial port and decode it.
        3. Extract and return a value based on the provided regular expression pattern.
        4. Reattempt if the value is not found within the output, up to a specified number of attempts.

        Args:
            command (str): The command to execute in order to retrieve information.
            pattern (str): A regular expression pattern used to search for a specific value in the output.
            attempts (int, optional): The number of attempts to search for the value (default is 3).

        Returns:
            str: The extracted value based on the regular expression pattern, or an empty string if not found.
        """
        with self.method_lock:
            # Initialize the value variable
            value = ""

            for _ in range(attempts):
                # Execute the provided command
                time.sleep(3)
                self.ser.flushInput()
                self.write(command)

                # Read and decode the output from the serial port
                try:
                    output = self.ser.readall().decode('utf-8')
                except UnicodeDecodeError:
                    logging.info(f"Serial communication is abnormal, {command} fail")
                    return False

                # Split the output into lines and search for the value
                start = output.find(command) + len(command)
                output = output[start:].strip()
                parts = output.split()
                logging.debug(parts)
                for part in parts:
                    # Use the regular expression pattern to search for the value
                    value = re.findall(pattern, part)
                    if value:
                        logging.info(value[0])
                        return value[0]
                    else:
                        # Reset the value if not found
                        value = ""
                        logging.debug("value not found")
            # Return the extracted value or an empty string if not found
            return value

    def reboot(self, attempts=3):
        """
        Reboot the device through a serial port connection.

        Args:
            attempts (int, optional): The number of reboot attempts to make. Defaults to 3.

        Returns:
            bool: True if the reboot is successful, False if all attempts fail.

        This function attempts to reboot the device connected through a serial port.
        It will make several reboot attempts, and it checks the status of the reboot.

        During each reboot attempt:
        1. It toggles the Request To Send (RTS) signal to control power.
        2. It waits for a specified time interval (5 seconds) after toggling the RTS signal.
        3. After waiting, it checks the status by verifying the serial output.
        4. If the serial output indicates success, it immediately returns True and stops further attempts.
        5. If the serial output does not indicate success, it waits for a brief period (5 seconds) before making another attempt.

        If all reboot attempts fail, it returns False and logs a failure message.

        Note: The function expects that a serial port (self.ser) is open and correctly configured.

        """
        for i in range(attempts):
            logging.info(f"attempt: {i}")
            # Record the start time of the reboot attempt
            reboot_start_time = time.time()

            # Continue with the reboot process for a fixed duration (20 seconds)
            while time.time() - reboot_start_time < 20:
                if self.ser.isOpen():
                    # Toggle Request To Send (RTS) signal to control power
                    self.ser.setRTS(1)
                    self.ser.setRTS(0)
                else:
                    logging.info("serial not open")
                    return False

            # Sleep for a longer duration (40 seconds) to allow the reboot to complete
            time.sleep(40)

            # Record the start time for checking the reboot status
            check_start_time = time.time()

            # Continue checking the status for a specific duration (SerialPort.reboot_wait_time)
            while time.time() - check_start_time < SerialPort.reboot_wait_time:
                # Verify the serial output to determine the success of the reboot
                if not self.verify_serial_output("cat /da", "cat: /da: No such file or directory"):
                    time.sleep(5)
                else:
                    # If the serial output indicates success, return immediately
                    logging.info("reboot success")
                    return True

        logging.info("Reboot failed after {} attempts".format(attempts))
        return False

    def check_serial_status(self, attempts=True):
        """
        Check the status of the serial communication.

        This function verifies if the serial port is open and communication is functioning as expected.
        It performs the following steps:
        1. Checks if the serial port is open.
        2. Verifies serial communication by sending a command and checking for an expected response.
        3. If the communication is not successful, attempts a system reboot.
        4. Logs relevant messages for each step.

        Args:
        - attempts (bool, optional): If True, attempt system reboot if communication fails. Default is True.

        Returns:
        - bool: True if the serial communication is in a good state, False otherwise.
        """
        # Check if the serial port is open
        if self.ser.isOpen():
            # Verify serial communication by sending a command and checking for an expected response
            if not self.verify_serial_output("cat /da", "cat: /da: No such file or directory"):
                # If communication is not successful, attempt a system reboot
                if attempts:
                    # Attempt a system reboot
                    if self.reboot():
                        # Return True indicating successful communication after reboot
                        return True
                    else:
                        # Return False indicating failed communication after reboot attempt
                        logging.info("reboot is fail")
                        return False
            else:
                # Return True indicating successful serial communication
                logging.info("serial is ok")
                return True
        else:
            # Return False indicating the serial port is not open
            logging.info("serial not open")
            return False

    def pause_power(self):
        """
        Pauses the power by toggling the Request To Send (RTS) signal while waiting for the power_on_signal.

        Returns:
        - True: If the power is successfully paused.
        - False: If there's an issue with the serial connection or the power_on_signal remains False.
        """
        # While loop continues until the power_on_signal becomes True
        while not self.power_on_signal:
            # Check if the serial connection is open
            if self.ser.isOpen():
                # Toggle Request To Send (RTS) signal to control power
                self.ser.setRTS(1)
                self.ser.setRTS(0)
            else:
                # Return False indicating an issue with the serial connection
                logging.info("serial not open")
                return False
        # Return True indicating successful pausing of the power
        logging.info("pause power end")
        return True

    def __del__(self):
        try:
            self.ser.close()
            logging.info('close serial port %s' % self.ser)
        except AttributeError as e:
            logging.info('failed to open serial port,not need to close')

