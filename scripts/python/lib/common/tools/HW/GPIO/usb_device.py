#-*- coding: utf-8 -*-
from ctypes import *
import platform
from lib.common.tools.HW.GPIO.librockmong import *


def UsbDevice_Scan(SerialNumbers):
    """
    Scans for USB devices and retrieves information about connected devices.

    Args:
    - SerialNumbers: A parameter to receive the serial numbers of detected USB devices.

    Returns:
    - If the return value is greater than 0, it indicates the number of detected devices.
    - If it equals 0, it means no device is currently inserted.
    - If it's less than 0, it indicates an error occurred during the scan.
    """
    return librockmong.UsbDevice_Scan(SerialNumbers)