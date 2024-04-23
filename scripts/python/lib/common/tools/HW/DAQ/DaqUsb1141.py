import time
import sys
from . import libdaq
from ctypes import *
import math
import os
import logging


class DaqUsb1141(object):
    CH_RANGE = libdaq.CHANNEL_RANGE_N5V_P5V
    CH_COUPLE_MODE = libdaq.ADC_CHANNEL_DC_COUPLE
    CH_REFGROUND_RSE = libdaq.ADC_CHANNEL_REFGND_RSE
    CH_REFGROUND_DIFF = libdaq.ADC_CHANNEL_REFGND_DIFF
    TEMP_GUN_GPIO_KEY_REDUCE_INDEX = 4
    TEMP_GUN_GPIO_KEY_ADD_INDEX = 5

    def __init__(self, platform_number="T3X", test_module="A55", json_handler=""):
        index = 0
        libdaq.libdaq_init()
        device_count = libdaq.libdaq_device_get_count()
        logging.info(f"device_count: {device_count}")
        if device_count < 1:
            raise ValueError("no device detected!")
        device_name = create_string_buffer(b'0', 100)
        libdaq.libdaq_device_get_name(index, byref(device_name), len(device_name))
        logging.info("device: %s detected" % device_name.value)
        self.device = libdaq.DAQUSB1141(device_name)
        self.project_json = json_handler.read(f"{os.getcwd()}/tests/HW/project/{platform_number}/{platform_number}.json")
        self.current_multiple = self.project_json["module"][test_module]["current_multiple"]
        self.num_samples_voltage = self.project_json["num_samples"]["voltage"]
        self.num_samples_current = self.project_json["num_samples"]["current"]
        self.adc_index = self.project_json["adc_index"]
        self.channel_index_voltage = self.project_json["channel_index"]["voltage"]
        self.channel_index_current = self.project_json["channel_index"]["current"]

    def adc_rse_sample(self, selected_channel_index=""):
        """
        Perform single-ended ADC sampling:

        - Configure ADC channels with the selected settings.
        - Collect ADC data for each channel in the given channel list.
        - Calculate the average of sampled values for each channel.

        Returns:
        - If no specific channel is selected, returns a dictionary containing the average result for each channel.
        - If a specific channel is chosen, returns the average result for that particular channel.
        """
        # channel config
        for channel in range(0, 4):
            if self.adc_index == 1:
                self.device.ADC1.config_channel_ex(channel, DaqUsb1141.CH_RANGE, DaqUsb1141.CH_COUPLE_MODE, DaqUsb1141.CH_REFGROUND_RSE)
            else:
                self.device.ADC2.config_channel_ex(channel, DaqUsb1141.CH_RANGE, DaqUsb1141.CH_COUPLE_MODE,
                                                   DaqUsb1141.CH_REFGROUND_RSE)

        # Define the channel list to sample data
        channel_list = [0, 1, 2, 3]

        # Initialize a list to store all results
        all_results = []
        adc_res = {}

        # Get ADC data for a specific number of samples

        for _ in range(self.num_samples_voltage):
            # Retrieve ADC data for the given channel list
            if self.adc_index == 1:
                (errorcode, result) = self.device.ADC1.singleSample(channel_list)
            else:
                (errorcode, result) = self.device.ADC2.singleSample(channel_list)

            # Append the result to the list
            all_results.append(result)

        # Calculate the average for each channel in the channel list
        for channel in range(len(channel_list)):
            channel_average = sum(result[channel] for result in all_results) / self.num_samples_voltage
            formatted_average = "%.3f" % channel_average
            adc_res[channel] = formatted_average

        logging.info(adc_res)
        # Check if a specific channel index is provided and return the corresponding result
        if self.channel_index_voltage is None and selected_channel_index is None:
            return adc_res
        elif selected_channel_index is None:
            return adc_res[self.channel_index_voltage]
        else:
            return adc_res[selected_channel_index]

    def adc_current_sample(self, selected_channel_index="", current_multiple=""):
        """
        Perform differential ADC sampling:

        - Configure ADC channels with the selected settings for differential mode.
        - Collect ADC data for each channel in the given channel list.
        - Calculate the average of sampled values for each channel.

        Returns:
        - If no specific channel is selected, returns a dictionary containing the average result for each channel.
        - If a specific channel is chosen, returns the average result for that particular channel.
        """
        if current_multiple:
            current_multiple = current_multiple
        else:
            current_multiple = self.current_multiple

        # Channel configuration for differential mode
        for channel in range(0, 4):
            if self.adc_index == 1:
                self.device.ADC1.config_channel_ex(channel, DaqUsb1141.CH_RANGE, DaqUsb1141.CH_COUPLE_MODE, DaqUsb1141.CH_REFGROUND_DIFF)
            else:
                self.device.ADC2.config_channel_ex(channel, DaqUsb1141.CH_RANGE, DaqUsb1141.CH_COUPLE_MODE,
                                                   DaqUsb1141.CH_REFGROUND_DIFF)

        # Define the channel list for data sampling
        channel_list = [0, 2]

        # Initialize a list to store all results
        all_results = []
        adc_current = {}

        # Get ADC data for a specific number of samples
        for _ in range(self.num_samples_current):
            # Get adc data
            if self.adc_index == 1:
                (errorcode, result) = self.device.ADC1.singleSample(channel_list)
            else:
                (errorcode, result) = self.device.ADC2.singleSample(channel_list)

            # Append the result to the list
            all_results.append(result)

        # Calculate the average for each channel in the channel list
        for channel in range(len(channel_list)):
            channel_average = sum(result[channel] for result in all_results) / self.num_samples_current
            test_average = channel_average * current_multiple
            formatted_average = "%.1f" % test_average
            adc_current[channel_list[channel]] = formatted_average
        logging.info(adc_current)
        # Check if a specific channel index is provided and return the corresponding result
        if self.channel_index_current is None and selected_channel_index is None:
            return adc_current
        elif selected_channel_index is None:
            return adc_current[self.channel_index_current]
        else:
            return adc_current[selected_channel_index]

    def adc_diff_sample(self, selected_channel_index=""):
        """
        Perform differential ADC sampling:

        - Configure ADC channels with the selected settings for differential mode.
        - Collect ADC data for each channel in the given channel list.
        - Calculate the average of sampled values for each channel.

        Returns:
        - If no specific channel is selected, returns a dictionary containing the average result for each channel.
        - If a specific channel is chosen, returns the average result for that particular channel.
        """

        # Channel configuration for differential mode
        for channel in range(0, 4):
            if self.adc_index == 1:
                self.device.ADC1.config_channel_ex(channel, DaqUsb1141.CH_RANGE, DaqUsb1141.CH_COUPLE_MODE, DaqUsb1141.CH_REFGROUND_DIFF)
            else:
                self.device.ADC2.config_channel_ex(channel, DaqUsb1141.CH_RANGE, DaqUsb1141.CH_COUPLE_MODE,
                                                   DaqUsb1141.CH_REFGROUND_DIFF)

        # Define the channel list for data sampling
        channel_list = [0, 2]

        # Initialize a list to store all results
        all_results = []
        adc_diff = {}

        # Get ADC data for a specific number of samples
        for _ in range(self.num_samples_current):
            # Get adc data
            if self.adc_index == 1:
                (errorcode, result) = self.device.ADC1.singleSample(channel_list)
            else:
                (errorcode, result) = self.device.ADC2.singleSample(channel_list)

            # Append the result to the list
            all_results.append(result)

        # Calculate the average for each channel in the channel list
        for channel in range(len(channel_list)):
            test_average = sum(result[channel] for result in all_results) / self.num_samples_current
            formatted_average = "%.5f" % test_average
            adc_diff[channel_list[channel]] = formatted_average

        # Check if a specific channel index is provided and return the corresponding result
        if self.channel_index_current is None and selected_channel_index is None:
            return adc_diff
        elif selected_channel_index is None:
            return adc_diff[self.channel_index_current]
        else:
            return adc_diff[selected_channel_index]

    def temp_gun_key(self, temp_gun_gpio_key_index, times=2, attempt=3):
        """
        Controls a GPIO key on the DAQ device by pressing and releasing it for a specific number of times.

        Args:
        - temp_gun_gpio_key_index: Index of the GPIO key to be controlled.
        - times: Number of times to press and release the GPIO key (default is 2).
        - attempt: Number of attempts to perform the press/release action for each key press (default is 3).

        Returns:
        - True if the GPIO key control is successful for all attempts; False otherwise.
        """
        for _ in range(times):
            # Attempt to write bit value '0' to the GPIO key 'temp_gun_gpio_key_index'
            # Multiple attempts are made as specified by 'attempt' parameter
            for i in range(attempt):
                error_code = self.device.GPIOOUT.write_bit(temp_gun_gpio_key_index, 0)
                time.sleep(0.05)
                # If successful (error_code = 0), break out of the loop to proceed to the next key press
                if error_code == 0:
                    break
            else:
                # If all attempts fail, return False indicating unsuccessful control of the GPIO key
                return False

            for i in range(attempt):
                # Similar process to write bit value '1' to the GPIO key 'temp_gun_gpio_key_index'
                error_code = self.device.GPIOOUT.write_bit(temp_gun_gpio_key_index, 1)
                time.sleep(0.05)
                if error_code == 0:
                    break
            else:
                return False

        # If all key press and release actions are successful, return True
        return True

    def temp_gun_key_once(self, temp_gun_gpio_key_index, bit, attempt=3):
        """
        Controls a GPIO key on the DAQ device by setting it to a specific bit value.

        Args:
        - temp_gun_gpio_key_index: Index of the GPIO key to be controlled.
        - bit: Bit value to be set for the GPIO key.
        - attempt: Number of attempts to set the bit value (default is 3).

        Returns:
        - True if successfully sets the bit value for the GPIO key within attempts; False otherwise.
        """
        # Controls a GPIO key on the DAQ device by setting it to a specific bit value within attempts
        for i in range(attempt):
            # Attempt to write 'bit' value to the GPIO key 'temp_gun_gpio_key_index'
            error_code = self.device.GPIOOUT.write_bit(temp_gun_gpio_key_index, bit)
            # If successful (error_code = 0), break out of the loop
            if error_code == 0:
                break
        else:
            # If all attempts fail, return False indicating unsuccessful control of the GPIO key
            return False

    def gpio_set(self, commands, attempt=3):
        """
        Executes GPIO commands to set specific GPIO key values.

        Args:
        - commands (str): A string containing multiple GPIO commands separated by ';'.
                          Each command should follow the format 'GPIO_KEY=value'.
        - attempt (int): Number of attempts to execute each GPIO command (default is 3).

        Returns:
        - bool: True if all GPIO commands are successfully executed within attempts; False otherwise.
        """
        # Split the commands string into a list of individual commands
        command_list = commands.split(";")
        for command in command_list:
            # Parse each command
            parts = command.strip().split("=")
            gpio_key, value = parts

            # Extract the GPIO key index and bit value from the command
            gpio_key_index = int(gpio_key[2:])
            bit_value = int(value)

            # Try to write to GPIO
            for i in range(attempt):
                error_code = self.device.GPIOOUT.write_bit(gpio_key_index, bit_value)
                # If the write operation is successful, exit the loop
                if error_code == 0:
                    break
            else:
                # Return False if all attempts fail for any command
                return False

        # Return True if all commands are successfully executed
        return True





