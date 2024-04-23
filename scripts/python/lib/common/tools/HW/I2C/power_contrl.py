import ctypes
import logging
import time
from ctypes import *

Dir_USB2UARTSPIIICDLL = "/home/amlogic/AutoTestRes/scripts/python/lib/common/tools/HW/I2C/libUSB2UARTSPIIIC.so"


class PowerCtl(object):

    def __init__(self, usb_index=0):
        # Import the dynamic link library
        self.I2cDriver_dll_Usb = ctypes.CDLL(Dir_USB2UARTSPIIICDLL)
        self.usb_index = usb_index

        # Open the port
        if self.I2cDriver_dll_Usb.OpenUsb(ctypes.c_int(self.usb_index)) == 0:
            logging.debug("open port success")

        # Configure parameters
        if self.I2cDriver_dll_Usb.ConfigIICParam(ctypes.c_uint(100000), ctypes.c_uint(10000), ctypes.c_uint(self.usb_index)) == 0:
            logging.debug("config success")

        time.sleep(1)

    def rn5t567_set_dcdc_voltage(self, idx, uV):
        """
        Sets the DC-DC voltage for a specific index.

        Args:
            self: Instance of the PowerCtl class.
            idx (int): Index representing the specific DC-DC setting.
            uV (int): Desired voltage value in microvolts (μV).

        Returns:
            bool: Returns True if the voltage is successfully set, otherwise returns False.

        This function sets the DC-DC voltage at the given index to the desired microvolt value.
        It checks the validity of the voltage range and calculates the appropriate value (tmp_val) for the voltage.
        If the voltage is within the valid range, it writes the calculated tmp_val to the device
        at address 0x35 + idx using the 'rn5t618_write' method.
        Returns True to indicate successful setting of the DC-DC voltage or False if the operation fails.
        """
        tmp_val = 0

        if 600000 <= uV < 3800000:
            tmp_val = (uV - 600000) // 12500
        else:
            logging.info("EOVERFLOW")
            return False

        if self.rn5t618_write(0x35 + idx, tmp_val) < 0:
            logging.info("set dcdc fail")
            return False

        return True

    def rn5t567_set_ldo_voltage(self, idx, uV):
        """
        Sets the LDO (Low Drop-Out) voltage for a specific index.

        Args:
            self: Instance of the PowerCtl class.
            idx (int): Index representing the specific LDO setting.
            uV (int): Desired voltage value in microvolts (μV).

        Returns:
            bool: Returns True if the voltage is successfully set, otherwise returns False.

        This function sets the LDO voltage at the given index to the desired microvolt value.
        It checks the validity of the voltage range based on the specified LDO index (idx).
        If the voltage is within the valid range, it calculates the appropriate value (tmp_val) for the voltage.
        Then, it writes the calculated tmp_val to the device at address 0x4B + idx using 'rn5t618_write'.
        Returns True to indicate successful setting of the LDO voltage or False if the operation fails.
        """
        tmp_val = 0

        if idx == 3:
            if uV < 600000 or uV > 3500000:
                logging.info("Beyond voltage range")
                return False
            else:
                tmp_val = ((uV - 600000) // 50000) * 2
        else:
            if uV < 900000 or uV > 3500000:
                logging.info("Beyond voltage range")
                return False
            else:
                tmp_val = ((uV - 900000) // 50000) * 2

        if self.rn5t618_write(0x4B + idx, tmp_val) < 0:
            return False

        return True

    def rn5t618_write(self, add, val):
        """
        Writes a value to a specific address in the device.

        Args:
            self: Instance of the PowerCtl class.
            add (int): Address to write the value to.
            val (int): Value to be written at the given address.

        Returns:
            int: Returns the status indicating the success (positive value) or failure (negative value) of the write operation.

        This function writes a value (val) to the specified address (add) in the device.
        It first masks the address (add) and value (val) to ensure they are within 8-bit range.
        Then, it creates character buffer arrays 'regBuf' and 'sendBuf' of length 1 to store the address and value as bytes.
        It uses 'IICRegisterSend' function from the external DLL to send the address and value to the device.
        If the write operation is successful, it returns a positive value, otherwise, it returns a negative value.
        """
        # Ensure the address is within the 8-bit range
        add = add & 0xFF
        # Ensure the value is within the 8-bit range
        val = val & 0xFF

        # Create character buffer arrays of length 1 to store address and value as bytes
        regBuf = (c_char * 1)()
        # Convert 'add' to bytes and store it in 'regBuf'
        regBuf[0] = add.to_bytes(1, byteorder='big')

        sendBuf = (c_char * 1)()
        # Convert 'val' to bytes and store it in 'sendBuf'
        sendBuf[0] = val.to_bytes(1, byteorder='big')  # 将 val 转换为字节并存储在 sendBuf 中

        ret = self.I2cDriver_dll_Usb.IICRegisterSend(c_ubyte(0), c_uint(0x32), regBuf, sendBuf, c_ubyte(1), c_uint(1), c_uint(self.usb_index))
        if ret >= 0:
            logging.debug("success")

        return ret

    def rn5t567_get_ldo_voltage(self, idx):
        """
        Retrieves the LDO (Low Drop-Out) voltage value for a specific index.

        Args:
            self: Instance of the PowerCtl class.
            idx (int): Index representing the specific LDO setting.

        Returns:
            int or None: Returns the LDO voltage value in microvolts (μV) if successful,
                         returns None if the read operation fails.

        This function retrieves the LDO voltage value at the given index from the device.
        It reads data from the device at address 0x4B + idx using 'rn5t618_read' method
        and stores the value in 'tmp_val' variable as bytes.
        If 'tmp_val' is not None (indicating successful read), it converts 'tmp_val' to an integer.
        Based on the index (idx), it calculates the voltage (uV) using specific formulas.
        Returns the calculated LDO voltage value in microvolts (μV) if successful,
        otherwise logs an error message and returns None to indicate read failure.
        """
        tmp_val = None
        uV = None

        tmp_val = self.rn5t618_read(0x4B + idx)
        if tmp_val:
            tmp_val = int.from_bytes(tmp_val, byteorder='big')
            if idx == 3:
                if tmp_val > 0x74:
                    uV = 0
                else:
                    uV = 600000 + (tmp_val // 2) * 50000
            else:
                if tmp_val > 0x68:
                    uV = 0
                else:
                    uV = 900000 + (tmp_val // 2) * 50000  # 50mv 2 steps
        else:
            logging.info("read fail")

        return uV

    def rn5t567_get_dcdc_voltage(self, idx):
        """
        Retrieves the DC-DC voltage value for a specific index.

        Args:
            self: Instance of the PowerCtl class.
            idx (int): Index representing the specific DC-DC setting.

        Returns:
            int or None: Returns the DC-DC voltage value in microvolts (μV) if successful,
                         returns None if the read operation fails.

        This function retrieves the DC-DC voltage value at the given index from the device.
        It reads data from the device at address 0x35 + idx using the 'rn5t618_read' method
        and stores the value in 'tmp_val' variable as bytes.
        If 'tmp_val' is not None (indicating a successful read), it converts 'tmp_val' to an integer.
        Calculates the voltage (uV) using the formula (uV = 600000 + tmp_val * 12500) where each step represents 12.5mV.
        Returns the calculated DC-DC voltage value in microvolts (μV) if successful,
        otherwise logs an error message and returns None to indicate read failure.
        """
        tmp_val = None
        uV = None

        tmp_val = self.rn5t618_read(0x35 + idx)
        if tmp_val:
            tmp_val = int.from_bytes(tmp_val, byteorder='big')
            uV = 600000 + tmp_val * 12500  # 12.5mv per step
        else:
            logging.info("read fail")

        return uV

    def rn5t618_read(self, add):
        """
        Reads a value from a specific address in the device.

        Args:
            self: Instance of the PowerCtl class.
            add (int): Address to read the value from.

        Returns:
            bytes or None: Returns the value read from the specified address as bytes.
                           Returns None if the read operation fails.

        This function reads a value from the specified address (add) in the device.
        It first ensures that the address is within the 8-bit range by masking with 0xFF.
        Then, it initializes character buffer arrays 'regBuf' and 'rcvBuf' of length 1.
        Stores the address (converted to bytes) in 'regBuf' and initializes 'rcvBuf' with b"\x00".
        Uses 'IICRegisterRead' function from the external DLL to read data from the specified address.
        If the read operation is successful (ret >= 0), it retrieves the value from 'rcvBuf' and returns it as bytes.
        Otherwise, it logs an error message and returns None to indicate the read operation failed.
        """
        # Ensure the address is within the 8-bit range
        add = add & 0xFF

        # Initialize val to None
        val = None

        # Create a character buffer array of length 1
        regBuf = (c_char * 1)()
        # Convert 'add' to bytes and store it in 'regBuf'
        regBuf[0] = add.to_bytes(1, byteorder='big')

        # Create a character buffer array of length 1
        rcvBuf = (c_char * 1)()
        # Initialize the receive buffer with b"\x00"
        rcvBuf[0] = b"\x00"

        # Read data from the specified address using 'IICRegisterRead' function
        ret = self.I2cDriver_dll_Usb.IICRegisterRead(c_ubyte(0), c_uint(0x32), regBuf, rcvBuf, c_ubyte(1), c_uint(1), c_uint(self.usb_index))
        if ret >= 0:
            # Retrieve the value from 'rcvBuf' and store it in 'val'
            val = rcvBuf[0]
        else:
            logging.info("rn5t618 read fail")

        return val

    def rn5t567_set_dcdc_status(self, idx, status):
        """
        Sets the DC-DC status for a specific index.

        Args:
            self: Instance of the PowerCtl class.
            idx (int): Index representing the specific DC-DC setting.
            status (int): Status value (0 or 1) to set for the DC-DC.

        Returns:
            bool: Returns True if the status is successfully set, otherwise returns False.

        This function sets the status (enable/disable) for the DC-DC at the given index.
        It reads the original value (org_val) from the device at address 0x2A + idx * 2 using 'rn5t618_read'.
        If 'org_val' is not None (indicating a successful read), it converts 'org_val' to an integer.
        Based on the specified 'status' parameter, it calculates the new value (new_val) to be written.
        Writes the calculated 'new_val' to the device at address 0x2A + idx * 2 using 'rn5t618_write'.
        If the write operation fails, it logs an error message and returns False.
        Returns True to indicate successful setting of the DC-DC status or False if the operation fails.
        """
        org_val = None
        org_val = self.rn5t618_read(0x2A + idx * 2)
        if org_val:
            org_val = int.from_bytes(org_val, byteorder='big')
            if status == 0:
                new_val = org_val & (~0x01)
            else:
                new_val = org_val | 0x01
            if self.rn5t618_write(0x2A + idx * 2, new_val) < 0:
                logging.info("rn5t618 set dcdc status fail")
                return False
        else:
            logging.info("rn5t618 read fail")
            return False

        return True

    def rn5t567_set_ldo_status(self, idx, status):
        """
        Sets the LDO (Low Drop-Out) status for a specific index.

        Args:
            self: Instance of the PowerCtl class.
            idx (int): Index representing the specific LDO setting.
            status (int): Status value (0 or 1) to set for the LDO.

        Returns:
            bool: Returns True if the status is successfully set, otherwise returns False.

        This function sets the status (enable/disable) for the LDO at the given index.
        It reads the original value (org_val) from the device at address 0x44 using 'rn5t618_read'.
        If 'org_val' is not None (indicating a successful read), it converts 'org_val' to an integer.
        Based on the specified 'status' parameter, it calculates the new value (new_val) to be written.
        Writes the calculated 'new_val' to the device at address 0x44 using 'rn5t618_write'.
        If the write operation fails, it logs an error message and returns False.
        Returns True to indicate successful setting of the LDO status or False if the operation fails.
        """
        org_val = None
        org_val = self.rn5t618_read(0x44)
        if org_val:
            org_val = int.from_bytes(org_val, byteorder='big')
            if status == 0:
                new_val = org_val & (~(0x01 << (idx - 1)))
            else:
                new_val = org_val | (0x01 << (idx - 1))
            if self.rn5t618_write(0x44, new_val) < 0:
                logging.info("rn5t618 set ldo status fail")
                return False
        else:
            logging.info("rn5t618 read fail")
            return False

        return True

    def rn5t567_get_dcdc_status(self, idx):
        """
        Retrieves the status of the DC-DC for a specific index.

        Args:
            self: Instance of the PowerCtl class.
            idx (int): Index representing the specific DC-DC setting.

        Returns:
            int or bool: Returns the status of the DC-DC (1 for enabled, 0 for disabled) if successful,
                         returns False if the read operation fails.

        This function retrieves the status (enabled or disabled) for the DC-DC at the given index.
        It reads data from the device at address 0x2A + idx * 2 using 'rn5t618_read' method
        and stores the value in 'tmp_val' variable as bytes.
        If 'tmp_val' is not None (indicating a successful read), it converts 'tmp_val' to an integer.
        Determines the status of the DC-DC based on the least significant bit (LSB) of 'tmp_val'.
        Returns the status of the DC-DC (1 for enabled, 0 for disabled) if successful,
        otherwise logs an error message and returns False to indicate read failure.
        """
        tmp_val = None
        tmp_val = self.rn5t618_read(0x2A + idx * 2)
        if tmp_val:
            tmp_val = int.from_bytes(tmp_val, byteorder='big')
            status = 1 if tmp_val & 0x01 else 0
        else:
            logging.info("rn5t618 read fail")
            return False

        return status

    def rn5t567_get_ldo_status(self, idx):
        """
        Retrieves the status of the LDO (Low Drop-Out) for a specific index.

        Args:
            self: Instance of the PowerCtl class.
            idx (int): Index representing the specific LDO setting.

        Returns:
            int or bool: Returns the status of the LDO (1 for enabled, 0 for disabled) if successful,
                         returns False if the read operation fails.

        This function retrieves the status (enabled or disabled) for the LDO at the given index.
        It reads data from the device at address 0x44 using 'rn5t618_read' method
        and stores the value in 'tmp_val' variable as bytes.
        If 'tmp_val' is not None (indicating a successful read), it converts 'tmp_val' to an integer.
        Determines the status of the LDO based on the bit corresponding to the given 'idx'.
        Returns the status of the LDO (1 for enabled, 0 for disabled) if successful,
        otherwise logs an error message and returns False to indicate read failure.
        """
        tmp_val = None
        tmp_val = self.rn5t618_read(0x44)
        if tmp_val:
            tmp_val = int.from_bytes(tmp_val, byteorder='big')
            status = 1 if tmp_val & (0x01 << (idx - 1)) else 0
        else:
            logging.info("rn5t618 read fail")
            return False

        return status

    def iO_set(self, index, bit):
        """
        Set a specific bit in the I/O port.

        Args:
        - index (int): The index of the I/O port.
        - bit (int): The bit value to be set (0 or 1).

        Returns:
        - bool: True if the I/O set operation is successful, False otherwise.
        """
        ret = self.I2cDriver_dll_Usb.IOSetAndRead(c_uint(index), c_uint(1), c_uint(bit), c_uint(self.usb_index))
        if ret == bit:
            logging.debug("io set success")
            return True
        else:
            logging.info("io set fail")
            return False

    def iO_read(self, index, bit):
        """
        Read the value of a specific bit in the I/O port.

        Args:
        - index (int): The index of the I/O port.
        - bit (int): The expected bit value (0 or 1).

        Returns:
        - bool: True if the read operation matches the expected bit value, False otherwise.
        """
        ret = self.I2cDriver_dll_Usb.IOSetAndRead(c_uint(index), c_uint(0), c_uint(bit), c_uint(self.usb_index))
        if ret == bit:
            logging.debug("io read success")
            return True
        else:
            logging.info("io read fail")
            return False