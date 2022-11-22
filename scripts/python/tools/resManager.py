#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2021/9/27 10:28
# @Author  : chao.li
# @Site    :
# @File    : resManager.py
# @Software: PyCharm


import logging
import os
import shutil

import requests
from lib.common.system.NetworkAuxiliary import getIfconfig


class ResManager:
    iplist = getIfconfig()
    device_ip_sz = "192.168.1.246"
    if device_ip_sz not in iplist:
        # shanghai
        SERVER_PATH = 'http://10.18.7.30:80/'
    else:
        # shenzhen
        SERVER_PATH = 'http://10.28.18.56:80/'
    ROOT_PATH = 'res/'

    def download_target(self, path):
        try:
            file = requests.get(self.SERVER_PATH + self.ROOT_PATH + path)
            if file.ok:
                logging.debug('Find the file')
                with open(f'res/{path}', 'wb') as f:
                    f.write(file.content)
            else:
                raise FileNotFoundError("Can't found the file on server , pls check again")
        except requests.exceptions.ConnectionError as e:
            logging.warning(f"Can't connect {self.SERVER_PATH}")
            logging.warning(e)

    def download_directory_target(self, source_path, target_path, ignore=None):
        # Todo 后续使用wget -r -np -nH -R index.html -q http://10.28.18.43/res/xxx/实现
        if os.path.isdir(source_path):
            if not os.path.isdir(target_path):
                os.makedirs(target_path)
            files = os.listdir(source_path)
            if ignore is not None:
                ignored = ignore(source_path, files)
            else:
                ignored = set()
            for f in files:
                if f not in ignored:
                    logging.debug(os.path.join(source_path, f))
                    logging.debug(os.path.join(target_path, f))
                    self.download_directory_target(os.path.join(source_path, f), os.path.join(target_path, f),
                                                   ignore=None)
                    if not os.path.isdir(os.path.join(source_path, f)):
                        shutil.copyfile(os.path.join(source_path, f), os.path.join(target_path, f))

    def get_target(self, path):
        if not os.path.exists('../res'):
            os.mkdir('../res')
        logging.debug(f'get_target {path}')
        target_path, filename = os.path.split('res/' + path)
        if filename != "" and not os.path.exists('res/' + path):
            if not os.path.exists(target_path):
                os.makedirs(target_path)
            if not path.endswith('/'):
                self.download_target(path)
        if path.endswith('/'):
            self.download_directory_target(source_path=f"/var/www/res/{path}",
                                           target_path=os.getcwd() + '/' + target_path)
        else:
            logging.debug('file already exists')
        return f'{os.getcwd()}' + '/res/' + path

    def remove_target(self, path):
        if os.path.exists(f'res/{path}'):
            os.system(f'rm res/{path}')
        else:
            logging.warning('file not exists')


# if __name__ == '__main__':
#     res = ResManager()
#     res.get_target('apk/app-debug.apk')
