import os

os.environ['DISPLAY'] = ':0'
import pyautogui
import yaml
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


class yamlTool:
    def __init__(self, path):
        self.path = path
        with open(path, encoding='utf8') as a_yaml_file:
            # 解析yaml
            self.parsed_yaml_file = yaml.load(a_yaml_file, Loader=yaml.FullLoader)

    def get_note(self, note):
        return self.parsed_yaml_file.get(note)


config_yaml = yamlTool(os.getcwd() + '/AutoTestRes/scripts/python/nts_test/nts_config.yaml')
p_conf_element = config_yaml.get_note("elements")
p_conf_login_element = p_conf_element["login"]
p_conf_platform_element = p_conf_element["select_platform"]
p_conf_manager = p_conf_element["manager"]
p_conf_test_plan_element = p_conf_element["test_plan"]
p_conf_retry = p_conf_element["retry"]
NTS_url = "https://partnertools.nrd.netflix.com/nts/"
test_username = "xiaoliang.wang@amlogic.com"
test_password = "Linux2017!"
option = webdriver.ChromeOptions()
option.add_argument("--start-maximized")
option.add_experimental_option("detach", True)
driver = webdriver.Chrome(options=option)


# print("driver", driver)


def open_webpage(url, title):
    driver.get(url)
    WebDriverWait(driver=driver, timeout=10).until(EC.title_is(title))
    print("Successfully to open URL")


def switch_window(target_window=None):
    if not target_window:
        for window in driver.window_handles:
            if driver.current_window_handle != window:
                driver.switch_to.window(window)
    else:
        driver.switch_to.window(target_window)


def mouse_move_click(x_point, y_point):
    x = int(x_point)
    y = int(y_point)
    pyautogui.moveTo(x, y)
    time.sleep(3)
    pyautogui.click(x, y, button="left")


def login_test_account(user, password, timeout=60):
    try:
        # print(p_conf_login_element["username_path"])
        WebDriverWait(driver=driver, timeout=timeout).until(
            EC.visibility_of_element_located((By.ID, p_conf_login_element["username_path"])))
        driver.find_element(By.ID, p_conf_login_element["username_path"]).send_keys(user)
        time.sleep(1)
        driver.find_element(By.ID, p_conf_login_element["continue_btn"]).click()
        time.sleep(1)
        driver.find_element(By.ID, p_conf_login_element["password_path"]).send_keys(password)
        time.sleep(1)
        driver.find_element(By.ID, p_conf_login_element["login_btn"]).click()
        time.sleep(3)
        return True
    except Exception as e:
        print("Login window load failed,Please check network")
        print(e)
        driver.quit()
        return False


def set_cookie(cookies):
    for cookie in cookies:
        driver.add_cookie(cookie)


def check_status():
    fail_count = 0
    while fail_count <= 3:
        wait_text = WebDriverWait(driver, 30).until(
            EC.text_to_be_present_in_element((By.XPATH, p_conf_manager["wait_path"]),
                                             p_conf_manager["wait_text"]))
        if wait_text:
            try:
                # driver.find_element(By.ID, p_conf_platform_element["cancel"]).click()
                # time.sleep(2)
                driver.find_element(By.XPATH, p_conf_manager["HWManager"]).click()
                time.sleep(5)
                switch_window()
                WebDriverWait(driver, 20).until(
                    EC.visibility_of_element_located((By.XPATH, p_conf_manager["my_devices"])))
                driver.find_element(By.XPATH, p_conf_manager["my_devices"]).click()
                time.sleep(5)
                # status_element = driver.find_element(By.XPATH, p_conf_manager["status"])
                start_time = time.time()
                timeout = 72000
                while time.time() - start_time < timeout:
                    status_element = driver.find_element(By.XPATH, p_conf_manager["status"])
                    if status_element.text == "testing":
                        print("Device is running test,please wait")
                        time.sleep(1800)
                        driver.refresh()
                        time.sleep(10)
                    elif status_element.text == "available":
                        print("Device has finished test")
                        return True
                    else:
                        time.sleep(15)  # Wait 15 seconds for refresh
                print("Timeout: Exceeded 20 hours")
                return False
            except Exception as e:
                print(e)
                raise Exception("Can't find element,please check config yaml")
        else:
            driver.refresh()
            fail_count += 1
    return False


def select_platform():
    fail_count = 0
    while fail_count <= 3:
        wait_text = WebDriverWait(driver, 30).until(
            EC.text_to_be_present_in_element((By.XPATH, p_conf_platform_element["wait_path"]),
                                             p_conf_platform_element["wait_text"]))
        if wait_text:
            try:
                mouse_move_click(x_point=648, y_point=595)
                time.sleep(2)
                driver.find_element(By.ID, p_conf_platform_element["next_btn"]).click()
                print("Select device successfully")
                break
            except Exception as e:
                print(e)
                raise Exception("Can't find element,please check config yaml")
        else:
            driver.refresh()
            fail_count += 1


def run_test_plan():
    fail_count = 0
    while fail_count <= 3:
        wait_text = WebDriverWait(driver, 30).until(
            EC.text_to_be_present_in_element((By.XPATH, p_conf_test_plan_element["wait_path"]),
                                             p_conf_test_plan_element["wait_text"]))
        if wait_text:
            try:
                # step select test_plan
                filter_element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, p_conf_test_plan_element["filter"])))
                driver.execute_script("arguments[0].click();", filter_element)
                time.sleep(1)
                # step click filter>None
                driver.find_element(By.ID, p_conf_test_plan_element["none"]).click()
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, p_conf_test_plan_element["filter"])))
                driver.execute_script("arguments[0].click();", filter_element)
                time.sleep(1)
                # step click filter>Automated Tests
                auto_element = driver.find_element(By.ID, p_conf_test_plan_element["auto"])
                driver.execute_script("arguments[0].click();", auto_element)
                # step click select tests>select all testes
                select_element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, p_conf_test_plan_element["select"])))
                # select_element.click()
                driver.execute_script("arguments[0].click();", select_element)
                time.sleep(1)
                all_element = driver.find_element(By.ID, p_conf_test_plan_element["select_all"])
                driver.execute_script("arguments[0].click();", all_element)
                print("All test cases has selected")
                time.sleep(1)
                # step click Run selected
                driver.find_element(By.XPATH, p_conf_test_plan_element["run"]).click()
                # step select Send Email Report
                email_element = WebDriverWait(driver, 5).until(
                    EC.presence_of_all_elements_located((By.XPATH, p_conf_test_plan_element["send_email"])))
                email_element[2].click()
                time.sleep(2)
                # step click Run
                driver.find_element(By.XPATH, p_conf_test_plan_element["run_all"]).click()
                print("Start Run Test")
                break
            except Exception as e:
                print(e)
                raise Exception("Can't find element,please check config yaml")
        else:
            driver.refresh()
            fail_count += 1


def run_retry():
    fail_count = 0
    driver.find_element(By.XPATH, p_conf_retry["test_plan"]).click()
    while fail_count <= 3:
        wait_text = WebDriverWait(driver, 30).until(
            EC.text_to_be_present_in_element((By.XPATH, p_conf_test_plan_element["wait_path"]),
                                             p_conf_test_plan_element["wait_text"]))
        if wait_text:
            try:
                driver.find_element(By.XPATH, p_conf_retry["pending"]).click()
                select_element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, p_conf_test_plan_element["select"])))
                # select_element.click()
                driver.execute_script("arguments[0].click();", select_element)
                time.sleep(1)
                all_element = driver.find_element(By.ID, p_conf_test_plan_element["select_all"])
                driver.execute_script("arguments[0].click();", all_element)
                print("All test cases has selected")
                time.sleep(1)
                # step click Run selected
                driver.find_element(By.XPATH, p_conf_test_plan_element["run"]).click()
                # step select Send Email Report
                email_element = WebDriverWait(driver, 5).until(
                    EC.presence_of_all_elements_located((By.XPATH, p_conf_test_plan_element["send_email"])))
                email_element[2].click()
                time.sleep(2)
                # step click Run
                driver.find_element(By.XPATH, p_conf_test_plan_element["run_all"]).click()
                print("Start Run Test")
                break
            except Exception as e:
                print(e)
                raise Exception("Can't find element,please check config yaml")
        else:
            driver.refresh()
            fail_count += 1


if __name__ == '__main__':
    open_webpage(NTS_url, "NTS")
    # print(p_conf_login_element["username_path"])
    main_window = driver.current_window_handle
    # print(main_window)
    switch_window()
    time.sleep(1)
    login_fail_count = 0
    while login_fail_count <= 5:
        if login_test_account(test_username, test_password):
            print("Login successfully")
            break
        else:
            login_fail_count += 1
    if login_fail_count < 5:
        # cookies = driver.get_cookies()
        # set_cookie(cookies)
        switch_window(target_window=main_window)
        cookies = driver.get_cookies()
        set_cookie(cookies)
        select_platform()
        time.sleep(3)
        run_test_plan()  # first loop
        time.sleep(60)
        check_status()
        time.sleep(5)
        switch_window(target_window=main_window)
        run_retry()  # retry
        check_status()
        switch_window(target_window=main_window)
        driver.find_element(By.XPATH, p_conf_retry["test_plan"]).click()  # return test plan
    else:
        raise Exception("Login failed for 5 times,exit test")
