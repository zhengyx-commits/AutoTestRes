import signal
import psutil
import serial
import os
import time
import threading
import logging
import subprocess
from lib.common.tools.HW.DAQ.DaqUsb1141 import DaqUsb1141


class TempCtrl(object):
    TEMP_GUN_MIX = 80

    def __init__(self, serial="", daq="", platform_number="", test_module="", json_handler=""):
        self.shutdown_event = threading.Event()
        self.temp_ctrl_cir_stop_event = threading.Event()
        self.serial = serial
        self.daq = daq
        self.pause_power_process = None
        self.cur_temp_gun = TempCtrl.TEMP_GUN_MIX
        self.cur_board_temp = 70
        self.stop_test_flag = False
        self.result_record = None
        self.temp_ctrl_flag = False
        self.platform_number = platform_number
        self.test_module = test_module
        self.json_handler = json_handler
        self.project_json = json_handler.read(f"{os.getcwd()}/tests/HW/project/{platform_number}/{platform_number}.json")
        self.get_thermal_temp_command = self.project_json["module"][test_module]["get_thermal_temp_command"]
        self.temp_gun_max = self.project_json["temp_ctrl"]["temp_gun_max"]
        self.temp_board_max = self.project_json["temp_ctrl"]["temp_board_max"]
        self.temp_board_target = self.project_json["temp_ctrl"]["temp_board_target"]
        self.gun_serial_number = self.project_json["temp_ctrl"]["gun_serial_number"]

    @staticmethod
    def pause_power(serial_number="/dev/ttyCH9344USB1"):
        """
        Pauses power for a specified serial number.

        Args:
        - serial_number (str, optional): Serial number to pause power (default: "/dev/ttyCH9344USB1").

        Returns:
        - subprocess.Popen: Process object representing the execution of the power pause command.

        This method triggers the pausing of power for a specified serial number using a subprocess.

        Note:
        - The command execution pauses the power for the provided serial number.

        Example:
        - To pause power for a different serial number:
          `pause_power("/dev/ttyOTHER_SERIAL")`
        """
        # Construct the command to pause power for the given serial number
        command = f"./lib/common/tools/HW/powerOff {serial_number} off"
        # Execute the command using subprocess.Popen
        process = subprocess.Popen(command, shell=True)
        # Return the process object representing the execution of the power pause command
        return process

    @staticmethod
    def kill_process_by_name(process_name):
        """
        Terminates a process by its name.

        Args:
        - process_name (str): Name of the process to terminate.

        This method iterates through the existing processes and terminates the process
        that matches the given process name.

        Note:
        - This function uses psutil library to iterate through the running processes.
        - It terminates the process by sending a SIGTERM signal to its associated PID.

        Example:
        - To terminate a process named "example_process":
          `kill_process_by_name("example_process")`
        """
        # Iterate through all running processes
        for proc in psutil.process_iter(['pid', 'name']):
            # Check if the process name matches the given process_name
            if proc.info['name'] == process_name:
                # Get the PID of the matching process
                pid = proc.info['pid']
                try:
                    # Attempt to terminate the process by sending SIGTERM signal
                    os.kill(pid, signal.SIGTERM)
                    logging.info(f"Process {process_name} with PID {pid} terminated.")
                except ProcessLookupError:
                    # If process not found with the given PID, log the information
                    logging.info(f"Process {process_name} with PID {pid} not found.")

    def temp_gun_init(self):
        """
        Initializes the temperature gun.

        This method initializes the temperature gun by sending specific key signals
        to the DAQ (Data Acquisition) hardware. It sets the temperature gun GPIO keys
        to predefined values and waits for a specified duration to ensure proper initialization.

        Note:
        - The method assumes the existence of a DAQ object with appropriate methods to control
          temperature-related GPIO keys.
        - The TEMP_GUN_GPIO_KEY_ADD_INDEX and TEMP_GUN_GPIO_KEY_REDUCE_INDEX are assumed to be
          constants indicating specific GPIO key indices for temperature control.

        It also updates the current temperature of the gun to a predefined initial temperature value.

        Example:
        - Initializing the temperature gun:
          `obj.temp_gun_init()`
        """
        # Send key signals to the DAQ to set temperature gun GPIO keys
        self.daq.temp_gun_key_once(self.daq.TEMP_GUN_GPIO_KEY_ADD_INDEX, 1)
        # Signal to reduce temperature
        self.daq.temp_gun_key_once(self.daq.TEMP_GUN_GPIO_KEY_REDUCE_INDEX, 0)
        # Wait for 10 seconds for initialization
        time.sleep(10)
        # Signal to increase temperature
        self.daq.temp_gun_key_once(self.daq.TEMP_GUN_GPIO_KEY_REDUCE_INDEX, 1)
        # Set the current gun temperature to a predefined value
        self.temp_gun = TempCtrl.TEMP_GUN_MIX

    def temp_ctrl_init(self):
        """
        Initializes temperature control:

        - Sets the power-on signal to False.
        - Starts a thread to pause the power.
        - Initializes the temperature gun.
        - Executes temperature gun key presses for calibration.
        - Starts the pause power process.
        - Sets the power-on signal to True after a delay.
        - Checks the serial status; terminates the 'powerOff' process if the status check fails.
        - If the serial status check passes, sets the temperature gun value to its initial mix value and returns True.
        - If the serial status check fails, logs the failure, terminates the 'powerOff' process, and returns False.
        """
        # Sets the power-on signal to False
        self.serial.power_on_signal = False

        # Starts a thread to pause the power
        board_power_off_thread = threading.Thread(target=self.serial.pause_power)
        board_power_off_thread.start()

        # Initializes the temperature gun
        self.temp_gun_init()

        # Executes temperature gun key presses for calibration
        self.daq.temp_gun_key(temp_gun_gpio_key_index=self.daq.TEMP_GUN_GPIO_KEY_ADD_INDEX, times=5)
        time.sleep(2)
        self.daq.temp_gun_key(temp_gun_gpio_key_index=self.daq.TEMP_GUN_GPIO_KEY_REDUCE_INDEX, times=5)
        time.sleep(2)

        # Starts the pause power process
        self.pause_power_process = self.pause_power(self.gun_serial_number)
        time.sleep(5)

        # Sets the power-on signal to True after a delay
        self.serial.power_on_signal = True
        time.sleep(40)

        # Checks the serial status
        if not self.serial.check_serial_status():
            # Terminates the 'powerOff' process
            self.kill_process_by_name("powerOff")
            logging.info("serial status check failed")
            return False
        else:
            return True

    def get_board_temp(self):
        """
        Retrieves the current board temperature:

        - Fetches the current CPU temperature using the 'getprop_node_value' function from the serial interface.
        - Converts the obtained CPU temperature to Celsius if available.
        - Compares the difference between the current board temperature and the previously recorded board temperature.
        - Updates the current board temperature value if the difference is within a specified range.

        Returns:
        - True if the current board temperature is successfully obtained and within the specified range of the previous value.
        - False if unable to retrieve the current board temperature.
        """
        # Fetches the current CPU temperature from the serial interface
        temp = self.serial.getprop_node_value(self.get_thermal_temp_command, r'^\d+$')
        if temp:
            # Converts the obtained CPU temperature to Celsius if available
            temp = int(temp) / 1000
            # Compares the difference between the current board temperature and the previously recorded board temperature
            if abs(temp - self.cur_board_temp) <= 50:
                self.cur_board_temp = temp
                logging.info(f"cur board temp:{self.cur_board_temp}")
        return temp

    def temp_ctrl_on(self):
        """
        Initiates temperature control:

        - Sets the temperature control flag to True.
        - Waits for a specific duration before performing further actions.
        - Checks if the pause_power_process exists and kills the process if found.
        - Initializes the delta_temp variable to 3.
        - Enters a loop to control the temperature until the delta_temp falls below a certain threshold.

        """
        # Sets the temperature control flag to True
        self.temp_ctrl_flag = True
        # Waits board boot complete 30s
        time.sleep(30)

        # Checks if the pause_power_process exists and kills the process if found
        if self.pause_power_process:
            self.kill_process_by_name("powerOff")
            logging.info("gun power on now")
            self.pause_power_process = None

        # wait temp gun heat 30s
        time.sleep(30)

        while True:
            temp = self.get_board_temp()
            if temp:
                cur_board_temp = temp
            else:
                continue

            delta_temp = self.temp_board_target - cur_board_temp
            if delta_temp >= 2.5:
                time_wait = round(2 * delta_temp)
                delta_temp = round(delta_temp)
                calculated_temp_gun = self.cur_temp_gun + delta_temp
                if calculated_temp_gun >= self.temp_gun_max:
                    actual_delta_temp = round(self.temp_gun_max - self.cur_temp_gun)
                    time_wait = round(2 * actual_delta_temp)
                    if actual_delta_temp != 0:
                        self.daq.temp_gun_key(temp_gun_gpio_key_index=DaqUsb1141.TEMP_GUN_GPIO_KEY_ADD_INDEX,
                                              times=actual_delta_temp)
                    self.cur_temp_gun = self.temp_gun_max
                else:
                    self.daq.temp_gun_key(temp_gun_gpio_key_index=DaqUsb1141.TEMP_GUN_GPIO_KEY_ADD_INDEX,
                                          times=delta_temp)
                    self.cur_temp_gun = calculated_temp_gun
                start_time = time.time()
                while time.time() - start_time <= time_wait:
                    temp = self.get_board_temp()
                    if temp:
                        cur_board_temp = temp
                    else:
                        continue
                    delta_temp = self.temp_board_target - cur_board_temp
                    if delta_temp < 0:
                        logging.info("temp has exceeded")
                        break
            elif delta_temp <= -2.5:
                time_wait = abs(round(2 * delta_temp))
                delta_temp = abs(round(delta_temp))
                calculated_temp_gun = self.cur_temp_gun - delta_temp
                if calculated_temp_gun >= TempCtrl.TEMP_GUN_MIX:
                    self.daq.temp_gun_key(temp_gun_gpio_key_index=DaqUsb1141.TEMP_GUN_GPIO_KEY_REDUCE_INDEX,
                                          times=delta_temp)
                    self.cur_temp_gun = calculated_temp_gun
                else:
                    actual_delta_temp = abs(self.cur_temp_gun - TempCtrl.TEMP_GUN_MIX)
                    time_wait = abs(round(2 * actual_delta_temp))
                    self.daq.temp_gun_key(temp_gun_gpio_key_index=DaqUsb1141.TEMP_GUN_GPIO_KEY_REDUCE_INDEX,
                                          times=actual_delta_temp)
                    self.cur_temp_gun = TempCtrl.TEMP_GUN_MIX
                start_time = time.time()
                while time.time() - start_time <= time_wait:
                    temp = self.get_board_temp()
                    if temp:
                        cur_board_temp = temp
                    else:
                        continue
                    delta_temp = self.temp_board_target - cur_board_temp
                    if delta_temp > 0:
                        logging.info("temp too low")
                        break
            else:
                logging.info("temp temperature has been reached")
                break

            time.sleep(1)

        # Starts the thread for temperature control circuit
        board_power_off_thread = threading.Thread(target=self.temp_ctrl_cir)
        board_power_off_thread.daemon = True
        board_power_off_thread.start()
        logging.info("temp ctrl thread start")

    def temp_ctrl_cir(self):
        """
        Controls the temperature within a circuit:

        - Monitors the temperature by continuously checking the board temperature.
        - If the temperature exceeds a threshold or falls below a threshold, takes corrective actions.
        - Stops the temperature control loop when the stop event is set.

        """
        while not self.temp_ctrl_cir_stop_event.is_set():
            logging.info("-------------------------temp ctrl ing----------------------------------")

            temp = self.get_board_temp()
            if temp:
                cur_board_temp = temp
            else:
                continue

            if cur_board_temp > self.temp_board_max:
                logging.info("board temp too high!!!!")
                self.stop_test_flag = True
                self.result_record = "board temp too high"
                break
            else:
                delta_temp = self.temp_board_target - cur_board_temp

            if delta_temp >= 0.5:
                time_wait = round(2 * delta_temp)
                delta_temp = round(delta_temp)
                calculated_temp_gun = self.cur_temp_gun + delta_temp
                if calculated_temp_gun >= self.temp_gun_max:
                    actual_delta_temp = round(self.temp_gun_max - self.cur_temp_gun)
                    if actual_delta_temp != 0:
                        self.daq.temp_gun_key(temp_gun_gpio_key_index=DaqUsb1141.TEMP_GUN_GPIO_KEY_ADD_INDEX,
                                              times=actual_delta_temp)
                    self.cur_temp_gun = self.temp_gun_max
                else:
                    self.daq.temp_gun_key(temp_gun_gpio_key_index=DaqUsb1141.TEMP_GUN_GPIO_KEY_ADD_INDEX,
                                          times=delta_temp)
                    self.cur_temp_gun = calculated_temp_gun
                start_time = time.time()
                while time.time() - start_time <= time_wait:
                    temp = self.get_board_temp()
                    if temp:
                        cur_board_temp = temp
                    else:
                        continue
                    delta_temp = self.temp_board_target - cur_board_temp
                    if delta_temp < 0:
                        logging.info("temp has exceeded")
                        break
            elif delta_temp <= -0.5:
                time_wait = abs(round(2 * delta_temp))
                delta_temp = abs(round(delta_temp))
                calculated_temp_gun = self.cur_temp_gun - delta_temp
                if calculated_temp_gun >= TempCtrl.TEMP_GUN_MIX:
                    self.daq.temp_gun_key(temp_gun_gpio_key_index=DaqUsb1141.TEMP_GUN_GPIO_KEY_REDUCE_INDEX,
                                          times=delta_temp)
                    self.cur_temp_gun = calculated_temp_gun
                else:
                    actual_delta_temp = abs(self.cur_temp_gun - TempCtrl.TEMP_GUN_MIX)
                    time_wait = abs(round(2 * actual_delta_temp))
                    self.daq.temp_gun_key(temp_gun_gpio_key_index=DaqUsb1141.TEMP_GUN_GPIO_KEY_REDUCE_INDEX,
                                          times=actual_delta_temp)
                    self.cur_temp_gun = TempCtrl.TEMP_GUN_MIX
                start_time = time.time()
                while time.time() - start_time <= time_wait:
                    temp = self.get_board_temp()
                    if temp:
                        cur_board_temp = temp
                    else:
                        continue
                    delta_temp = self.temp_board_target - cur_board_temp
                    if delta_temp > 0:
                        logging.info("temp too low")
                        break

            if self.cur_temp_gun > self.temp_gun_max:
                logging.info("gun temp too high!!!!")
                self.temp_gun_init()
                self.result_record = "gun temp too high!!!!"
                self.stop_test_flag = True
                break

            time.sleep(1)

        logging.info("-----------------temp ctrl cir stop------------------")
        self.temp_gun_init()
        self.temp_ctrl_flag = False