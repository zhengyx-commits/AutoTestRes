#!/usr/bin/env python
#
# Copyright 2020 Amlogic.com, Inc. or its affiliates. All rights reserved.
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

from util.errors import Errors


class AATSRuntimeError(RuntimeError):
    pass


"""AATSSTarget Exceptions"""


class AATSDeviceNotFoundError(Errors.DeviceUnavailableError):
    pass


class AATSTimeoutException(AATSRuntimeError):
    pass


class AATSInvalidTestPathException(AATSRuntimeError):
    """
    Raised when the given test path does not exist
    """
    pass


class AATSBinaryMissingError(AATSRuntimeError):
    """
    Raised when "device_check" CLI is missing
    """
    pass


"""CLI Exceptions"""


class CLIEndpointNotAvailableError(Errors.CLINotFoundError):
    """
    Raised when the requested CLI endpoint is not available in the device
    target
    """
    pass


class MultiPlayerRuntimeError(RuntimeError):
    pass


class MultiPlayerDeviceNotFoundError(Errors.DeviceUnavailableError):
    pass


class MultiPlayerAdbServerRestartedException(MultiPlayerRuntimeError):
    """
    Raised when a ping response indicates the device restarted during
    the execution of an endpoint. Usually means a stackoverflow or segfault
    ocurred.
    """
    pass


class MultiPlayerDeviceSignatureNotFoundException(MultiPlayerRuntimeError):
    pass


class MultiPlayerSignaturePemPk8NotFoundException(MultiPlayerRuntimeError):
    pass


class BroadlinkRm3RuntimeError(RuntimeError):
    pass


class BroadlinkRm3DeviceNotFoundError(Errors.DeviceUnavailableError):
    pass
