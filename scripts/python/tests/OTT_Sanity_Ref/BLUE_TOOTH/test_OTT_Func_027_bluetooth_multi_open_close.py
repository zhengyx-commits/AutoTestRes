import logging
import time

import pytest

from . import btTest


@pytest.fixture(scope="module", autouse=True)
def setup_teardown():
    yield
    logging.info("close bt")
    btTest.checkoutput(btTest.CLOSE_BLUETOOTH_COMMAND)


@pytest.mark.parametrize("status", ["OFF", "ON"] * 5)
def test_027_bt_status(status):
    if status == "OFF":
        btTest.checkoutput(btTest.CLOSE_BLUETOOTH_COMMAND)
    else:
        btTest.checkoutput(btTest.OPEN_BLUETOOTH_COMMAND)

    time.sleep(5)
    assert btTest.get_bluetooth_status() == (status == "ON"), f"Bluetooth status not {status}"


