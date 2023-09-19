# /usr/bin/env python
# -+- coding: utf-8 -*-
import time
from pywinauto import Desktop, keyboard, application, findwindows


print('-----开始安装OpenSSH 服务器-----')
# 模拟按下"Win + I"打开设置窗口
keyboard.send_keys('{VK_LWIN down}i{VK_LWIN up}')
print('输入 win + i')

# 等待设置窗口打开
settings_window = Desktop(backend='uia').window(title='设置')
settings_window.wait('visible', timeout=10)

# 打印窗口控件信息
# print(settings_window.print_control_identifiers())

# 点击"应用"
settings_window.child_window(title="应用", control_type="Text").click_input()
print('应用')

# 等待"应用和功能"窗口打开
apps_window = Desktop(backend='uia').window(title='设置')
apps_window.wait('visible', timeout=10)
print('应用和功能')
# print(settings_window.print_control_identifiers())

# 点击"可选功能"
apps_window.child_window(title="可选功能", control_type="Text").click_input()

# 等待"可选功能"窗口打开
optional_features_window = Desktop(backend='uia').window(title='设置')
optional_features_window.wait('visible', timeout=10)
print('可选功能')
# print(settings_window.print_control_identifiers())

# 滚动到底部
# optional_features_window.child_window(auto_id="PageContainer").scroll_down()

# 点击"添加功能"
optional_features_window.child_window(title="添加功能", control_type="Button").click_input()

# 等待"添加可选功能"窗口打开
available_features_window = Desktop(backend='uia').window(title='设置')
available_features_window.wait('visible', timeout=10)
print('添加可选功能')
# print(optional_features_window.print_control_identifiers())

# 搜索"OpenSSH服务器"
available_features_window.type_keys("OpenSSH{SPACE}服务器")
keyboard.send_keys('{ENTER}')


search_box = Desktop(backend='uia').window(title='设置')
search_box.wait('visible', timeout=10)
print('openssh')
# print(available_features_window.print_control_identifiers())

# 选择"OpenSSH服务器"
ssh_server = search_box.child_window(title="OpenSSH 服务器", control_type="CheckBox")
ssh_server.click_input()

# 点击"安装"
install_button = search_box.child_window(title="安装(1)", control_type="Button")
install_button.click_input()
print('安装')

# 等待安装完成
# app = Application().connect(title="设置")
# time.sleep(60)

# 检查OpenSSH服务器是否安装成功
timeout = 600
while True:
    verify_window = Desktop(backend='uia').window(title='设置')
    # print(verify_window.print_control_identifiers())
    apps_list = verify_window.child_window(auto_id='SystemSettings_Optional_Features_Installed_Collection_V2_ListView', control_type='List')
    openssh_item = apps_list.child_window(title='OpenSSH 服务器', control_type='Text')
    if openssh_item.exists():
        print('install is successful.')
        break
    else:
        print('OpenSSH 不在安装列表中, 请等待安装完成')
    if timeout <= 0:
        print('install is failed.')
        break

    timeout -= 10
    time.sleep(10)

settings_window.close()
print('-----结束安装OpenSSH 服务器-----')


print('-----开始设置OpenSSH 服务自动启动-----')
# 打开"services.msc"
keyboard.send_keys('{VK_LWIN down}r{VK_LWIN up}')
time.sleep(1)
keyboard.send_keys('services.msc')
keyboard.send_keys('{ENTER}')
time.sleep(1)

# 等待"服务"窗口打开
services_window = Desktop(backend='uia').window(title='服务')
# print(services_window.print_control_identifiers())
services_window.wait('visible', timeout=10)
print('服务')

# 搜索并选择SSH服务
search_box = services_window.child_window(title="名称", control_type="HeaderItem")
search_box.click_input()
keyboard.send_keys(r'OpenSSH{SPACE}SSH{SPACE}Server')
keyboard.send_keys('{ENTER}')

# 等待搜索结果出现
time.sleep(1)

# 选中SSH服务
ssh_service = services_window.child_window(title="OpenSSH SSH Server", control_type="ListItem")
# print(ssh_service.print_control_identifiers())
ssh_service.click_input()
print('OpenSSH SSH Server')

# 等待SSH服务属性窗口打开
ssh_service_properties = Desktop(backend='uia').window(title='OpenSSH SSH Server 的属性(本地计算机)')
# print(ssh_service_properties.print_control_identifiers())
ssh_service_properties.wait('visible', timeout=10)
print('OpenSSH SSH Server 属性')

# 设置启动类型为自动
startup_type_combobox = ssh_service_properties.child_window(title="启动类型(E):", control_type="ComboBox")
startup_type_combobox.select("自动")
print('启动类型')

startup_button = ssh_service_properties.child_window(title="启动(S)", control_type="Button")
startup_button.click_input()
print('启动')
time.sleep(30)

# startup_win = Desktop(backend='uia').window(title='服务控制')
# if startup_win:
#     print(startup_win.print_control_identifiers())
#     startup_win.wait_not('visible', timeout=10)
#     print('服务控制')
# else:
#     print('启动成功')

# 点击"应用"
ssh_service_properties.child_window(title="应用(A)", control_type="Button").click_input()
print('应用')

# 点击"确定"
ssh_service_properties.child_window(title="确定", control_type="Button").click_input()
print('确定')

# 关闭"服务"窗口
services_window.close()
print('-----开始设置OpenSSH 服务自动启动-----')


def get_current_active_window():
    # 获取当前活动窗口信息
    active_window = findwindows.find_windows(active_only=True, visible_only=True)
    if active_window:
        # 打印当前活动窗口的标题和类名
        app = application.Application().connect(handle=active_window[0])
        active_window = app.window(handle=active_window[0])
        window_title = active_window.window_text()
        window_class = active_window.element_info.class_name
        print("当前活动窗口的标题:", window_title)
        print("当前活动窗口的类名:", window_class)
        # print(active_window.print_control_identifiers())
        return active_window
    else:
        print("没有找到当前活动窗口。")


print('-----开始安装Dta驱动-----')
# 启动安装程序
app = application.Application().start("C:\DownloadedFiles\DtaInstall.exe")
time.sleep(3)

# 处理弹窗
dlg = get_current_active_window()
if dlg.window_text() == '用户账户控制':
    print('用户账户控制')
    dlg.Edit.type_keys("{TAB}{TAB}{ENTER}")
    time.sleep(3)
else:
    print("UAC提示框未出现。")

# 等待安装程序窗口出现
time.sleep(30)
print('开始安装')

# 获取当前界面
# dlg = app.window(title='Dta Driver v4.28.7.283 - InstallShield Wizard')
dlg = get_current_active_window()
# print(dlg.print_control_identifiers())
dlg.Next.click()
time.sleep(1)
print('简介')

# 选择安装步骤
dlg = get_current_active_window()
# print(dlg.print_control_identifiers())
dlg.Install.click()
time.sleep(1)
print('安装')

# 等待安装完成
timeout = 300
while True:
    dlg = get_current_active_window()
    finish_button = dlg.child_window(title='&Finish', class_name='Button')
    if finish_button.exists():
        print('安装完成.')
        break
    else:
        print('安装中...')
    if timeout <= 0:
        print('安装失败.')
        break
    timeout -= 10
    time.sleep(10)
# print(dlg.print_control_identifiers())
dlg.Finish.click()
time.sleep(1)
print('完成')

# 关闭安装程序
app.kill()
print('-----结束安装Dta驱动-----')

print('-----开始安装StreamXpress-----')
# 启动安装程序
app = application.Application().start("C:\DownloadedFiles\StreamXpressSetup.exe")
time.sleep(3)

# 处理弹窗
dlg = get_current_active_window()
if dlg.window_text() == '用户账户控制':
    print('用户账户控制')
    dlg.Edit.type_keys("{TAB}{TAB}{ENTER}")
    time.sleep(3)
else:
    print("UAC提示框未出现。")


# 等待安装程序窗口出现
time.sleep(30)
print('开始安装')

# 获取当前界面
# dlg = app.window(title='StreamXpress Stream Player (DTC-300) - InstallShield Wizard')
dlg = get_current_active_window()
# print(dlg.print_control_identifiers())
dlg.Next.click()
time.sleep(1)
print('简介')

# 同意协议
dlg = get_current_active_window()
# print(dlg.print_control_identifiers())
accept_radio = dlg.child_window(title='I &accept the terms in the license agreement', class_name="Button")
accept_radio.click()
time.sleep(1)
dlg.Next.click()
time.sleep(1)
print('协议')

# 选择用户
dlg = get_current_active_window()
# print(dlg.print_control_identifiers())
dlg.Next.click()
time.sleep(1)
print('用户选择')

# 选择安装类型
dlg = get_current_active_window()
# print(dlg.print_control_identifiers())
complete_radio = dlg.child_window(title="&Complete", class_name="Button")
complete_radio.click()
dlg.Next.click()
time.sleep(1)
print('安装类型')

# 选择安装步骤
dlg = get_current_active_window()
# print(dlg.print_control_identifiers())
dlg.Install.click()
time.sleep(1)
print('安装')

# 等待安装完成
timeout = 300
while True:
    dlg = get_current_active_window()
    finish_button = dlg.child_window(title='&Finish', class_name='Button')
    if finish_button.exists():
        print('安装完成.')
        break
    else:
        print('安装中...')
    if timeout <= 0:
        print('安装失败.')
        break
    timeout -= 10
    time.sleep(10)
# print(dlg.print_control_identifiers())
dlg.Finish.click()
time.sleep(1)
print('完成')

# 关闭安装程序
app.kill()
print('-----结束安装StreamXpress-----')


print('-----开始安装DtInfoInstall-----')
# 启动安装程序
app = application.Application().start("C:\DownloadedFiles\DtInfoInstall.exe")
time.sleep(3)

# 处理弹窗
dlg = get_current_active_window()
if dlg.window_text() == '用户账户控制':
    print('用户账户控制')
    dlg.Edit.type_keys("{TAB}{TAB}{ENTER}")
    time.sleep(3)
else:
    print("UAC提示框未出现。")


# 等待安装程序窗口出现
time.sleep(30)
print('start install')

# 获取当前界面
# dlg = app.window(title='DtInfo v4.32.0.74 - InstallShield Wizard')
dlg = get_current_active_window()
# print(dlg.print_control_identifiers())
dlg.Next.click()
time.sleep(1)
print('简介')

# 选择用户
dlg = get_current_active_window()
# print(dlg.print_control_identifiers())
dlg.Next.click()
time.sleep(1)
print('用户选择')

# 选择安装类型
dlg = get_current_active_window()
# print(dlg.print_control_identifiers())
complete_radio = dlg.child_window(title="&Complete", class_name="Button")
complete_radio.click()
dlg.Next.click()
time.sleep(1)
print('setup type')

# 选择安装步骤
dlg = get_current_active_window()
# print(dlg.print_control_identifiers())
dlg.Install.click()
time.sleep(1)
print('install')

# 等待安装完成
timeout = 300
while True:
    dlg = get_current_active_window()
    finish_button = dlg.child_window(title='&Finish', class_name='Button')
    if finish_button.exists():
        print('install is finished')
        break
    else:
        print('installing')
    if timeout <= 0:
        print('install is failed.')
        break
    timeout -= 10
    time.sleep(10)
# print(dlg.print_control_identifiers())
dlg.Finish.click()
time.sleep(1)
print('finish')

# 关闭安装程序
app.kill()
print('-----结束安装DtInfoInstall-----')