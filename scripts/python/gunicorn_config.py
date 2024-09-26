#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/9/8 下午5:17
# @Author  : yongbo.shao
# @File    : gunicorn_config.py
# @Email   : yongbo.shao@amlogic.com
# @Ide: PyCharm
# gunicorn_config.py

bind = "0.0.0.0:8000"  # 指定绑定的IP地址和端口
workers = 4            # 启动4个工作进程
app_name = "app.py:app"  # 指定Flask应用的导入路径
# 运行命令 gunicorn -b 0.0.0.0:8000 -w 4 --log-level debug app:app
