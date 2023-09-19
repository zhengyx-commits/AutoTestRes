import logging
import os
import re
import threading
import time
from lib.common.system.SSH import SSH
from lib.common.system.NetworkAuxiliary import getIfconfig
from tools.yamlTool import yamlTool

config_yaml = yamlTool(os.getcwd() + '/config/config_dvb.yaml')
p_conf_node_ip = config_yaml.get_note('conf_stream_node')['ip_Linux']
p_conf_node_user = config_yaml.get_note('conf_stream_node')['user_Linux']
p_conf_node_pwd = config_yaml.get_note('conf_stream_node')['pwd_Linux']
p_conf_stream_path = config_yaml.get_note('conf_stream_path')['stream_Linux']
p_conf_video_path = config_yaml.get_note('conf_stream_path')['video_Linux']


class DVBStreamProvider:
    DTPLAY_COMMAND = 'DtPlay'
    DTPLAY_PATH = p_conf_stream_path
    DECTEK_DEVICE = "lsusb"
    DECTEK_DEVICE_ID = "1297:030f"
    DTPLAY_PROCESS = "ps ux |grep DtPlay"
    TYPE = "dvb-s"  # -mt type
    FREQUENCY = 1150  # -mf freq
    STREAM_RATE = 38000000
    QAM = 7/8  # -mC constellation
    LOOP = 0
    OUTPUT_LEVEL = 0.0  # -ml

    def __init__(self, ip=p_conf_node_ip, service="dvb"):
        '''
        Connect to stream provider node.

        Args:
            ip: stream provider node ip
            service: dvb
        '''
        self.ssh_pipe = self.ssh_connect(ip, service)
        self.video_root_path = p_conf_video_path
        logging.info(f"self.video path: {self.video_root_path}")
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
                ssh_pipe = SSH(ip, uname='amlogic', passwd='Linux2017', platform='Linux')
            else:
                ssh_pipe = SSH(ip, uname=p_conf_node_user, passwd=p_conf_node_pwd, platform='Linux')
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
            target_name = ' '.join([f"-a -name '*{a}*'" for a in args])
        find_command = f"find {self.video_root_path} -name '*.{video_format}' {target_name} -not -name '.*'"
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

    def _start_dektec_dtu_315_server(self, file_path, **kwargs):
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
        if protocol not in ['dvb-s']:
            raise ValueError("Doesn't support such protocol , pls select ")
        try:
            if protocol == 'dvb-s':
                self._start_dektec_dtu_315_server(file_path, **kwargs)
                return
        except Exception as e:
            logging.warning("Can't setup stream")

    # def __check_dectek_device(self):
    #     dectek_device_id = self.ssh_pipe.send_cmd(self.DECTEK_DEVICE)[0].strip()
    #     # logging.info(f"dectek_device_id: {dectek_device_id}")
    #     device_id = re.findall(r"1297:030f", dectek_device_id, re.S)
    #     if device_id and self.DECTEK_DEVICE_ID == device_id[0]:
    #         pass
    #     else:
    #         raise EnvironmentError("dectek is not attached")

    def stop_dvb(self):
        p_lookup_dtplay_thread_cmd = 'ps -e | grep DtPlay'
        p_dtplay_thread_list = self.ssh_pipe.send_cmd(p_lookup_dtplay_thread_cmd)[0].strip()
        logging.info(f'Dtplay thread:{p_dtplay_thread_list}')
        if 'DtPlay' in p_dtplay_thread_list:
            # self._stop_popen(self.dtplay_popen)
            p_dtplay_pid = re.search('(.*?) DtPlay', p_dtplay_thread_list, re.M | re.I).group(1).strip().split(" ")[0]
            self.ssh_pipe.send_cmd(f'kill {p_dtplay_pid}')
            logging.info(f'Dtplay thread:{p_dtplay_pid} is killed.')
            return
        else:
            logging.info('there is no DTplay thread.')

    def start_dvbs_stream(self, video_name, video_format='ts', scan_format='DVBS', freq=1150, symbol_rate=38000000):
        self.remove_tmp_log()
        file_path = self.get_file_path(video_format, video_name)
        logging.info(f"file_path: {file_path}")
        self.record_video_path(file_path)
        self.record_video_information(file_path)
        self.start_send(self.TYPE, file_path[0], mf=freq, mt=scan_format, r=symbol_rate, l=self.LOOP, ml=self.OUTPUT_LEVEL)

    def start_dvbt_stream(self, video_name, video_format='trp', scan_format='DVBT', freq=474, band_width='8MHZ', mode='QAM256', fft_size='2K', G_I='1_32', code_rate='1_2'):
        """
        start dvb-s stream

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
        self.remove_tmp_log()
        file_path = self.get_file_path(video_format, video_name)
        logging.info(f"file_path: {file_path}")
        self.record_video_path(file_path)
        self.record_video_information(file_path)
        self.start_send(self.TYPE, file_path[0].rstrip('\r'), mf=freq, mt=scan_format, mB=band_width, mC=mode, mT=fft_size, mG=G_I, mc=code_rate, l=self.LOOP, ml=self.OUTPUT_LEVEL)

    def resume_dvbt_stream(self, video_name, video_format='trp', scan_format='DVBT', freq=474, band_width='8MHZ', mode='QAM256', fft_size='2K', G_I='1_32', code_rate='1_2'):
        """
        resume dvb-s stream

        Args:
            freq: TS player frequency
            video_format: ts, mp4, and so on.
            video_name: video name.
            scan_format: DVBT, DVBT2
            band_width: 1_7MHZ, 5MHZ, 6MHZ, 8MHZ, 10MHZ, ...
            fft_size: 1K, 2K, 4K, 8K, 16K, 32K, ...
            mode: BPSK, QPASK, QAM16, QAM64, QAM256, ...

        Returns:
            None
        """
        file_path = self.get_file_path(video_format, video_name)
        logging.info(f"file_path: {file_path}")
        self.start_send(self.TYPE, file_path[0].rstrip('\r'), mf=freq, mt=scan_format, mB=band_width, mC=mode, mT=fft_size, mG=G_I, mc=code_rate, l=self.LOOP, ml=self.OUTPUT_LEVEL)

    def record_video_path(self, file_path):
        '''

        Args:
            file_path: video path that for streaming

        Returns:
            Recording file path and video channel number in dvb.log
        '''
        video_log_filter = 'ffprobe -print_format json -show_format -v quiet'
        video_channel_number = self.ssh_pipe.send_cmd(f'{video_log_filter} {file_path[0]} | grep nb_programs')[0]
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

