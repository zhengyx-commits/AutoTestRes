import re
import logging
from lib.common.system.ADB import ADB
import time

adb = ADB()


def test_volume_adjust():
    adb.clear_logcat()
    adb.keyevent('KEYCODE_VOLUME_DOWN')
    adb.keyevent('KEYCODE_VOLUME_DOWN')
    time.sleep(3)
    volume_down = check_volume()
    adb.clear_logcat()
    adb.keyevent('KEYCODE_VOLUME_UP')
    adb.keyevent('KEYCODE_VOLUME_UP')
    volume_up = check_volume()
    assert volume_down < volume_up
# cast_VolumeControlAndroid: New volume for castType 0 is 0.72


def check_volume():
    start = time.time()
    logcat = adb.popen("logcat -s cast_VolumeControlAndroid")
    while time.time() - start < 5:
        line = logcat.stdout.readline()
        if 'cast_VolumeControlAndroid: New volume for castType' in line:
            volume = re.findall(r".* cast_VolumeControlAndroid: New volume for castType \d is (.*)", line)[0]
            logging.info(f"volume: {volume}")
            return float(volume)
    return False
