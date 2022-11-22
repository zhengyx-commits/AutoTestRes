#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/8/3
# @Author  : kejun.chen
# @File    : DVBStreamProvider.py
# @Email   : kejun.chen@amlogic.com
# @Ide: PyCharm
import logging
import os
import re
import threading
import time
from lib.common.system.SSH import SSH
from lib.common.system.NetworkAuxiliary import getIfconfig


class DVBStreamProvider():
    DTPLAY_PROCESS = "ps ux |grep DtPlay"
    TYPE = "dvb-c"
    RATE = 6875  # -r rate
    # FREQUENCY = 474  # -mf freq
    # PORT = 9000  # -ipport
    LOOP_TDT = 'LOOP_TDT'  # -lf
    DTPLAY_COMMAND = 'Dt2115bRc.exe'
    DTPLAY_PATH = 'C:\\DVB'
    OUTPUT_LEVEL = 0.0  # -ml

    FRQ_LIST = ['474', '578', '322', '330', '338', '346', '354', '362']
    PORT_LIST = ['9000', '8999', '8998', '8997', '8996', '8995', '8994', '8993']

    def __init__(self, ip="10.18.19.35", service="dvb"):
        '''
        Connect to stream provider node.

        Args:
            ip: stream provider node ip
            service: dvb
        '''
        self.ssh_pipe = self.ssh_connect(ip, service)
        # self.root_path = self.ssh_pipe.send_cmd('chdir')[0].strip()
        self.root_path = 'C:\\DVB'
        logging.info(f"self.root_path: {self.root_path}")
        self.video_root_path = self.root_path + '\\video'
        self.remove_tmp_log()
        self._thread = None

    def ssh_connect(self, ip, service):
        '''

        Args:
            ip: ip to ssh connect
            service: dvb

        Returns:

        '''
        # check sh or sz node
        iplist = getIfconfig()
        device_ip_sz = "10.18.19.35"
        try:
            if device_ip_sz in iplist:
                ssh_pipe = SSH(ip, uname='SH171300-407', passwd='Amlogic!234', platform='win')
            else:
                ssh_pipe = SSH(ip, uname='SH171300-407', passwd='Amlogic!234', platform='win')
        except Exception as e:
            logging.info("Can't connect ssh")
            raise Exception("ssh unable to connect")
        finally:
            logging.info("Connected ssh")
            return ssh_pipe

    def get_file_path(self, video_format, *args):
        '''
        find video path which match condition
        @param video_format: such mp4 or ts,which format you want search
        @param args: filename re
        @return: list with file path
        '''
        target_name = ""
        if args:
            target_name = ' '.join([f"*{a}*" for a in args])
        find_command = f"where /R {self.video_root_path} *{target_name}*.{video_format}"
        logging.info(f"find_command: {find_command}")
        if not self.ssh_pipe.send_cmd(find_command):
            raise IOError("can't find the video.")
        else:
            res = self.ssh_pipe.send_cmd(find_command)[0]
        return res.split('\n')[:-1]

    def start_send(self, protocol, file_path, iswait=False, **kwargs):
        '''

        Args:
            protocol: dvb-c, dvb-t, dvb-s
            file_path: video path for streaming
            iswait: bool = False
            **kwargs: Any parameter

        Returns:

        '''
        self._thread = None
        if not file_path:
            raise IOError("pls set local playback file path.")
        if not isinstance(self._thread, threading.Thread):
            self._thread = threading.Thread(target=self._start_send, args=(protocol, file_path),
                                            kwargs={**kwargs},
                                            name='dvb_stream')
            self._thread.setDaemon(True)
            self._thread.start()
        if iswait:
            time.sleep(2)

    def _start_dektec_dtu_2115bRc_server(self, file_path, **kwargs):
        """

        Args:
            file_path: video path that for streaming
            **kwargs: command parameter

        Returns:
            None

        """
        value = ''.join([f'-{k} {v} ' for k, v in kwargs.items()])
        cmd = f'{self.DTPLAY_PATH}/{self.DTPLAY_COMMAND} {file_path} {value}'
        logging.info(f"cmd: {cmd}")
        self.dtplay_popen = self.ssh_pipe.send_cmd(cmd)
        time.sleep(3)

    def _start_send(self, protocol, file_path, **kwargs):
        '''
        stitch command
        @param protocol: udp or rtsp or rtp
        @param file_path: video file path such like C:\\DVB\\video\\nndj.mp4
        @return: command :str
        '''
        if not file_path:
            raise IOError("pls set local playback file path.")
        if protocol not in ['dvb-c']:
            raise ValueError("Doesn't support such protocol , pls select ")
        try:
            if protocol == 'dvb-c':
                self._start_dektec_dtu_2115bRc_server(file_path, **kwargs)
                return
        except Exception as e:
            logging.warning("Can't setup stream")

    def stop_dvb(self, stream_count=""):
        file_path = 'C:\\DVB\\video\\gr1.ts'
        if not stream_count:
            stream_count = 2
        for i in range(stream_count):
            try:
                self.start_send(self.TYPE, file_path.rstrip('\r'), ipport=self.PORT_LIST[i], stop='')
                logging.info(f"dtplay process {i} is stopped")
            except Exception as e:
                logging.warning(f"Can't stop dtplay process : {self.PORT_LIST[i]}")
            time.sleep(1)

    def start_dvbc_stream(self, video_name, video_format='ts'):
        """
        Only one stream.

        Args:
            video_format: ts, mp4, and so on.
            video_name: video name.

        Returns:
            None
        """
        # self.stop_dvb()
        self.remove_tmp_log()
        file_path = self.get_file_path(video_format, video_name)
        logging.info(f"file_path: {file_path}")
        self.record_video_path(file_path)
        self.record_video_information(file_path)
        self.start_send(self.TYPE, file_path[0].rstrip('\r'), ipport=self.PORT_LIST[0], mf=self.FRQ_LIST[0], lf=self.LOOP_TDT, ml=self.OUTPUT_LEVEL)

    def start_dvbc_multi_stream_diff_frq(self, video_format='ts', *video_name):
        '''
        Multi stream using different frequent.

        Args:
            video_format: ts, mp4, and so on.
            *video_name: video name.

        Returns:
            None
        '''
        # self.stop_dvb()
        self.remove_tmp_log()
        for i in range(len(video_name)):
            file_path = self.get_file_path(video_format, video_name[i])
            logging.info(f"file_path: {file_path}")
            self.record_video_path(file_path)
            self.record_video_information(file_path)
            self.start_send(self.TYPE, file_path[0].rstrip('\r'), ipport=self.PORT_LIST[i], mf=self.FRQ_LIST[i], lf=self.LOOP_TDT, ml=self.OUTPUT_LEVEL)
            time.sleep(1)

    # def start_dvbc_multi_stream_same_frq(self, video_format='ts', *video_name):
    #     '''
    #     Multi stream using same frequent.
    #
    #     Args:
    #         video_format: ts, mp4, and so on.
    #         *video_name: video name.
    #
    #     Returns:
    #         None
    #     '''
    #     # self.stop_dvb()
    #     for i in range(len(video_name)):
    #         file_path = self.get_file_path(video_format, video_name[i])
    #         logging.info(f"file_path: {file_path}")
    #         # self.record_video_path(file_path)
    #         self.start_send(self.TYPE, file_path[0].rstrip('\r'), ipport=self.PORT_LIST[i], mf=self.FREQUENCY)

    def record_video_path(self, file_path):
        '''

        Args:
            file_path: video path that for streaming

        Returns:
            Recording file path and video channel number in dvb.log
        '''
        video_log_filter = 'ffprobe -print_format json -show_format -v quiet'
        video_channel_number = self.ssh_pipe.send_cmd(f'{video_log_filter} {file_path[0]} | findstr nb_programs')[0]
        logging.info(f'video_channel_number: {video_channel_number}')
        with open('dvb.log', 'a', encoding='utf-8') as f:
            f.write(file_path[0] + '\n')
            f.write(f'video_channel_number:{video_channel_number}' + '\n')
            f.close()

    def record_video_information(self, file_path):
        """

        Args:
            file_path:

        Returns:

        """
        video_log_filter = 'ffprobe -print_format json -show_format'
        video_information = self.ssh_pipe.send_cmd(f'{video_log_filter} {file_path[0]}')[1]
        logging.debug(f'video information : {video_information}')
        video_information_intercept = re.findall(r'Input #0, mpegts, from(.*)', video_information, re.S)[0]
        logging.info(f'video_information_intercept: {video_information_intercept}')
        with open('dvb.log', 'a', encoding='utf-8') as f:
            f.write(video_information_intercept)
            f.close()

    def remove_tmp_log(self):
        if os.path.isfile('./dvb.log'):
            try:
                os.remove('./dvb.log')
            except BaseException as e:
                print(e)
        else:
            logging.info('The dvb tmp log is not exit.')


# demo
# from tools.DVBStreamProvider import DVBStreamProvider
# dvb_stream = DVBStreamProvider()

# simple stream
# dvb_stream.start_dvbc_stream('gr1')

# different frequent and multi stream
# dvb_stream.start_dvbc_multi_stream_diff_frq('ts', 'gr1', 'iptv')

# same frequent and multi stream
# dvb_stream.start_dvbc_multi_stream_same_frq('ts', 'gr1', 'iptv')
