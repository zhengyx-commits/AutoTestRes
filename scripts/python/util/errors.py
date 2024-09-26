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

import inspect

SETUP = "[AATS_{}_ERR]: "


class AATSClassNotImplementedError(Exception):
    """
    To be raised when any Base class is used directly, instead of being extended.
    """
    MSG = " is an abstract base class. This class is not intended to be used directly. " \
          "Please extend with a user-friendly class name and message!"

    def __init__(self):
        caller = inspect.stack()[1][0].f_locals["self"].__class__.__name__
        super().__init__(caller + self.MSG)


class Errors:
    """
    This is the container class for common errors file. This class is instantiated and set as an attribute to the
    pytest module to be shared across tests and inside of the framework.

    Usage:
        raise pytest.errors.WifiError("Unable to connect to wifi using SSID: {}.".format(ssid))
        and
        import pytest
        class AuxillaryTVUnavailable(pytest.errors.DeviceUnavailableError):
            pass
        or
        from errors import Errors
        class AuxillaryTVUnavailable(Errors.BaseEnvironmentError):
            pass

        raise AuxillaryTVUnavailable("Unable to receive ping from {}! Please check IR blaster!".format(TV.ip_address)
    """

    class BaseAATSError(Exception):
        """
        All Base classes should be derived from this base class. This is the foundation that allows str(error) calls
        to be printed with the same behavior (printing the error name) as when it is raised itself. This is
        necessary for carrying the Error name over when someone catches an exception and calls pytest.fail(str(error))
        in order to provide key metrics for specific errors reported by test results.
        """

        def __init__(self, message):
            if self.__class__.__name__ == "BaseAATSError":
                raise AATSClassNotImplementedError()
            super().__init__(message)

        def __get_mro(self):
            return str(inspect.getmro(self.__class__)[0]).replace("'", "").replace("<class ", "").replace(">", "")

        def __str__(self):
            caller = inspect.stack()[1].function

            if caller == '_some_str':  # if caller is "raise" or error is "raised", do what you normally do
                return str(self.args[0])

            return self.__get_mro() + ': ' + self.args[0]  # if str() called on instance after raise, mimic raise

    """ ****** Lab Stakeholder ****** """

    class BaseEnvironmentError(BaseAATSError):
        """
        This is a base class to be extended as appropriate. This base class is used to associate failures with that
        occur inside the lab environment. If you try to instantiate this error directly, it will result in a
        NotImplementedError being raised.
        """

        def __init__(self, message):
            if self.__class__.__name__ == "BaseEnvironmentError":
                raise AATSClassNotImplementedError()

            self.message = SETUP.format("ENV") + message
            super().__init__(self.message)

    class DeviceUnavailableError(BaseEnvironmentError):
        """
        If a device is unreachable over any protocol, this error should be used.
        """
        pass

    class AuxiliaryDeviceError(BaseEnvironmentError):
        """
        This should be used as a base class is for specific Auxiliary device (used as a dependency)
        has an error.
        """
        pass

    # Start Connectivity Errors
    class ConnectivityError(BaseEnvironmentError):
        """
        Base Class for Connectivity Errors. This should be used for any type of WiFi or BT error. Best if extended to
        a more specific error type.
        """

        def __init__(self, message):
            self.message = SETUP.format("CONN") + message
            super().__init__(self.message)

    class WifiError(ConnectivityError):
        """Error for Wifi."""
        pass

    class WifiDisabledException(WifiError):
        """Raised when the wpa supplicant is not running"""
        pass

    """ ****** Framework Stakeholder ****** """

    class BaseFrameworkError(BaseAATSError):
        """
        This is a base class to be extended as appropriate. This base class is used to associate failures that occur
        inside of the framework. This is primarily used by the Framework Developers to indicate a problem occuring at
        the framework level. If you try to instantiate this error directly, it will result in a 'NotImplementedError'
        being raised.
        """

        def __init__(self, message):
            if self.__class__.__name__ == "BaseFrameworkError":
                raise AATSClassNotImplementedError()

            self.message = SETUP.format("FWK") + message
            super().__init__(self.message)

    class ResultParserError(BaseFrameworkError):
        """
        To be used for the framework result parser logic.
        """
        pass

    class CLINotFoundError(BaseFrameworkError):
        """
        To be used when CLI is not found, but should be there.
        """
        pass

    """ ****** QA Stakeholder ****** """

    class BaseTestError(BaseAATSError):
        """
        This is a base class to be extended as appropriate. This base class is used to associate failures with that
        occur due to an error in associated with the QA role. If you try to instantiate this error directly, it will
        result in a 'NotImplementedError' being raised.
        """

        def __init__(self, message):
            if self.__class__.__name__ == "BaseTestError":
                raise AATSClassNotImplementedError()

            self.message = SETUP.format("QA") + message
            super().__init__(self.message)

    class DeviceNotProvisionedError(BaseTestError):
        """
        This indicates an error due to a lack of provisioning needing to be done on the device. This specifically
        is used for these types of issues where the QA is responsible for provisioning the device. If Lab is proper
        stakeholder, please extend the BaseEnvironmentError and use there.
        """
        pass

    class TaskConfigError(BaseTestError):
        """
        To be used when a config that is a necessary test dependency is missing. Every test should be evaluating the
        proper keys are present, and raising this error if anything is missing.
        """
        pass

    class RemoteServiceUnavailableError(BaseTestError):
        """
        This is for external dependencies. For instance, if you're depending on a remote service callback from a
        registration API, if the registration API is down, this will inform QA that there was an issue with this
        service at this point in time. Timestamp and address would be great to have as well in the message.
        """
        pass

    class RegistrationError(BaseTestError):
        """
        Due to the high volume of registration errors, this is defined to go to the QA first for validation.
        """

        def __init__(self, message):
            self.message = SETUP.format("REGISTRATION") + message
            super().__init__(self.message)

    class DeregistrationError(RegistrationError):
        """
        Due to the high volume of de-registration errors, this is defined to go to the QA first for validation.
        """
        pass
