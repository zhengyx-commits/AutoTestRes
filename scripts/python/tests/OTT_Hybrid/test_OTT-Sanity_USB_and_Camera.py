import pytest
import logging
import re
import time
from lib.common.playback.LocalPlayer import LocalPlayer
from lib.common.checkpoint.PlayerCheck_Base import PlayerCheck_Base
from . import *


p_conf_usb = config_yaml.get_note('conf_usb')
p_conf_fs = p_conf_usb['fs']
p_conf_keyboard = p_conf_usb['keyboard']
p_conf_mouse = p_conf_usb['mouse']

localplayer = LocalPlayer()
playercheck = PlayerCheck_Base()


class TestUSBFunc:
    # MOVIE_PLAYER_COMPONENT = "am start -n com.droidlogic.videoplayer/.FileList"
    # @pytest.mark.skip
    def test_OTT_Sanity_Func_030_Keyboard_and_Mouse(self):
        event = localplayer.run_shell_cmd("ls /dev/input/")[1]
        logging.info(event)
        if (p_conf_mouse in event) and (p_conf_keyboard in event):
            assert True
        else:
            assert False

    # @pytest.mark.skip
    def test_OTT_Sanity_Func_030_031_032_USB(self):
        uuids = localplayer.getUUIDs()
        for usb in p_conf_fs.values():
            assert usb in uuids

    # @pytest.mark.skip
    def test_OTT_Sanity_Func_033_USB_Camera(self):
        # logging.info(pytest.result_dir)
        from tests.common.camera.test_camera_recorder import TestCameraRecorder
        testcamerarecorder = TestCameraRecorder()
        testcamerarecorder.test_run()
        # play video and picture
        res = localplayer.run_shell_cmd("ls /storage/emulated/0/DCIM/Camera")[1]
        video = re.findall(r".*\.3gp", res)[0]
        localplayer.run_shell_cmd(
            f"am start -n com.droidlogic.videoplayer/.VideoPlayer -d file:/storage/emulated/0/DCIM/Camera/{video}")
        time.sleep(10)
        localplayer.back()
