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
from tools.yamlTool import yamlTool

config_yaml = yamlTool(os.getcwd() + '/config/config_dvb.yaml')
p_conf_freq = config_yaml.get_note('conf_freq')
# sh env configration
p_conf_node_ip = config_yaml.get_note('conf_stream_node')['ip_Win']
p_conf_node_user = config_yaml.get_note('conf_stream_node')['user_Win']
p_conf_node_pwd = config_yaml.get_note('conf_stream_node')['pwd_Win']
p_conf_stream_path = config_yaml.get_note('conf_stream_path')['stream_Win']
p_conf_video_path = config_yaml.get_note('conf_stream_path')['video_Win']
p_conf_serial_number = config_yaml.get_note('conf_stream_path')['serial_number']
# sz env configration
p_conf_node_ip_sz = config_yaml.get_note('conf_stream_node')['ip_Win_sz']
p_conf_node_user_sz = config_yaml.get_note('conf_stream_node')['user_Win_sz']
p_conf_node_pwd_sz = config_yaml.get_note('conf_stream_node')['pwd_Win_sz']
p_conf_stream_path_sz = config_yaml.get_note('conf_stream_path')['stream_Win_sz']
p_conf_video_path_sz = config_yaml.get_note('conf_stream_path')['video_Win_sz']
p_conf_serial_number_sz = config_yaml.get_note('conf_stream_path')['serial_number_sz']


class DVBStreamProvider():
    DTPLAY_PROCESS = "ps ux |grep DtPlay"
    TYPE = "dvb-c"
    RATE = 6875  # -r rate
    # FREQUENCY = 474  # -mf freq
    # PORT = 9000  # -ipport
    # LOOP_TDT = 'LOOP_TDT'  # -lf
    LOOP_FLAG = 12  # -lf
    DTPLAY_COMMAND = 'Dt2115bRc.exe'
    # DTPLAY_PATH = p_conf_stream_path
    OUTPUT_LEVEL = 0.0  # -ml
    OUTPUT_LEVEL_DVBT = -3.0  # -ml
    OUTPUT_LEVEL_DVBS = -25.0  # -ml

    # FRQ_LIST = ['474', '578', '322', '330', '338', '346', '354', '362']
    PORT_LIST = ['9000', '8999', '8998', '8997', '8996', '8995', '8994', '8993']

    def __init__(self, ip=p_conf_node_ip, service="dvb"):
        '''
        Connect to stream provider node.

        Args:
            ip: stream provider node ip
            service: dvb
        '''
        iplist = getIfconfig()
        device_ip_sz = '10.28.9.68'
        if device_ip_sz in iplist:
            ip = p_conf_node_ip_sz
            logging.debug(f'sz ip: {ip}')
            self.video_root_path = p_conf_video_path_sz
            logging.debug(f"self.video path: {self.video_root_path}")
            self.DTPLAY_PATH = p_conf_stream_path_sz
            logging.debug(f"self.dtplay path: {self.DTPLAY_PATH}")
            self.SERIAL_NUMBER = p_conf_serial_number_sz
            logging.debug(f"self.SERIAL_NUMBER: {self.SERIAL_NUMBER}")
        else:
            ip = p_conf_node_ip
            logging.debug(f'sh ip: {ip}')
            self.video_root_path = p_conf_video_path
            logging.debug(f"self.video path: {self.video_root_path}")
            self.DTPLAY_PATH = p_conf_stream_path
            logging.debug(f"self.dtplay path: {self.DTPLAY_PATH}")
            self.SERIAL_NUMBER = p_conf_serial_number
            logging.debug(f"self.SERIAL_NUMBER: {self.SERIAL_NUMBER}")
        self.ssh_pipe = self.ssh_connect(ip, service)
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
        device_ip_sz = '10.28.9.68'
        try:
            if device_ip_sz in iplist:
                ssh_pipe = SSH(ip, uname=p_conf_node_user_sz, passwd=p_conf_node_pwd_sz, platform='win')
            else:
                ssh_pipe = SSH(ip, uname=p_conf_node_user, passwd=p_conf_node_pwd, platform='win')
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
        cmd = f'{self.DTPLAY_PATH}/{self.DTPLAY_COMMAND} -f {file_path} {value}'
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

    def stop_dvb(self, stream_count="", list_index=0):
        file_path = 'C:\\DVB\\video\\gr1.ts'
        if list_index:
            try:
                self.start_send(self.TYPE, file_path.rstrip('\r'), p=self.PORT_LIST[list_index], a='stop', n=self.SERIAL_NUMBER)
                logging.info(f"dtplay process {list_index} is stopped")
            except Exception as e:
                logging.warning(f"Can't stop dtplay process : {self.PORT_LIST[list_index]}")
            time.sleep(1)
        else:
            if not stream_count:
                stream_count = 2
            for i in range(stream_count):
                try:
                    self.start_send(self.TYPE, file_path.rstrip('\r'), p=self.PORT_LIST[i], a='stop')
                    logging.info(f"dtplay process {i} is stopped")
                except Exception as e:
                    logging.warning(f"Can't stop dtplay process : {self.PORT_LIST[i]}")
                time.sleep(1)

    def pause_dvb(self, stream_count=""):
        file_path = 'C:\\DVB\\video\\gr1.ts'
        if not stream_count:
            stream_count = 2
        for i in range(stream_count):
            try:
                self.start_send(self.TYPE, file_path.rstrip('\r'), p=self.PORT_LIST[i], a='pause', n=self.SERIAL_NUMBER)
                logging.info(f"dtplay process {i} is paused")
            except Exception as e:
                logging.warning(f"Can't pause dtplay process : {self.PORT_LIST[i]}")
            time.sleep(1)

    def start_dvbc_stream(self, video_name, video_format='ts', list_index=0):
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
        self.start_send(self.TYPE, file_path[0].rstrip('\r'), a='play', n=self.SERIAL_NUMBER, p=self.PORT_LIST[list_index], o=p_conf_freq[list_index], m='DVB-C', P='16QAM', lf=self.LOOP_FLAG, ml=self.OUTPUT_LEVEL)

    def resume_dvbc_stream(self, video_name, video_format='ts', list_index=0):
        """
        Only one stream.

        Args:
            video_format: ts, mp4, and so on.
            video_name: video name.

        Returns:
            None
        """
        file_path = self.get_file_path(video_format, video_name)
        logging.info(f"file_path: {file_path}")
        self.start_send(self.TYPE, file_path[0].rstrip('\r'), a='resume', n=self.SERIAL_NUMBER, p=self.PORT_LIST[list_index], o=p_conf_freq[list_index], lf=self.LOOP_FLAG, ml=self.OUTPUT_LEVEL)

    def start_dvbc_multi_stream_diff_frq(self, diff_type=0, video_format='ts', *video_name):
        '''
        Multi stream using different frequent.

        Args:
            diff_type: 0 ,the video formats are the same; otherwise the different.
            video_format: ts, mp4, and so on.
            *video_name: video name.

        Returns:
            None
        '''
        # self.stop_dvb()
        self.remove_tmp_log()
        if not diff_type:
            for i in range(len(video_name)):
                file_path = self.get_file_path(video_format, video_name[i])
                logging.info(f"file_path: {file_path}")
                self.record_video_path(file_path)
                self.record_video_information(file_path)
                self.start_send(self.TYPE, file_path[0].rstrip('\r'), a='play', n=self.SERIAL_NUMBER, p=self.PORT_LIST[i], o=p_conf_freq[i], m='DVB-C', P='16QAM', lf=self.LOOP_FLAG, ml=self.OUTPUT_LEVEL)
                time.sleep(1)
        else:
            file_path = self.get_file_path(video_format, video_name[0])
            logging.info(f"file_path: {file_path}")
            self.record_video_path(file_path)
            self.record_video_information(file_path)
            self.start_send(self.TYPE, file_path[0].rstrip('\r'), a='play', n=self.SERIAL_NUMBER, p=self.PORT_LIST[0], o=p_conf_freq[0], m='DVB-C', P='16QAM', lf=self.LOOP_FLAG, ml=self.OUTPUT_LEVEL)
            time.sleep(1)
            file_path2 = self.get_file_path('trp', video_name[1])
            logging.info(f"file_path: {file_path2}")
            self.record_video_path(file_path2)
            self.record_video_information(file_path2)
            self.start_send(self.TYPE, file_path2[0].rstrip('\r'), a='play', n=self.SERIAL_NUMBER, p=self.PORT_LIST[1], o=p_conf_freq[1], m='DVB-C', P='16QAM', lf=self.LOOP_FLAG, ml=self.OUTPUT_LEVEL)

    def start_dvbc_stream_with_given_freq(self, given_freq=474, video_name='', video_format='ts'):
        '''
        stream using the given frequent.

        Args:
            given_freq: the freq to start stream.
            video_format: ts, mp4, and so on.
            *video_name: video name.

        Returns:
            None
        '''
        self.remove_tmp_log()
        file_path = self.get_file_path(video_format, video_name)
        logging.info(f"file_path: {file_path}")
        self.record_video_path(file_path)
        self.record_video_information(file_path)
        self.start_send(self.TYPE, file_path[0].rstrip('\r'), a='play', n=self.SERIAL_NUMBER, p=self.PORT_LIST[0], o=given_freq, m='DVB-C', P='16QAM', lf=self.LOOP_FLAG, ml=self.OUTPUT_LEVEL)

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

    def start_dvbs_stream(self, video_name, video_format='ts', scan_format='DVBS', freq=1150, symbol_rate=38000000, **kwargs):
        """
        start dvb-s stream

        Args:
            freq: TS player frequency
            video_format: ts, mp4, and so on.
            video_name: video name.
            scan_format: DVBS, DVBS2_QPSK, DVBS2_8PSK, DVBS2_16APSK, DVBS2_32APSK, ...
            parameter: eg: QPSK_3/4_25%

        Returns:
            None
        """
        parameter = kwargs.get('parameter')
        self.remove_tmp_log()
        file_path = self.get_file_path(video_format, video_name)
        logging.info(f"file_path: {file_path}")
        self.record_video_path(file_path)
        self.record_video_information(file_path)
        if parameter is not None:
            self.start_send(self.TYPE, file_path[0].rstrip('\r'), a='play', n=self.SERIAL_NUMBER, p=self.PORT_LIST[0], o=freq, m=scan_format, P=parameter, r=symbol_rate, lf=self.LOOP_FLAG, ml=self.OUTPUT_LEVEL_DVBS)
        else:
            self.start_send(self.TYPE, file_path[0].rstrip('\r'), a='play', n=self.SERIAL_NUMBER, p=self.PORT_LIST[0], o=freq, m=scan_format, r=symbol_rate, lf=self.LOOP_FLAG, ml=self.OUTPUT_LEVEL_DVBS)


    def start_dvbt_stream(self, video_name, video_format='trp', scan_format='DVBT', freq=474, parameter='3/4_7MHZ_QPSK_G=1/16_4K_NATIVE'):
        """
        start dvb-t stream

        Args:
            freq: TS player frequency
            video_format: ts, mp4, and so on.
            video_name: video name.
            scan_format: DVBT, DVBT2
            band_width: 1_7MHZ, 5MHZ, 6MHZ, 8MHZ, 10MHZ, ...
            fft_size: 1K, 2K, 4K, 8K, 16K, 32K, ...
            mode: BPSK, QPASK, QAM16, QAM64, QAM256, ...
            G_I: 1_4, 1_8, 1_16, 1_32, 1_128, 19_128, 19_256
            code_rate: 1_2, 2_3, 3_4, 5_6, 7_8

        Returns:
            None
        """
        # parameter = f"{code_rate}_{band_width}_{mode}_G={G_I}_{fft_size}_NATIVE"
        self.remove_tmp_log()
        file_path = self.get_file_path(video_format, video_name)
        logging.info(f"file_path: {file_path}")
        self.record_video_path(file_path)
        self.record_video_information(file_path)
        self.start_send(self.TYPE, file_path[0].rstrip('\r'), a='play', n=self.SERIAL_NUMBER, p=self.PORT_LIST[0], o=freq, m=scan_format, P=parameter, lf=self.LOOP_FLAG, ml=self.OUTPUT_LEVEL_DVBT)


