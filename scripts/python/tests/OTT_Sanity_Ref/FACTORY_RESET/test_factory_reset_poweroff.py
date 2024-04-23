import allure
from tests.OTT_Sanity_Ref.FACTORY_RESET import *
import subprocess


@pytest.fixture(scope='function', autouse=True)
def multi_teardown():
    yield
    pass_oobe()


@allure.step("Start factory reset and power off after some time")
def test_factory_reset_poweroff():
    logging.info("enter factory reset")
    adb.root()
    adb.shell('am broadcast -p "android" --receiver-foreground -a android.intent.action.FACTORY_RESET')
    powerRelay_bin_path = get_powerRelay_path()
    time.sleep(20)
    logging.info(f"Power OFF")
    subprocess.run([f"{powerRelay_bin_path}powerRelay", p_conf_power_symlink, "1", "off"])
    time.sleep(2)
    logging.info(f"Power ON")
    subprocess.run([f"{powerRelay_bin_path}powerRelay", p_conf_power_symlink, "1", "on"])
    assert wait_boot_complete()
