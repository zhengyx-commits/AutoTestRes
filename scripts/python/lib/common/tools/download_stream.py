import logging
import re
from typing import Union
import requests
import paramiko
import os


class DownloadStream:
    def __init__(self, ip="10.18.7.30", uname="amlogic", passwd="Linux2017"):
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

    # get videos path
    def get_video_path(self, path="/var/www/res/video/temp"):
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
            video_path = re.findall(r"/res(.*)", video)[0]
            video_url = self.serverUrl + video_path
            ext = video_path.rsplit(".", 1)[-1].lower()
            allowed_extensions = {"rm", "rmvb", "avi", "mkv", "mp4", "wmv", "mov", "flv", "asf", "3gp", "mpg", "mvc",
                                  "m2ts", "ts", "swf", "mlv", "divx", "3gp2", "3gpp", "h265", "m4v", "mts", "tp", "bit",
                                  "webm", "3g2", "f4v", "pmp", "mpeg", "vob", "dat", "m2v", "iso", "vp9", "trp", "bin",
                                  "hm10"}
            if ext in allowed_extensions:
                self.video_url_list.append(video_url)

    # download videos
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
            relative_path = os.path.dirname(download_url.replace("http://10.18.7.30/res/video/", ""))
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
