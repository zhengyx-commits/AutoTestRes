from tests.OTT_Sanity_Ref import *
import time
import pytest
from lib.common.system.CPU import CPU
from lib.common.system.WIFI import WifiTestApk
from lib import get_device
import logging
import threading
import fcntl

for g_conf_device_id in get_device():
    cpu = CPU(serialnumber=g_conf_device_id)
p_result_path = f'{pytest.result_dir}/../../systemInfo.log'


BUILD_INFO = 'ro.bootimage.build.fingerprint'
BUILD_DATE = 'ro.bootimage.build.date'
SDK_VERSION = 'ro.bootimage.build.version.sdk'
EMMC_SIZE = 'cat /sys/block/mmcblk0/size'
DDR_SIZE = 'cat /proc/meminfo'
DOBLY_ENABLE = 'cat /sys/module/aml_media/parameters/dolby_vision_enable'
KERNEL_VERISON = 'cat /proc/version'

p_conf_wifi = config_ott_sanity_yaml.get_note('conf_wifi')
if not is_sz_server():
    p_conf_wifi_AP = p_conf_wifi['AP_SH']
else:
    p_conf_wifi_AP = p_conf_wifi['AP']
p_conf_wifi_AP_ssid = p_conf_wifi_AP['ssid']
p_conf_wifi_AP_pwd = p_conf_wifi_AP['pwd']

wifi = WifiTestApk()


@pytest.fixture(scope="module", autouse=True)
def setup_teardown():
    adb.reboot()
    start_time = time.time()
    while True:
        if time.time() - start_time > 300:
            raise TimeoutError("Timeout waiting for set-top box to start")

        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)

        if adb.serialnumber in result.stdout:
            adb.root()
            print("Set-top box started successfully")
            break
    adb.run_shell_cmd("dmesg > data/reboot_dmesg.log")
    adb.pull("/data/reboot_dmesg.log", f"{adb.logdir}/reboot_dmesg.log")
    yield
    if 'JENKINS_HOME' in os.environ or 'JENKINS_UPL' in os.environ or 'BUILD_ID' in os.environ:
        send_file_to_remote([f'{pytest.result_dir}/../../systemInfo.log'])


def test_016_get_image_info():
    build_info = adb.run_shell_cmd(f"getprop {BUILD_INFO}")[1]
    build_date = adb.run_shell_cmd(f"getprop {BUILD_DATE}")[1]
    kernel_version = adb.run_shell_cmd(f"getprop {KERNEL_VERISON}")[1]
    dobly_enable = adb.run_shell_cmd(f"getprop {DOBLY_ENABLE}")[1]
    with open(p_result_path, 'a') as f:
        f.write("build info: ")
        f.write(build_info)
        f.write('\n')
        f.write("android version: ")
        f.write(android_version)
        f.write('\n')
        f.write("build date: ")
        f.write(build_date)
        f.write('\n')
        f.write("kernel version: ")
        f.write(kernel_version)
        f.write('\n')
        f.write("dobly enable: ")
        f.write(dobly_enable)
        f.write('\n')
        f.write('-' * 20 + '\n')


def test_016_get_emmc_module_size():
    HS_info = ''
    with open(f"{adb.logdir}/reboot_dmesg.log", "r") as f:
        content = f.readlines()
        for line in content:
            if "new HS" in line:
                HS_info = re.findall(r' new HS(\d+) MMC', line, re.S)[0]
                print(HS_info)
    emmc_size = adb.run_shell_cmd(EMMC_SIZE)[1]
    with open(p_result_path, 'a') as f:
        f.write("HS info: ")
        f.write(HS_info)
        f.write('\n')
        f.write("emmc size: ")
        f.write(f"{int(emmc_size) * 512 / (1024 * 1024) / 1000}GiB")
        f.write('\n')
        f.write('-' * 20 + '\n')


def test_016_get_provision_key():
    resmanager.get_target(path="test_bin/provision_test_query.sh", source_path="test_bin/provision_test_query.sh")
    adb.push("res/test_bin/provision_test_query.sh", "data/")
    adb.run_shell_cmd("chmod 777 /data/provision_test_query.sh")
    keys = adb.run_shell_cmd("./data/provision_test_query.sh")[1].split('.')
    with open(p_result_path, 'a') as f:
        f.write("provision key status: ")
        for key in keys:
            if "provisioned in" in key:
                f.write(key)
                f.write('\n')
        f.write('-' * 20 + '\n')


def test_016_get_ddr_size():
    ddr_size = adb.run_shell_cmd(DDR_SIZE)[1]
    match = re.search(r'MemTotal:\s+(\d+)\s+kB', ddr_size)
    mem_total = 0
    if match:
        mem_total = match.group(1)
        print("MemTotal:", mem_total)
    else:
        print("MemTotal 数据未找到")
    with open(p_result_path, 'a') as f:
        f.write("ddr size: ")
        f.write(f"{int(mem_total) / 1000}MB")
        f.write('\n')
        f.write('-' * 20 + '\n')


def test_016_get_cpu_gpu_info():
    with open(p_result_path, 'a') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        topInfo = adb.run_shell_cmd('top -n 1 -m 5')[1]
        if topInfo:
            f.write(f'Time : {time.asctime()} \n')
            f.write('cpu&gpu info:\n')
            # f.write(topInfo)
            # f.write('\n')
            cpu_model = adb.run_shell_cmd(cpu.CPU_MODEL_COMMAND)[1].strip()
            lines = cpu_model.strip().split('\n')
            count = 0
            for line in lines:
                if line.startswith('processor'):
                    processor = line.split(':')[1].strip()
                    count += 1
                    logging.info(f"processor: {processor}")
                f.write('processor: ')
                f.write(str(count))
                f.write('\n')
                if line.startswith('model name'):
                    model_name = line.split(':')[1].strip()
                    logging.info(f'Model Name : {model_name}')
                    f.write('cpu_model: ')
                    f.write(cpu_model)
                    f.write('\n')
            cpu_work_mode = adb.run_shell_cmd(cpu.CPU_WORK_MODE_COMMAND)[1].strip()
            logging.info(f'cpu_work_mode : {cpu_work_mode}')
            f.write('cpu_work_mode: ')
            f.write(cpu_work_mode)
            f.write('\n')
            current_freq = adb.run_shell_cmd(cpu.CPU_CUR_COMMAND)[1].strip()
            logging.info(f'current_freq : {current_freq}')
            f.write('cpu_current_freq: ')
            f.write(current_freq)
            f.write('\n')
            max_freq = adb.run_shell_cmd(cpu.CPU_MAX_COMMAND)[1].strip()
            logging.info(f'cpu_max_freq : {max_freq}')
            f.write('cpu_max_freq: ')
            f.write(max_freq)
            f.write('\n')
            min_freq = adb.run_shell_cmd(cpu.CPU_MIN_COMMAND)[1].strip()
            logging.info(f'cpu_min_freq: {min_freq} ')
            f.write('cpu_min_freq: ')
            f.write(min_freq)
            f.write('\n')
            gpu_max_freq = adb.run_shell_cmd(cpu.GPU_MAX_COMMAND)[1].strip()
            logging.info(f'gpu_max_freq: {gpu_max_freq} ')
            f.write('gpu_max_freq: ')
            f.write(gpu_max_freq)
            f.write('\n')
            gpu_cur_freq = adb.run_shell_cmd(cpu.GPU_CUR_COMMAND)[1].strip()
            logging.info(f'gpu_max_freq: {gpu_cur_freq} ')
            f.write('gpu_max_freq: ')
            f.write(gpu_cur_freq)
            f.write('\n')
            cpu_online = adb.run_shell_cmd(cpu.CPU_ONLINE_COMMAND)[1].strip()
            logging.info(f'cpu_online: {cpu_online} ')
            f.write('cpu_online: ')
            f.write(cpu_online)
            f.write('\n')
            cpu_temperature = adb.run_shell_cmd(cpu.CPU_TEMPERATURE_COMMAND)[1].strip()
            logging.info(f'cpu_temperature: {cpu_temperature} ')
            f.write('cpu_temperature: ')
            f.write(cpu_temperature)
            f.write('\n')
            f.write('-' * 20 + '\n')
            time.sleep(1)
        else:
            assert False


def test_016_get_hdmi_resolution():
    hdmi_support_resolution = adb.run_shell_cmd("cat /sys/class/amhdmitx/amhdmitx0/disp_cap")[1]
    with open(p_result_path, 'a') as f:
        f.write('hdmi_support_resolution: ')
        f.write(hdmi_support_resolution)
        f.write('-' * 20)
        f.write('\n')


def get_interface():
    network_interface = adb.create_network_auxiliary()
    return network_interface


def start_iperf_server():
    subprocess.run(wifi.IPERF_SERVER, shell=True)


def start_iperf_client(server_ip, num_threads, connection):
    adb.push("res/wifi/iperf", "/data/")
    adb.run_shell_cmd("chmod 777 /data/iperf")
    iperf_command = wifi.IPERF_CLIENT_REGU.format(server_ip, num_threads)
    result, output = adb.run_shell_cmd(f"/data/{iperf_command}")
    print("result", result, output)
    time.sleep(30)
    if result == 0:
        with open(p_result_path, 'a') as f:
            f.write(f"{connection} data: " + "\n")
            f.write(output)
            f.write('\n')
            f.write('-' * 20 + '\n')

    adb.run_shell_cmd("\003")
    return result


def iperf_test(connection):
    print(connection, "吞吐率")
    server_thread = threading.Thread(target=start_iperf_server)
    server_thread.setDaemon(True)
    server_thread.start()

    time.sleep(2)
    print("所有线程执行完毕，主线程退出")


def test_016_network_connection():
    network_interface = get_interface()
    adb.restore_network(network_interface)
    result = adb.ping(hostname="www.youtube.com")
    if not result:
        logging.info("connected with ethernet")
        iperf_test("ethernet")
        start_iperf_client(p_conf_obs_websocket_ip, 1, "ethernet")


def test_016_dobly_enable():
    dobly_enable_status = adb.run_shell_cmd(DOBLY_ENABLE)[1].strip()
    with open(p_result_path, 'a') as f:
        f.write('dobly_enable_status: ')
        f.write(dobly_enable_status + '\n')
        f.write('-' * 20)
        f.write('\n')






