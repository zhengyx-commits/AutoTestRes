import logging
import os
import re
import sys
import time

import pytest

from lib import CheckAndroidVersion
from lib.common import config_yaml
from lib.common.playback.LocalPlayer import LocalPlayer
from lib.common.system.ADB import ADB
from tools.resManager import ResManager


class CameraRecorder(ADB, CheckAndroidVersion):
    ACTIVITY_NAME = "com.droidlogic.democamera.MainActivity"
    APK_PACKAGE_NAME = "com.droidlogic.democamera"
    APK_NAME = "DemoCamera-20210330.apk"
    GALLERY_APK = "com.android.gallery3d"
    GALLERY_APK_VIDEO_ACTIVITY = ".app.MovieActivity"
    GALLERY_APK_PICTURE_ACTIVITY = ".app.Wallpaper"

    def __init__(self):
        # self.device_id = pytest.config['device_id']
        ADB.__init__(self, "CameraRecorder", unlock_code="", logdir=pytest.result_dir, stayFocus=True)
        CheckAndroidVersion.__init__(self)
        self.localplayer = LocalPlayer()
        self.resManager = ResManager()
        self.app_path = self.resManager.get_target("apk/")
        _INSTANCE = None
        # self.app_path = "res/apk/"
        # self.Camera_Recorder = pytest.config.get("Camera_Recorder")
        # self.log_path = self.Camera_Recorder["log_path"]
        # self.path = self.Camera_Recorder['path']
        # self.name = self.Camera_Recorder['name']
        # self.ref_fps = self.Camera_Recorder['reference_fps']
        # self.ref_w = self.Camera_Recorder['reference_width']
        # self.ref_h = self.Camera_Recorder['reference_height']
        self.p_conf_Camera_Recorder = config_yaml.get_note('conf_Camera_Recorder')
        self.p_conf_log_path = self.p_conf_Camera_Recorder['log_path']
        self.p_conf_path = self.p_conf_Camera_Recorder['path']
        self.p_conf_name = self.p_conf_Camera_Recorder['name']
        self.p_conf_ref_fps = self.p_conf_Camera_Recorder['reference_fps']
        self.p_conf_ref_w = self.p_conf_Camera_Recorder['reference_width']
        self.p_conf_ref_h = self.p_conf_Camera_Recorder['reference_height']
        self.remove_image_video = f"rm -rf {self.p_conf_path}"
        # clear video and image data
        self.run_shell_cmd(self.remove_image_video)
        self.ott_flag = False
        self.set_androidversion_r_apk()

    def set_androidversion_r_apk(self):
        if self.build_version == "30" or self.build_version == "34" or self.build_version == "31":
            self.APK_NAME = "Camera2.apk"
            self.APK_PACKAGE_NAME = "com.android.camera2"
            self.ACTIVITY_NAME = "com.android.camera.CameraLauncher"
            self.ott_flag = True
            return self.ott_flag

    def start_app(self):
        logging.info("Start Camera App")
        self.start_activity(self.APK_PACKAGE_NAME, self.ACTIVITY_NAME)

    def stop_app(self):
        logging.info("Stop Camera App")
        self.app_stop(self.APK_PACKAGE_NAME)

    def start_record(self):
        if self.build_version == "34":
            if self.APK_PACKAGE_NAME not in self.run_shell_cmd('dumpsys activity | grep camera2')[1]:
                return False
        else:
            if self.APK_PACKAGE_NAME not in self.run_shell_cmd('dumpsys activity | grep mResume')[1]:
                return False
        try:
            if not self.ott_flag:
                logging.info("START CLICK")
                self.find_and_tap("open", "text")
                time.sleep(2)
                self.find_and_tap("start record", "text")
                logging.info("START RECORDING")
            else:
                if self.build_version == "34":
                    logging.info("Click Video")
                    time.sleep(2)
                    self.keyevent(21)
                    self.find_and_tap("Video", "text")
                    time.sleep(2)
                    self.find_and_tap("com.android.camera2:id/shutter_button", "resource-id")
                    time.sleep(65)
                    self.find_and_tap("com.android.camera2:id/shutter_button", "resource-id")
                else:
                    logging.info("Click Video")
                    self.find_and_tap("Video", "text")
                    time.sleep(5)
                    self.keyevent(22)
                    time.sleep(1)
                    self.keyevent(22)
                    time.sleep(1)
                    self.keyevent(23)
                    time.sleep(65)
                    self.keyevent(23)
                    time.sleep(1)
            logging.info("STOP RECORDING")
            time.sleep(2)
            self.pull_video()
        except Exception as e:
            logging.info(str(e))

    def start_camera2(self):
        if self.build_version == "34":
            if self.APK_PACKAGE_NAME not in self.run_shell_cmd('dumpsys activity | grep camera2')[1]:
                return False
        else:
            if self.APK_PACKAGE_NAME not in self.run_shell_cmd('dumpsys activity | grep mResume')[1]:
                return False
        for i in range(5):
            try:
                if self.build_version == "34":
                    self.root()
                    logging.info(f"Click Camera,{i + 1} times")
                    time.sleep(2)
                    self.keyevent(21)
                    self.find_and_tap("Camera", "text")
                    time.sleep(2)
                    self.find_and_tap("com.android.camera2:id/shutter_button", "resource-id")
                    time.sleep(20)
                else:
                    logging.info(f"Click Camera,{i + 1} times")
                    self.find_and_tap("Camera", "text")
                    time.sleep(5)
                    self.keyevent(22)
                    time.sleep(1)
                    self.keyevent(22)
                    time.sleep(1)
                    self.keyevent(23)
                    time.sleep(2)
                    self.keyevent(22)
                    self.keyevent(22)
                    logging.info(f"pls watch picture,{i + 1} times")
                    time.sleep(1)
                    self.keyevent(21)
                    time.sleep(1)
                    self.keyevent(21)
            except Exception as e:
                logging.info(str(e))

    def pull_video(self):
        res = False
        try:
            if self.check_video_file():
                logging.info("video pulling")
                if not self.ott_flag:
                    self.pull("/storage/" + self.localplayer.getUUID() + self.p_conf_path + self.p_conf_name,
                              pytest.result_dir)
                else:
                    if self.build_version == "34":
                        os.mkdir(pytest.result_dir + "/" + self.p_conf_log_path)
                        self.pull("/storage/emulated/0/Pictures/.", pytest.result_dir + "/" + self.p_conf_log_path)
                        self.pull("/storage/emulated/0/Movies/.", pytest.result_dir + "/" + self.p_conf_log_path)
                    else:
                        self.pull(self.p_conf_path, pytest.result_dir)
                res = True
                time.sleep(20)

        except Exception as e:
            logging.info(str(e))
        finally:
            if res:
                logging.info("video file pulled")

    def check_file(self):
        # TODO @chao.li : Cognitive Complexity from 24 to the 15 allowed
        check_flag = False
        files = {
            True: os.listdir(pytest.result_dir + "/" + self.p_conf_log_path),
            False: os.listdir(pytest.result_dir)
        }[self.ott_flag]
        logging.info(f"files:{files}")
        for file in files:
            logging.info(f"file:{file}")
            if "3gp" not in file:
                continue
            # get probe info from stderr
            # rc, output = self.checkoutput_term(
            #     "ffprobe " + (pytest.result_dir + "/" + self.p_conf_log_path + "/" + file))
            rc, output = self.run_terminal_cmd(
                "ffprobe " + (pytest.result_dir + "/" + self.p_conf_log_path + "/" + file), output_stderr=True)
            if rc != 0:
                assert False, 'ffprobe command with error'
            logging.debug(f"output:{output}")
            output = str(output)
            encode_type_str = re.findall(r'Video: (\w+)', output)
            resolution_str = re.findall(r'([0-9]{3,4})x([0-9]{3,4})', output)
            fps_str = re.findall(r'(\w+.\w+) fps', output)
            logging.info(
                f"encode_type_str:{encode_type_str}, resolution_str:{resolution_str}, fps_str:{fps_str} \n")
            if not (encode_type_str and resolution_str and fps_str):
                logging.info(
                    f"encode_type_str:{encode_type_str}, resolution_str:{resolution_str}, fps_str:{fps_str} \n")
                break
            if not self.ott_flag:
                if encode_type_str[0] == 'h264' or 'hevc':
                    check_flag = True
                    logging.info(
                        f"encode_type_str:{encode_type_str}, resolution_str:{resolution_str}, fps_str:{fps_str} \n")
                    break
            else:
                check_flag = True
                logging.info(
                    f"encode_type_str:{encode_type_str}, resolution_str:{resolution_str}, fps_str:{fps_str} \n")
        return check_flag

    def check_video_file(self):
        check_flag = False
        if self.build_version == "34":
            picture_file = self.run_shell_cmd("ls /storage/emulated/0/Pictures/")[1]
            movies_file = self.run_shell_cmd("ls /storage/emulated/0/Movies/")[1]
            files = picture_file + movies_file
        else:
            files = self.run_shell_cmd(f'ls {self.p_conf_path}')[1]
        logging.info(f"files:{files}")
        if files != '':
            check_flag = True
        logging.info(f'check_flag : {check_flag}')
        return check_flag
