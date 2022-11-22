import os
import re

from tools.StreamProvider import StreamProvider
import logging


class DVBStreamProvider(StreamProvider):
    DECTEK_DEVICE = "lsusb"
    DECTEK_DEVICE_ID = "1297:030f"
    DTPLAY_PROCESS = "ps ux |grep DtPlay"
    TYPE = "QAM64"  # -mt type
    RATE = 6875  # -r rate
    FREQUENCY = 474  # -mf freq
    QAM = 7/8  # -mC constellation
    LOOP = 0

    def __init__(self, ip="10.18.19.248", service="dvb"):
        super().__init__(ip, service)
        # self.__check_dectek_device()

    # def __check_dectek_device(self):
    #     dectek_device_id = self.ssh_pipe.send_cmd(self.DECTEK_DEVICE)[0].strip()
    #     # logging.info(f"dectek_device_id: {dectek_device_id}")
    #     device_id = re.findall(r"1297:030f", dectek_device_id, re.S)
    #     if device_id and self.DECTEK_DEVICE_ID == device_id[0]:
    #         pass
    #     else:
    #         raise EnvironmentError("dectek is not attached")

    def stop_dvb(self):
        dtplay_process_id = self.ssh_pipe.send_cmd(self.DTPLAY_PROCESS)[0].strip()
        # logging.info(f"dtplay_process_id: {dtplay_process_id}")
        if dtplay_process_id:
            logging.info(f"dtplay_process_id: {dtplay_process_id}")
            self.ssh_pipe.send_cmd("killall DtPlay")
        else:
            logging.info(f"dtplay process is stopped")

    def start_dvbc_stream(self, video_name,type='ts'):
        self.stop_dvb()
        file_path = self.get_file_path(type, video_name)
        logging.info(f"file_path: {file_path}")
        video_log_filter = 'ffprobe -show_format'
        video_channel_number = self.ssh_pipe.send_cmd(f'{video_log_filter} {file_path[0]} | grep nb_programs')[0]
        logging.info(f'video_channel_number: {video_channel_number}')
        with open('dvb.log', 'w', encoding='utf-8') as f:
            f.write(file_path[0] + '\n')
            f.write(f'video_channel_number:{video_channel_number}' + '\n')
            f.close()
        self.start_send(self.TYPE, file_path[0], mt=self.TYPE, mf=self.FREQUENCY, l=self.LOOP)
