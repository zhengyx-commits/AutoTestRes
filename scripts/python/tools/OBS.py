import base64
import json
import logging
import threading
import time
import os
import cv2
import numpy as np
import subprocess
from obswebsocket import obsws, requests
from datetime import datetime
import signal
import psutil


def once(func):
    def wrapper(*args, **kwargs):
        if not wrapper.has_run:
            wrapper.has_run = True
            return func(*args, **kwargs)
    wrapper.has_run = False
    return wrapper

@once
def start_obs(app_id):
    obs_process = subprocess.Popen(['flatpak', 'run', app_id])
    time.sleep(5)


def stop_obs():
    # 查找 OBS 进程的 PID
    obs_pid = None
    for proc in psutil.process_iter():
        if "obs" in proc.name().lower():
            obs_pid = proc.pid
            break

    if obs_pid:
        print("Sending SIGINT signal to OBS process...")
        try:
            os.kill(obs_pid, signal.SIGINT)
            print("SIGINT signal sent successfully.")
        except OSError as e:
            print(f"Failed to send SIGINT signal: {e}")
    else:
        print("OBS process not found.")

@once
def start_obs_thread():
    t = threading.Thread(target=start_obs, args=('com.obsproject.Studio', ))
    t.setDaemon(True)
    t.start()


class OBS:
    def __init__(self, ip='192.168.1.105', port=4455, scene_name=None):
        self.ip = ip
        self.port = port
        self.screenshot_dir = "/home/amlogic/ref_screen/capture_screen/"
        self.reference_dir = "/home/amlogic/ref_screen/"
        self.record_dir = "/home/amlogic/record/"
        self.obs_ws = None
        self.scene_name = scene_name
        start_obs('com.obsproject.Studio')
        # start_obs_thread()

    # Connect to OBS WebSocket server
    def connect_to_obs(self):
        self.obs_ws = obsws(self.ip, self.port)
        self.obs_ws.connect()


    # Disconnect from OBS WebSocket server
    def disconnect_from_obs(self):
        if self.obs_ws is not None:
            self.obs_ws.disconnect()

    # Create a new scene name
    def set_scene_name(self):
        if self.obs_ws is not None:
            Scene_Object = self.get_scene_name()
            Set_Scene_Object = self.obs_ws.call(requests.SetSceneName(sceneName=Scene_Object['currentProgramSceneName'], newSceneName=self.scene_name))
            logging.info(f"Set_Scene_Object: {Set_Scene_Object}")
            New_Scene_Object = self.obs_ws.call(requests.GetSceneList()).datain
            logging.info(f"New_Scene_Object: {New_Scene_Object['currentProgramSceneName']}")

    def get_scene_name(self):
        if self.obs_ws is not None:
            Scene_Object = self.obs_ws.call(requests.GetSceneList()).datain
            logging.info(f"Scene_Object: {Scene_Object['currentProgramSceneName']}")
            return Scene_Object

    def set_source_name(self, source_name):
        if self.obs_ws is not None:
            Source_Object = self.get_source_name()
            New_Source_Object = self.obs_ws.call(requests.SetInputName(inputName=Source_Object['inputs'][2]['inputName'], newInputName=source_name))
            print(New_Source_Object)

    def get_source_name(self):
        if self.obs_ws is not None:
            Source_Object = self.obs_ws.call(requests.GetInputList()).datain
            return Source_Object

    # Capture screen using OBS
    def capture_screen(self, sleep_time=3):
        if self.obs_ws is not None:
            # Set the screenshot file save path
            self.check_and_create_directory(self.screenshot_dir)
            self.check_and_create_directory(self.reference_dir)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_file = f"{self.screenshot_dir}Screenshot_{timestamp}.png"

            # Send the screenshot command
            screenshot_response = self.obs_ws.call(
                requests.SaveSourceScreenshot(sourceName=self.scene_name, imageFormat='png', imageFilePath=screenshot_file))
            time.sleep(sleep_time)

            # Handle the response
            if screenshot_response.status:
                logging.info(f"Screenshot saved at: {screenshot_file}")
            else:
                logging.info(f"Screenshot failed: {screenshot_response}.status")

            return screenshot_file
        else:
            logging.error("Not connected to OBS WebSocket server.")

    # Check path
    def check_and_create_directory(self, path):
        if not os.path.exists(path):
            os.makedirs(path)

    # Calculate Mean Squared Error (MSE)
    def calculate_mse(self, image1, image2):
        difference = cv2.subtract(image1, image2)
        squared_difference = difference * difference
        mse = np.mean(squared_difference)
        logging.info(mse)
        return mse

    # Compare two images
    def compare_images(self, image1, image2, threshold):
        screenshot = cv2.imread(image1)
        reference = cv2.imread(image2)
        mse = self.calculate_mse(screenshot, reference)
        if mse < threshold:
            return True
        else:
            return False

    # Capture screen and compare
    def screenshot_and_compare(self, reference_file):
        # Connect to OBS WebSocket server
        self.connect_to_obs()

        self.set_scene_name()

        # Capture device screen
        screenshot_file = self.capture_screen()

        # Disconnect from OBS WebSocket server
        self.disconnect_from_obs()

        # Compare the two images
        is_same = self.compare_images(screenshot_file, reference_file, 1)
        if is_same:
            logging.info('Screenshot is similar to the reference image')
            return True
        else:
            logging.info('Screenshot is not similar to the reference image')
            return False

    def set_video_settings(self, outputHeight=1080, outputWidth=1920, fpsDenominator=30):
        if self.obs_ws is not None:
            video_settings = self.obs_ws.call(requests.GetVideoSettings())
            logging.info(f"video_settings: {video_settings}")
            new_video_settings = self.obs_ws.call(requests.SetVideoSettings(outputHeight=outputHeight, outputWidth=outputWidth, fpsDenominator=fpsDenominator))
            logging.info(f"new_video_settings: {new_video_settings}")

    def set_record_directory(self):
        self.check_and_create_directory(self.record_dir)
        if self.get_record_directory() != self.record_dir:
            if self.obs_ws is not None:
                self.obs_ws.call(requests.SetRecordDirectory(recordDirectory=self.record_dir))

    def get_record_directory(self):
        if self.obs_ws is not None:
            record_path = self.obs_ws.call(requests.GetRecordDirectory()).datain
            # print(record_path)
            return record_path

    # Start recording
    def start_recording(self):
        self.connect_to_obs()
        self.set_scene_name()
        self.set_record_directory()
        if self.obs_ws is not None:
            status = self.obs_ws.call(requests.GetRecordStatus()).datain
            logging.debug("status:", status)
            if status['outputActive']:
                self.obs_ws.call(requests.StopRecord())
            self.obs_ws.call(requests.StartRecord())

    # Stop recording
    def stop_recording(self):
        if self.obs_ws is not None:
            self.obs_ws.call(requests.StopRecord())
            status = self.obs_ws.call(requests.GetRecordStatus())
            return status
        self.disconnect_from_obs()

    def pause_resording(self):
        if self.obs_ws is not None:
            self.obs_ws.call(requests.PauseRecord())
            status = self.obs_ws.call(requests.GetRecordStatus())
            return status

    def resume_resording(self):
        if self.obs_ws is not None:
            self.obs_ws.call(requests.ResumeRecord())
            status = self.obs_ws.call(requests.GetRecordStatus())
            return status

    def get_media_input_status(self):
        if self.obs_ws is not None:
            Source_Object = self.get_source_name()
            # print(Source_Object)
            mediaState = self.obs_ws.call(requests.GetMediaInputStatus(inputName=Source_Object['inputs'][2]['inputName'])).datain
            logging.info("mediaState:", mediaState)

    def get_latest_file(self, file_dir):
        files = os.listdir(file_dir)
        files = [file for file in files if os.path.isfile(os.path.join(file_dir, file))]
        latest_file = max(files, key=lambda x: os.path.getmtime(os.path.join(file_dir, x)))
        # print(self.record_dir + "/" + latest_file)
        return file_dir + latest_file


if __name__ == '__main__':
    # start_obs()
    obs = OBS(ip='10.18.19.205', port=4455, scene_name='gtv')
    # obs.get_latest_file()
    # obs.connect_to_obs()
    # obs.start_recording()
    # time.sleep(3)  # 等待10秒钟
    # obs.stop_recording()
    # obs.disconnect_from_obs()
    # obs.set_record_directory()
    # obs.get_record_directory()
    # obs.set_scene_name()
    # obs.capture_screen()
    stop_obs()
    # print(obs.screenshot_and_compare('1', '/home/poppy/capture_screen/home.png'))
    # obs.set_scene_name()
    # obs.get_media_input_status()
    # obs.set_video_settings()
    # obs.start_recording()
    # time.sleep(10)  # 等待10秒钟
    # obs.stop_recording()
    # print(obs.screenshot_and_compare(source_name='1', reference_file='/home/poppy/Screenshot_20240227_155928.png'))

