import pytest
import logging
import re
import time
from tools.resManager import ResManager
from lib.common.checkpoint.PlayerCheck_Iptv import PlayerCheck_Iptv
from lib.common.playback.LocalPlayer import LocalPlayer
from tests.OTT_Sanity_Ref import config_yaml
from tests.common.camera.test_camera_recorder import TestCameraRecorder
from lib.common.playback import Environment_Detection

p_conf_usb = config_yaml.get_note('conf_usb_and_camera')
p_conf_keyboard = p_conf_usb['keyboard']
p_conf_mouse = p_conf_usb['mouse']
p_conf_uuid = p_conf_usb['usb']
app_name = 'com.droidlogic.videoplayer'
localplayer = LocalPlayer()
playerCheck = PlayerCheck_Iptv()
res_manager = ResManager()
env = Environment_Detection()

class TestUSBFunc:
    @pytest.mark.skip
    def test_OTT_Sanity_Func_030_Keyboard_and_Mouse(self):
        event = localplayer.run_shell_cmd("ls /dev/input/")[1]
        logging.info(event)
        if (p_conf_mouse in event) and (p_conf_keyboard in event):
            assert True
        else:
            assert False

    @pytest.mark.skip
    def test_OTT_Sanity_Func_030_031_032_USB(self):
        uuids = localplayer.getUUIDs()
        for usb in p_conf_uuid.values():
            assert usb in uuids, 'usb devices not found'

    # @pytest.mark.skip
    def test_OTT_Sanity_Func_033_USB_Camera(self):
        camerarecorder = TestCameraRecorder()
        if camerarecorder.getprop(camerarecorder.get_android_version()) == "34":
            res_manager.get_target(path="adt4_camera2", source_path="so/adt4_camera2")
            env.add_so()
        camerarecorder.test_run()   # take photos and video
        camerarecorder.test_play_video()   # play video
        camerarecorder.test_play_picture()  # show picture
        # assert False
        # res = localplayer.run_shell_cmd("ls /storage/emulated/0/DCIM/Camera")[1]
        # video = re.findall(r".*\.3gp", res)[0]
        # localplayer.run_shell_cmd("setenforce 0")
        # time.sleep(2)
        # # play video
        # localplayer.run_shell_cmd(
        #     f"am start -n com.droidlogic.videoplayer/.VideoPlayer -d file:/storage/emulated/0/DCIM/Camera/{video}")
        # assert playerCheck.check_startPlay()[0], 'playback start play failed'
        # localplayer.app_stop(app_name)


    # def test_OTT_Sanity_Func_MOVIEPLAYER_032(self, timeout=timeout):
    #     start_time = time.time()
    #     adb.run_shell_cmd(self.MOVIE_PLAYER_COMPONENT)
    #     p = subprocess.Popen(adb_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    #     while time.time() - start_time < timeout:
    #         recv = p.stdout.readline()
    #         logging.info(f"1 recv:{recv}")
    #         if re.search(b"FileList: BrowserFile path=/storage/4C16-2B29", recv):
    #             logging.info(f"2 recv:{recv}")
    #             assert True
    #             break
