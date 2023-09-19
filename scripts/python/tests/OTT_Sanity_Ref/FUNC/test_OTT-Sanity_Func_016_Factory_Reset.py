import logging
from lib.common.system.TvSetting import TvSettingApp, TV_SETTING_APP, FACTORY_RESET_ACTIVITY_NAME
import time
from lib.common.system.FactoryReset import FactoryReset

eth_set = TvSettingApp()
fac = FactoryReset()


def test_factory_reset():
    fac.check_test_file()
    eth_set.start_activity(TV_SETTING_APP, FACTORY_RESET_ACTIVITY_NAME)
    factory_reset()
    eth_set.stop()
    assert fac.check_test_file()
    eth_set.root()
    logging.info('factory reset ok')


def factory_reset():
    time.sleep(5)
    # eth_set.wait_and_tap('System', "text")
    # eth_set.find_and_tap('About', "text")
    # eth_set.find_and_tap('Factory reset', "text")
    # time.sleep(2)
    # eth_set.tap(1552, 529)  # Factory reset x_midpoint, y_midpoint
    # eth_set.find_and_tap('Erase everything', "text")
    eth_set.keyevent('20')
    eth_set.keyevent('20')
    eth_set.keyevent('20')
    eth_set.keyevent("23")
    time.sleep(3)
    eth_set.keyevent('20')
    eth_set.keyevent('20')
    eth_set.keyevent('20')
    eth_set.keyevent("23")
    time.sleep(3)
    logging.info('start factory reset')
    time.sleep(120)
