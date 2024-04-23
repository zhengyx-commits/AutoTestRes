from tests.OTT_Sanity_Ref import *
from tools.OBS import OBS

obs = OBS(ip=p_conf_obs_websocket_ip, port=4455, scene_name='gtv')


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