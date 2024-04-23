import time
import pytest
import allure
from tests.OTT_Sanity_Ref.FACTORY_RESET import *
import subprocess


# @pytest.mark.skip
@pytest.fixture(scope='function', autouse=True)
def multi_teardown():
    yield
    pass_oobe()


# @pytest.mark.skip
@allure.step("Start factory reset")
def test_factory_reset():
    logging.info("enter factory reset")
    adb.root()
    adb.shell('am broadcast -p "android" --receiver-foreground -a android.intent.action.FACTORY_RESET')
    time.sleep(60)
    wait_boot_complete()



