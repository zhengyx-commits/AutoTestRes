import time
import pytest
from lib.common.playback.LocalPlayer import LocalPlayer
from lib.common.tools.pass_oobe import *
from lib import get_device
import os
import re
from lib.common.system.NetworkAuxiliary import getIfconfig
from tools.resManager import ResManager
from tools.yamlTool import yamlTool
from datetime import datetime

config_yaml = yamlTool(os.getcwd() + '/config/config.yaml')
p_conf_obs_websocket_ip = config_yaml.get_note('ip').get('device_ip')
# obs = OBS(ip=p_conf_obs_websocket_ip, port=4455, scene_name='gtv')
resmanager = ResManager()
config_ott_sanity_yaml = yamlTool(os.getcwd() + '/config/config_ott_sanity.yaml')


def is_sz_server():
    device_ip_sz = "10.28.9.62"
    iplist = getIfconfig()
    if device_ip_sz in iplist:
        return True
    else:
        return False


serialnumbers = get_device()
u2 = UiautomatorTool(serialnumbers)
adb = ADB()
android_version = adb.getprop("ro.build.version.sdk")
p_conf_power_symlink = pytest.config['power_symlink']


if 'ott_sanity' == pytest.target.get("prj") or 'ott_hybrid' in pytest.target.get("prj"):
    adb.shell('\"echo 2 > /sys/class/remote/amremote/protocol\"')
    time.sleep(1)
    adb.home()
    adb.home()
    if not check_oobe():
        adb.root()
        network_interface = adb.create_network_auxiliary()
        adb.offline_network(network_interface)
        time.sleep(5)
        logging.info('start to oobe')
        adb.keyevent(4)
        adb.shell(f"cmd wifi connect-network {p_conf_wifi_ssid} wpa2 {p_conf_wifi_pwd}")
        time.sleep(10)
        assert pass_oobe()
        adb.shell("settings put global stay_on_while_plugged_in 1")
        adb.restore_network(network_interface)
        time.sleep(5)
    else:
        logging.info('oobe is complete')
        time.sleep(2)
        assert True


def reboot_and_retore():
    adb.reboot()
    start_time = time.time()
    while time.time() - start_time < 60:
        reboot_check = adb.run_shell_cmd("getprop sys.boot_completed")[1]
        if reboot_check == "1":
            logging.info("booted up")
            break
        else:
            time.sleep(5)
    reboot_check = adb.run_shell_cmd("getprop sys.boot_completed")[1]
    if reboot_check != "1":
        raise Exception('boot up run time error')
    else:
        pass
    time.sleep(20)
    adb.root()


def connect_network():
    network_interface = adb.create_network_auxiliary()
    adb.offline_network(network_interface)
    adb.forget_wifi()
    adb.set_wifi_enabled()
    time.sleep(2)
    output = adb.connect_wifi(p_conf_wifi_ssid, p_conf_wifi_pwd, "wpa2")
    logging.info(f"output: {output}")
    if "Connection failed" in output:
        return False
    else:
        return True


def get_powerRelay_path():
    path = os.getcwd()
    workspace_path = re.findall(r'(.*?)/scripts', path)[0]
    bin_target_path = workspace_path + "/bin/"
    return bin_target_path


def check_network(timeout=20.0):
    result = False
    start = float(time.time())
    while float(time.time()) - start < timeout:
        result = adb.ping()
        logging.info(f"result: {result}")
        if result:
            break
    return result


def check_network_connect_time(network="wifi", page="home"):
    start = time.time()
    current_window = adb.check_current_window(CURRENT_FOCUS)
    while time.time() - start <= 5:
        if page == "home":
            if HOME_ACTIVITY in current_window:
                logging.info(f"{network} connected within 5s")
                return True
        elif page == "exo_local":
            if "com.droidlogic.exoplayer2.demo/com.droidlogic.videoplayer.MoviePlayer" in current_window:
                logging.info(f"{network} connected within 5s")
                return True
        elif page == "youtube":
            if "com.google.android.youtube.tv/com.google.android.apps.youtube.tv.activity.MainActivity" in current_window:
                logging.info(f"{network} connected within 5s")
                return True


def get_display_mode():
    adb.root()
    display_mode = adb.run_shell_cmd("cat /sys/class/display/mode")[1]
    return display_mode


def send_file_to_remote(local_file_path):
    import paramiko
    import datetime
    remote_file_path = "/home/amlogic/FAE/AutoTest/OTT_BASIC/systeminfo"
    remote_host = "10.18.11.98"
    remote_username = "amlogic"
    remote_password = "Linux2023"
    run_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    try:
        # 建立 SSH 连接
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(remote_host, username=remote_username, password=remote_password)

        scp_client = paramiko.SFTPClient.from_transport(ssh_client.get_transport())

        # 通过 SFTP 将文件发送到远程 PC
        for local_file in local_file_path:
            remote_file = f"{remote_file_path}/{os.path.basename(local_file)}"
            scp_client.put(local_file, remote_file)
            _, stdout, _ = ssh_client.exec_command(f'mv {remote_file} {remote_file_path}/{run_time}_{pytest.result.get_name()}_{os.path.basename(local_file)}')
        scp_client.close()
        ssh_client.close()

        print(f"File {local_file_path} sent to remote PC successfully.")
    except Exception as e:
        print(f"Error occurred while sending file to remote PC: {e}")

