# #!/usr/bin/env python
# # -*- coding: utf-8 -*-
# # @Time    : 2023/8/3 下午5:44
# # @Author  : yongbo.shao
# # @File    : app.py
# # @Email   : yongbo.shao@amlogic.com
# # @Ide: PyCharm
# import fcntl
import os
import sys
from flask import Flask, render_template, request, jsonify, redirect, url_for
import subprocess
import json

app = Flask(__name__, template_folder='templates')

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

# 设置全局字符编码为 UTF-8
app.config['JSON_AS_ASCII'] = False

# 读取target.json和config.json的内容
with open('target.json', 'r') as target_file:
    target_data = json.load(target_file)


with open('config/config.json', 'r') as config_file:
    config_data = json.load(config_file)
    config_list = list(config_data.values())  # 将字典的值转化为列表
    # print(config_list)


# 提取config.json中的目标项目列表和设备列表
target_prj_list = list(config_data['devices'].keys())
device_list = list(config_data['devices'].values())


# 添加一个新的路由来加载config.json的内容
@app.route('/load_config', methods=['GET'])
def load_config():
    selected_project = request.args.get('project')
    print("selected_project", selected_project)
    try:
        with open('config/config.json', 'r') as config_file:
            config_data = json.load(config_file)
            # print("config_data", config_data)
            return jsonify(config_data['devices'].get(selected_project, {}))  # 返回指定的配置数据
    except FileNotFoundError:
        return jsonify({'error': 'Config file not found'}), 404


# 添加加载测试用例配置文件的路由
@app.route('/load_testcases', methods=['GET'])
def load_testcases():
    selected_project = request.args.get('project')
    testcases_filename = f'config/testcases_{selected_project}.json'
    print("51", testcases_filename)
    try:
        with open(testcases_filename, 'r') as testcases_file:
            testcases_data = json.load(testcases_file)

            # 遍历测试用例，读取内容并添加到数据中
            for test_case in testcases_data['testcases']:
                test_case_path = test_case.get('path', '')
                # 读取测试用例内容文件
                with open(test_case_path, 'r') as content_file:
                    test_case_content = content_file.read()
                    # print(test_case_content)
                test_case['content'] = test_case_content

            return jsonify(testcases_data)
    except FileNotFoundError:
        return jsonify({'error': 'Test cases not found for the selected project'}), 404


@app.route('/')
def index():
    # print("config_list", config_list)
    return render_template('index.html', target=target_data, target_prj_list=target_prj_list, device_list=device_list,
                           config_list=config_list)


@app.route('/update_config', methods=['POST'])
def update_config():
    new_target_prj = request.form.get('target_prj')
    new_device = request.form.get('device')
    new_device_id = request.form.get('device_id')
    new_serial_port = request.form.get('serial_port')
    new_baudrate = int(request.form.get('baudrate'))  # 转换为整数

    # 修改target.json中的配置信息
    target_data['target']['prj'] = new_target_prj
    # print("80", config_list[0][new_target_prj]['device_id'])
    # 遍历 config_list 寻找选择的目标项目并更新配置
    for project_name, config in config_data['devices'].items():
        if project_name == new_target_prj:
            print(f"project_name={project_name}, new_target_prj={new_target_prj}")
            # config['ipaddr'] = new_ipaddr
            config['device_id'] = new_device_id
            config['serial_port'] = new_serial_port
            config['baudrate'] = new_baudrate
            break  # 找到匹配的项目后跳出循环

    # 将新的配置信息写回文件
    with open('target.json', 'w') as target_file:
        json.dump(target_data, target_file, indent=4)

    with open('config/config.json', 'w') as config_file:
        json.dump(config_data, config_file, indent=4)

    return jsonify({'选择的项目': new_target_prj, '设备ID': new_device_id, '串口': new_serial_port, '波特率': new_baudrate})


@app.route('/run_tests')
def run_tests():
    test_case_name = request.args.get('test_case_name')
    project = request.args.get('project')
    # print("test_case_name", test_case_name)
    # print("project", project)

    if test_case_name is not None:
        # 构建要执行的命令，这里假设您的命令是运行Python脚本并传递测试用例路径作为参数
        command = ['python3', 'localtest_runner.py', '-m', test_case_name]
        print(command)
        # 使用subprocess调用命令来执行测试，并捕获输出
        result = subprocess.run(command, capture_output=True, text=True)
        print("result", result)
        # 返回测试结果
        return jsonify({'output': result.stdout})
    else:
        print("Test case not found")
        return jsonify({'error': 'Test case not found'})


if __name__ == '__main__':
    app.run(debug=True)
