import time
from ctypes import *
import os
import sys

public_path = os.path.normpath(os.path.dirname(os.path.abspath(__file__)) + "/../public")
sys.path.append(public_path)
from lib.common.tools.HW.GPIO.librockmong import *
from lib.common.tools.HW.GPIO.usb_device import *
from lib.common.tools.HW.GPIO.gpio import *
from time import sleep
import logging


class ExtendGpio(object):
    def __init__(self):
        SerialNumbers = (c_int * 20)()
        self.io_count = 16
        ret = UsbDevice_Scan(byref(SerialNumbers))
        if (0 > ret):
            print("Error: %d" % ret)
            exit()
        elif (ret == 0):
            print("No device!")
            exit()
        else:
            for i in range(ret):
                print("Dev%d SN: %d" % (i, SerialNumbers[i]))
        self.sn = SerialNumbers[0]
        self.IO_InitMulti_TxStrut = (IO_InitMulti_TxStruct_t * self.io_count)()
        self.IO_InitMulti_RxStruct = (IO_InitMulti_RxStruct_t * self.io_count)()

    def pin_init_output(self):
        """
        Initializes GPIO pins as output.

        This method sets all available GPIO pins to output mode with a default pull-up/pull-down configuration.

        Returns:
            bool: True if the initialization of pins is successful; False otherwise.
        """
        for i in range(self.io_count):
            self.IO_InitMulti_TxStrut[i].Pin = i
            # Set the pin mode to output
            self.IO_InitMulti_TxStrut[i].Mode = 1
            # Set the pull configuration (0 for none)
            self.IO_InitMulti_TxStrut[i].Pull = 0

        # Initialize GPIO pins as output
        ret = IO_InitMultiPin(self.sn, self.IO_InitMulti_TxStrut, self.IO_InitMulti_RxStruct, self.io_count)
        if ret < 0:
            for i in range(self.io_count):
                logging.info("error: %d" % self.IO_InitMulti_RxStruct[i].Ret)
                # Return False if there's an error in pin initialization
                return False
        else:
            # Return True if pin initialization is successful
            logging.debug("pins init success")
            return True

    def pin_init_input(self):
        """
        Initializes GPIO pins as input.

        This method sets all available GPIO pins to input mode with a default pull-up/pull-down configuration.

        Returns:
            bool: True if the initialization of pins is successful; False otherwise.
        """
        for i in range(self.io_count):
            self.IO_InitMulti_TxStrut[i].Pin = i
            # Set the pin mode to input
            self.IO_InitMulti_TxStrut[i].Mode = 0
            # Set the pull configuration (0 for none)
            self.IO_InitMulti_TxStrut[i].Pull = 0

        # Initialize GPIO pins as input
        ret = IO_InitMultiPin(self.sn, self.IO_InitMulti_TxStrut, self.IO_InitMulti_RxStruct, self.io_count)
        if ret < 0:
            for i in range(self.io_count):
                # Return False if there's an error in pin initialization
                logging.info("error: %d" % self.IO_InitMulti_RxStruct[i].Ret)
                return False
        else:
            # Return True if pin initialization is successful
            logging.debug("pins init success")
            return True

    def gpio_set(self, commands, attempt=3):
        """
        Controls GPIO pins based on the provided commands.

        Args:
            commands (str): A string containing GPIO control commands separated by ';'.
            attempt (int, optional): The number of attempts for each pin control. Defaults to 3.

        Returns:
            bool: True if all pin control operations are successful; False otherwise.
        """
        # Split commands by ';'
        command_list = commands.split(";")
        for command in command_list:
            parts = command.split("=")
            # Ensure correct command format
            if len(parts) == 2 and parts[0].startswith("P"):
                # Get the pin index
                pin_index = int(parts[0][1:])
                # Get the logic level (0 or 1)
                level = int(parts[1])

                for i in range(attempt):
                    ret = IO_WritePin(self.sn, pin_index, level)
                    if ret < 0:
                        logging.debug(f"Error controlling pin {pin_index}, attempt {i + 1}")
                    else:
                        break
                else:
                    # Return False if unable to control the pin after attempts
                    logging.debug(f"Failed to control pin {pin_index} after {attempt} attempts")
                    return False
        # Return True if all pin control operations are successful
        return True

    def key_high_low_change(self, pin_index, attempt=3):
        """
        Controls the state of a specific GPIO pin by alternating its level from high to low and vice versa.

        Args:
            pin_index (int): The index of the GPIO pin to be controlled.
            attempt (int, optional): The number of attempts for each pin control. Defaults to 3.

        Returns:
            None
        """
        # Lower the pin to '0' state and retry 'attempt' times
        for i in range(attempt):
            ret = IO_WritePin(self.sn, pin_index, 0)
            if ret < 0:
                logging.debug(f"Error controlling pin {pin_index}, attempt {i + 1}")
            else:
                break
        else:
            logging.debug(f"Failed to control pin {pin_index} after {attempt} attempts")

        time.sleep(0.05)
        # Raise the pin to '1' state and retry 'attempt' times
        for i in range(attempt):
            ret = IO_WritePin(self.sn, pin_index, 1)
            if ret < 0:
                logging.debug(f"Error controlling pin {pin_index}, attempt {i + 1}")
            else:
                break
        else:
            logging.debug(f"Failed to control pin {pin_index} after {attempt} attempts")

    def mux32_id(self, decimal_value, io_count):
        """
        Sets the states of multiple GPIO pins based on a given decimal value in a 32-bit configuration.

        Args:
            decimal_value (int): The decimal value to be converted into binary and distributed across GPIO pins.
            io_count (int): The number of GPIO pins to be controlled for the 32-bit configuration.

        Returns:
            bool: True if GPIO pin control is successful, False otherwise.
        """
        # Convert the decimal value to a binary string and fill it to the specified length
        binary_string = bin(decimal_value)[2:].zfill(io_count)

        # Reverse the binary string to align with GPIO pin index
        binary_string = binary_string[::-1]

        # Define structures for transmitting and receiving GPIO pin states
        IO_WriteMulti_TxStruct = (IO_WriteMulti_TxStruct_t * io_count)()
        IO_WriteMulti_RxStruct = (IO_WriteMulti_RxStruct_t * io_count)()

        # Set GPIO pin states based on the binary string
        for i, bit in enumerate(binary_string):
            IO_WriteMulti_TxStruct[i].Pin = i
            IO_WriteMulti_TxStruct[i].PinState = int(bit)

        # Control GPIO pins using the specified configuration
        ret = IO_WriteMultiPin(self.sn, IO_WriteMulti_TxStruct, IO_WriteMulti_RxStruct, io_count)

        # Check for errors and return the result
        if ret < 0:
            for i in range(io_count):
                logging.info("error: %d" % IO_WriteMulti_RxStruct[i].Ret)
                return False
        else:
            return True


# if __name__ == "__main__":
#     gpio = ExtendGpio()
#     # gpio.pin_init_output()
#     # gpio.key_high_low_change(4)
#     gpio.gpio_set("P4=0")
#     time.sleep(0.03)
#     gpio.gpio_set("P4=1")
