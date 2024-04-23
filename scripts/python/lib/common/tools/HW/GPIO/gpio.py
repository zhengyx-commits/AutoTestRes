#-*- coding: utf-8 -*-
from ctypes import *
import platform
from lib.common.tools.HW.GPIO.librockmong import *


# Initializes the working mode of the pin.
# SerialNumber: Device serial number.
# Pin: Pin number. 0 for P0, 1 for P1, and so on.
# Mode: Input/output mode. 0 for input, 1 for output, 2 for open-drain.
# Pull: Pull-up/pull-down resistor. 0 for none, 1 for enabling internal pull-up, 2 for enabling internal pull-down.
# Returns: 0 for normal, <0 for exception.
def IO_InitPin(SerialNumber, Pin, Mode, Pull):
    return librockmong.IO_InitPin(SerialNumber, Pin, Mode, Pull)


# Reads the state of the pin.
# SerialNumber: Device serial number.
# Pin: Pin number. 0 for P0, 1 for P1, and so on.
# PinState: Returns the pin state. 0 for low level, 1 for high level.
# Returns: 0 for normal, <0 for exception.
def IO_ReadPin(SerialNumber, Pin, PinState):
    return librockmong.IO_ReadPin(SerialNumber, Pin, PinState)


# Controls the output state of the pin.
# SerialNumber: Device serial number.
# Pin: Pin number. 0 for P0, 1 for P1, and so on.
# PinState: Pin state. 0 for low level, 1 for high level.
# Returns: 0 for normal, <0 for exception.
def IO_WritePin(SerialNumber, Pin, PinState):
    return librockmong.IO_WritePin(SerialNumber, Pin, PinState)


class IO_InitMulti_TxStruct_t(Structure):
    _fields_ = [
        ("Pin", c_ubyte),   # Pin number
        ("Mode", c_ubyte),  # Mode: 0 for input, 1 for output
        ("Pull", c_ubyte)
    ]


class IO_InitMulti_RxStruct_t(Structure):
    _fields_ = [
        ("Ret", c_ubyte),   # Return
    ]


def IO_InitMultiPin(SerialNumber, TxStruct, RxStruct, Number):
    return librockmong.IO_InitMultiPin(SerialNumber, TxStruct, RxStruct, Number)


class IO_ReadMulti_TxStruct_t(Structure):
    _fields_ = [
        ("Pin", c_ubyte),   # Pin number
    ]


class IO_ReadMulti_RxStruct_t(Structure):
    _fields_ = [
        ("Ret", c_ubyte),		# Return
        ("PinState", c_ubyte),  # Pin state
    ]


def IO_ReadMultiPin(SerialNumber, TxStruct, RxStruct, Number):
    return librockmong.IO_ReadMultiPin(SerialNumber, TxStruct, RxStruct, Number)


class IO_WriteMulti_TxStruct_t(Structure):
    _fields_ = [
        ("Pin", c_ubyte),		# Pin number
        ("PinState", c_ubyte),  # Pin state
    ]


class IO_WriteMulti_RxStruct_t(Structure):
    _fields_ = [
        ("Ret", c_ubyte),  # Return
    ]


def IO_WriteMultiPin(SerialNumber, TxStruct, RxStruct, Number):
    return librockmong.IO_WriteMultiPin(SerialNumber, TxStruct, RxStruct, Number)
