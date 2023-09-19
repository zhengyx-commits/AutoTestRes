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
import paramiko
import requests
import re
import json
import urllib.parse
from tools.yamlTool import yamlTool
from lib.common.system.NetworkAuxiliary import getIfconfig, config_common_yaml, differentiate_servers

config_compatibility_yaml = yamlTool(os.getcwd() + '/config/config_ott_hybrid_compatibility.yaml')
resource_url = config_compatibility_yaml.get_note("conf_resource_server").get("resource_url")
config_yaml = yamlTool(os.getcwd() + '/config/config.yaml')
local_ip = differentiate_servers()[0]


class ResManager:
    iplist = getIfconfig()
    device_ip_sz = "192.168.1.246"
    p_conf_server = config_common_yaml.get_note("server")
    if device_ip_sz not in iplist:
        # shanghai
        p_conf_res_path = p_conf_server.get("resource_server_sh")
        # SERVER_PATH = p_conf_res_path
    else:
        # other
        p_conf_res_path = p_conf_server.get("resource_server_xx")
        if 'xx' in p_conf_res_path:
            p_conf_res_path = 'http://10.28.18.56:80/'
    #     SERVER_PATH = 'http://10.28.18.56:80/'
    # ROOT_PATH = 'res/'

    def __init__(self, ip="10.18.11.94", uname="amlogic", passwd="Amlogicqa"):
        self.serverUrl = "http://"+ip+"/res"
        self.client = None
        self.ip = ip
        self.uname = uname
        self.passwd = passwd
        self.ssh_server = paramiko.SSHClient()
        self.ssh_server.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        self.ssh_server.connect(self.ip, username=self.uname, password=self.passwd)
        self.video_url_list = []
        self.file_paths = []
        self.invalid_video = []

    def get_video_path(self, path="/mnt/fileroot/Test_File"):
        """
        Args:
            name_keyword: Required parameter,string or list or tuple
            video_format: Optional parameter,string
        Returns:
            video path list
        """
        command = f"find {path} -type f"
        stdin, stdout, stderr = self.ssh_server.exec_command(command)
        self.file_paths = stdout.read().decode('utf-8').splitlines()
        for video in self.file_paths:
            if local_ip in self.serverUrl:
                video_path = re.findall(r"/res(.*)", video)[0]
                video_url = self.serverUrl + video_path
            else:
                self.serverUrl = resource_url
                last_slash_index = self.serverUrl.rfind("/")
                mate_string = self.serverUrl[last_slash_index + 1:]
                video_path = re.findall(rf"{mate_string}(.*)", video)[0]
                video_url = self.serverUrl + video_path
            ext = video_path.rsplit(".", 1)[-1].lower()
            allowed_extensions = {"rm", "rmvb", "avi", "mkv", "mp4", "wmv", "mov", "flv", "asf", "3gp", "mpg", "mvc",
                                  "m2ts", "ts", "swf", "mlv", "divx", "3gp2", "3gpp", "h265", "m4v", "mts", "tp", "bit",
                                  "webm", "3g2", "f4v", "pmp", "mpeg", "vob", "dat", "m2v", "iso", "vp9", "trp", "bin",
                                  "hm10"}
            if ext in allowed_extensions:
                self.video_url_list.append(video_url)

    def download_video(self, target_folder: str, video_url_list):
        """
        Args:
            target_folder: Required parameter, the target folder to save the downloaded videos
        Returns:
            Target server path list
        """
        os.makedirs(target_folder, exist_ok=True)
        file_count = 0
        for download_url in video_url_list:
            # Extract the filename from the URL
            filename = os.path.basename(download_url)
            # Create the target file path with preserved directory structure
            relative_path = os.path.dirname(download_url.replace(resource_url + "/", ""))
            target_path = os.path.join(target_folder, relative_path, filename)
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            response = requests.get(download_url, stream=True)
            if response.status_code == 200:
                with open(target_path, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=4096):
                        file.write(chunk)
                logging.info(f"Downloaded video: {filename} to {target_path}")
                file_count += 1
            else:
                logging.info(f"Failed to download video: {download_url}")
                self.invalid_video.append(download_url)

        logging.info(f"Total downloaded files: {file_count}")

    # download remote file
    def download_target(self, path, target_file=""):
        try:
            file = requests.get(self.p_conf_res_path + path)
            if file.ok:
                logging.debug('Find the file')
                if not target_file:
                    with open(f'res/{path}', 'wb') as f:
                        f.write(file.content)
                else:
                    with open(target_file, 'wb') as f:
                        f.write(file.content)
            else:
                raise FileNotFoundError("Can't found the file on server , pls check again")
        except requests.exceptions.ConnectionError as e:
            logging.warning(f"Can't connect {self.p_conf_res_path}")
            logging.warning(e)

    # download remote directory to local
    def download_directory_target(self, source_path, target_path, ignore=None):
        # Todo 后续使用wget -r -np -nH -R index.html -q http://10.28.18.43/res/xxx/实现
        if not os.path.isdir(target_path):
            os.makedirs(target_path)

        if source_path.startswith("http"):
            file_list = self.get_remote_file_list(source_path)
        else:
            file_list = os.listdir(source_path)

        if ignore is not None:
            ignored = ignore(source_path, file_list)
        else:
            ignored = set()

        for filename in file_list:
            if filename not in ignored:
                source_file_path = os.path.join(source_path, filename)
                target_file_path = os.path.join(target_path, filename)

                if source_path.startswith("http"):
                    # Check if remote file or directory exists
                    if self.check_remote_file_or_directory_exists(source_file_path):
                        if not source_file_path.endswith('/') and not os.path.isfile(target_file_path):
                            # Download file from remote URL
                            self.download_remote_file(source_file_path, target_file_path)
                        elif not source_file_path.endswith('/') and os.path.isfile(target_file_path):
                            logging.debug("target file exists")
                        else:
                            # Recursively download files from remote directory
                            self.download_directory_target(source_file_path, target_file_path, ignore=ignore)
                    else:
                        print(f"Remote file or directory does not exist: {source_file_path}")
                else:
                    # Local file copy
                    self.copy_local_file(source_file_path, target_file_path)

    def get_target(self, path, source_path=""):
        DEVICE_IP, STREAM_IP, RTSP_PATH = differentiate_servers()
        if not os.path.exists('../res'):
            os.mkdir('../res')
        logging.debug(f'get_target {path}')
        # get target_path, filename
        if "live555" in source_path:
            target_path, filename = os.path.split(RTSP_PATH + "/" + path)
        elif "rtp_udp" in source_path:
            path = path + "/"
            target_path, filename = os.path.split('/home/amlogic/video/' + path)
        elif "http_hls" in source_path:
            target_path, filename = os.path.split('/var/www/res/' + path)
        elif "so/wvcas_so" in source_path:
            path = path + "/"
            target_path, filename = os.path.split('/home/amlogic/so/' + path)
        elif "wvcas_video" in source_path:
            target_path, filename = os.path.split('/home/amlogic/Videos/' + path)
        elif "so/ms12_X4" in source_path:
            path = path + "/"
            target_path, filename = os.path.split('/home/amlogic/so/' + path)
        elif "so/adt4_camera2" in source_path:
            path = path + "/"
            target_path, filename = os.path.split('/home/amlogic/so/' + path)
        else:
            target_path, filename = os.path.split('res/' + path)
        target_file = target_path + "/" + filename

        # download file
        if filename != "" and not os.path.exists('res/' + path) and "apk" in path:
            if not os.path.exists(target_path):
                os.makedirs(target_path)
            if not path.endswith('/'):
                self.download_target(path)
        elif filename != "" and "Netflix" in path:
            if not os.path.exists(target_path):
                os.makedirs(target_path)
            if not path.endswith('/'):
                self.download_target(path)
        elif filename != "" and not os.path.exists(target_file):
            if not os.path.exists(target_path):
                os.makedirs(target_path)
            if not path.endswith('/'):
                self.download_target(source_path, target_file)
        else:
            pass

        # download directory
        if path.endswith('/') and source_path:
            self.download_directory_target(source_path=self.p_conf_res_path + source_path,
                                           target_path=target_path)
        elif path.endswith('/') and not source_path:
            logging.info(target_path)
        else:
            logging.debug('file already exists')

        # return result
        if filename != "":
            return target_file  # return file
        else:
            return target_path  # return path

    def remove_target(self, path):
        if os.path.exists(f'res/{path}'):
            os.system(f'rm res/{path}')
        else:
            logging.warning('file not exists')

    # get remote file and dir list
    def get_remote_file_list(self, url):
        response = requests.get(url)
        if response.status_code == 200:
            try:
                html_content = response.content.decode('utf-8')
                encoded_file_list = re.findall(r'<a href="([^"]+)">', html_content)
                file_list = [urllib.parse.unquote(encoded_file) for encoded_file in encoded_file_list]
                return file_list
            except:
                logging.warning(f"Failed to extract file list from response: {response.content}")
        else:
            logging.warning(f"Failed to get remote file list from: {url}")
        return []

    # check file/directory exists if not
    def check_remote_file_or_directory_exists(self, url):
        response = requests.get(url)
        return response.status_code == 200

    # download remote file to local
    def download_remote_file(self, source_file_path, target_file_path):
        response = requests.get(source_file_path)
        if response.status_code == 200:
            with open(target_file_path, 'wb') as file:
                file.write(response.content)
            print(f"Downloaded file: {source_file_path} to {target_file_path}")
        else:
            print(f"Failed to download file: {source_file_path}")

    # copy local file to local
    def copy_local_file(self, source_file_path, target_file_path):
        shutil.copyfile(source_file_path, target_file_path)
        print(f"Copied file: {source_file_path} to {target_file_path}")

# if __name__ == '__main__':
#     res = ResManager()
#     res.get_target('apk/app-debug.apk')
