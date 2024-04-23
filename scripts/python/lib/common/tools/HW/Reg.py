import logging
import sys

import pandas as pd
import serial
import time
import re


class Reg:
    def __init__(self, serial=""):
        self.serial = serial

    def process(self, row, command_type, command_value, mode):
        """
        Processes the given command_type and command_value.

        Args:
            row (pd.Series): DataFrame row.
            command_type (str): Type of command.
            command_value (str): Value of the command.

        Returns:
            tuple: A tuple containing the read_command and set_command strings if command_value is provided,
                   otherwise only returns the read_command string.
        """
        # Retrieve address and bit information from the DataFrame row
        address = row[f"{command_type}_address"]
        bit = row[f"{command_type}_bit"]
        bit = str(bit)

        # Generate the read command
        if mode == "uboot":
            read_command = f"md {address} 1"
        else:
            read_command = f"echo {address} > /sys/kernel/debug/aml_reg/paddr;cat {address} > /sys/kernel/debug/aml_reg/paddr"
        logging.info(read_command)

        # Get hexadecimal value from the serial port based on the read command
        if mode == "uboot":
            hex_value_from_serial = self.serial.getprop_node_value(read_command, r'(?<!: )[0-9a-fA-F]+$')
        else:
            self.serial.write(read_command.strip(";")[0])
            hex_value_from_serial = self.serial.getprop_node_value(read_command.strip(";")[1], r'=\s*(\S+)')
        print(hex_value_from_serial)

        if command_value is None:
            # If no command_value provided, return the read_command only
            bit_value = self.get_bit_value(hex_value_from_serial, bit)
            logging.info(bit_value)
            return bit_value

        # Set the bits using the retrieved values
        set_value = self.set_bits(hex_value_from_serial, bit, command_value)

        # Generate the set command
        if mode == "uboot":
            set_command = f"mw {address} {set_value}"
        else:
            set_command = f"echo {address} {set_value} > /sys/kernel/debug/aml_reg/paddr"
        assert self.serial.execute_commands(set_command), "mw/set fail"
        return set_command

    def get_bit_value(self, hex_string, bit_position):
        """
        Retrieves the value of a specific bit at the given position in a hexadecimal string.

        Args:
            hex_string (str): Hexadecimal string.
            bit_position (str): Position of the bit to retrieve.

        Returns:
            int: Value (0 or 1) of the specified bit position.
        """
        # Convert the hexadecimal string to the corresponding decimal integer
        decimal_value = int(hex_string, 16)

        # Convert the bit_position to an integer
        bit_position = int(float(bit_position))

        # Calculate the value of the specified bit position using bitwise operations
        bit_value = (decimal_value >> bit_position) & 1

        return bit_value

    def set_bits(self, value, set_bit_start_end, set_bit_value):
        """
        Sets specific bits in the given hexadecimal value to the specified value.

        Args:
            value (str): Hexadecimal value as a string.
            set_bit_start_end (str): Bit or bit range (start:end) to be set.
            set_bit_value (str): Value to set at the specified bits.

        Returns:
            str: Hexadecimal string after setting the bits to the new value.
        """
        # Convert the string representation of the hexadecimal value to an integer
        value = int(value, 16)
        set_bit_value = int(set_bit_value)

        # Convert the string representation of the start/end bits to integers
        if ":" not in set_bit_start_end:
            bit = int(float(set_bit_start_end))
            # Generate the mask for the bit to be set
            mask = 1 << bit

            # Clear the specified bit in the original value and set it to the new value using bitwise operations
            new_value = hex((value & ~mask) | (set_bit_value << bit))
        else:
            bit_end, bit_start = map(int, set_bit_start_end.split(':'))

            # Generate the mask for the bit range to be set
            mask = (2 ** (bit_end - bit_start + 1) - 1) << bit_start

            # Clear the specified bit range in the original value and set it to the new value using bitwise operations
            new_value = hex((value & ~mask) | (set_bit_value << bit_start))

        return new_value

    def execute(self, dataframe, commands_dict, mode):
        """
        Processes commands for each item in the DataFrame and generates a DataFrame containing the results.

        Args:
            dataframe (pandas.DataFrame): DataFrame containing pin information.
            commands_dict (dict): Dictionary with pin names as keys and commands as values.

        Returns:
            None
        """
        read_bit = None
        # Initialize an empty dictionary to store generated commands
        generated_command_dict = {}

        # Iterate through each key-value pair in the commands dictionary
        for key, commands in commands_dict.items():
            gpio_key = key.split()[0]
            # Find the index of the pin in the DataFrame
            index = dataframe[dataframe['Pin_Name'] == gpio_key].index[0]
            command_list = commands.split(';')
            generated_command_list = []

            # Process each command for the current pin
            for command in command_list:
                command = command.strip()
                command_parts = command.split('=')
                # Check if command contains '=' for setting
                if len(command_parts) == 2:
                    command_type = command_parts[0]
                    command_value = command_parts[1]
                    generated_command = self.process(dataframe.iloc[index], command_type, command_value, mode)
                else:
                    # If no '=', treat as a read command
                    command_type = command
                    generated_command = self.process(dataframe.iloc[index], command_type, None, mode)
                    read_bit = generated_command
                generated_command_list.append(generated_command)

            # Store the list of generated commands for the current pin in the dictionary
            generated_command_dict[key] = generated_command_list

        # Convert the generated command dictionary to a DataFrame
        df_generated_commands = pd.DataFrame(generated_command_dict.items(),
                                             columns=['pin_name', 'generated_command'])

        # Write the DataFrame to an Excel file
        df_generated_commands.to_excel('generated_command.xlsx', index=False)

        return read_bit