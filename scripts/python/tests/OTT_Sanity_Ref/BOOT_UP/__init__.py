from tests.OTT_Sanity_Ref import *
from tools.OBS import OBS

obs = OBS(ip=p_conf_obs_websocket_ip, port=4455, scene_name='gtv')


def get_boot_logo(first_logo=None, second_logo=None):
    logo_find = True
    ref_boot_image = resmanager.get_target("image/boot.png", source_path="image/boot.png")
    ref_googletv_image = resmanager.get_target("image/google_tv.png", source_path="image/google_tv.png")
    # while True:
    file = obs.get_latest_file(obs.record_dir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if first_logo and second_logo:
        first_process = subprocess.run(["tools/VideoStateDetector", "--method", "2", "--video_path", f"{file}", "--background_image_path", ref_boot_image, "--saved_path", f'{obs.screenshot_dir}{timestamp}_first.png', '--match_number', '1', '--cooldown_time', '0'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        logging.info(f"process: {first_process}")
        first_output = eval(first_process.stdout.decode())

        second_process = subprocess.run(["tools/VideoStateDetector", "--method", "2", "--video_path", f"{file}", "--background_image_path", ref_googletv_image, "--saved_path", f'{obs.screenshot_dir}{timestamp}_second.png', '--match_number', '1', '--cooldown_time', '0'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        logging.info(f"process: {second_process}")
        second_output = eval(second_process.stdout.decode())
        if (first_output['Matched time'] is not None) and (second_output['Matched time'] is not None):
            return logo_find
        else:
            return False
    else:
        return True


def get_launcher(timeout=10):
    launcher = False
    start = time.time()
    ref_image = resmanager.get_target("image/home.png", source_path="image/home.png")
    while time.time() - start < 120:
        obs.capture_screen(sleep_time=timeout)
        file = obs.get_latest_file(obs.screenshot_dir)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        process = subprocess.run(["tools/VideoStateDetector", "--method", "1", "--image_path", f"{file}", "--background_image_path", ref_image, "--saved_path", f'{obs.screenshot_dir}{timestamp}_home.png'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        logging.info(f"process: {process}")
        if process.returncode == 0:
            output = eval(process.stdout.decode())
            if output and output['Matched']:
                launcher = True
                break
    if "home.HomeActivity" in adb.run_shell_cmd(CURRENT_FOCUS)[1]:
        launcher = True
    return launcher
