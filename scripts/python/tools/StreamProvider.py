#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/2/21 13:29
# @Author  : chao.li
# @Site    :
# @File    : StreamProvider.py
# @Software: PyCharm
import signal
import subprocess
import logging
import os
import threading
import select
import time
import re
# from lib.common.system.ADB import ADB
from lib.common.system.SSH import SSH
from lib.common.system.NetworkAuxiliary import getIfconfig


class StreamProvider():
    VLC_VERSION_COMMAND = '/snap/bin/vlc --version'
    DTPLAY_COMMAND = 'DtPlay'
    # DTPLAY_PATH = '~/workdir/DTU-315/sample/DtPlay_v4.13.0'
    DTPLAY_PATH = '~/work/dta-2115b/DtPlay_v4.15.0'

    def __init__(self, ip="192.168.1.247", service="vlc"):
        '''
        vlc pc is 192.168.1.102
        vlc setup
        exit after play enc
        only playback 30 seconds

        StreamProvider.py will exit after vlc command exit (over 30 seconds)
        '''
        self.ssh_pipe = self.ssh_connect(ip, service)
        self.root_path = self.ssh_pipe.send_cmd('pwd')[0].strip()
        # logging.info(f"self.root_path: {self.root_path}")
        if service == "vlc":
            self.video_root_path = self.root_path + '/video'
            # self.open_vlc()
        else:
            # self.video_root_path = self.root_path + '/workdir/DTU-315/sample'
            self.video_root_path = self.root_path + '/work/dta-2115b'
        self._thread = None

    def ssh_connect(self, ip, service):
        # check sh or sz node
        iplist = getIfconfig()
        device_ip_sz = "192.168.1.246"
        try:
            if service == "vlc":
                if device_ip_sz in iplist:
                    # shenzhen
                    ssh_pipe = SSH(ip, uname='amlogic', passwd='Linux2017')
                else:
                    # shanghai
                    ip = "192.168.1.102"
                    ssh_pipe = SSH(ip, uname='aml', passwd='Linux2021')
            else:
                ssh_pipe = SSH(ip, uname='amlogic', passwd='Linux2020')
        except Exception as e:
            logging.info("Can't connect ssh")
            raise Exception("ssh unable to connect")
        finally:
            logging.info("Connected ssh")
            return ssh_pipe

    def open_vlc(self):
        try:
            self.ssh_pipe.send_cmd(self.VLC_VERSION_COMMAND)
        except Exception as e:
            logging.info("Can't find vlc command,pls check")
            raise EnvironmentError('vlc is not installed')

    def get_file_path(self, video_path, video_format, *args):
        '''
        find video path which match condition
        @param video_format: such mp4 or ts,which format you want search
        @param args: filename re
        @return: list with file path
        '''
        target_name = ""
        if args:
            target_name = ' '.join([f"-a -name '*{a}*'" for a in args])
        find_command = f"find {self.video_root_path}/{video_path} -name '*.{video_format}' {target_name} -not -name '.*'"
        logging.info(f"find_command: {find_command}")
        if not self.ssh_pipe.send_cmd(find_command):
            raise IOError("can't find the video.")
        else:
            res = self.ssh_pipe.send_cmd(find_command)[0]
        return res.split('\n')[:-1]

    def start_send(self, protocol, file_path, iswait=False, **kwargs):
        self._thread = None
        if not file_path:
            raise IOError("pls set local playback file path.")
        if not isinstance(self._thread, threading.Thread):
            if "QAM64" not in protocol:
                self._thread = threading.Thread(target=self._start_send, args=(protocol, file_path),
                                                name='vlc_stream')
            else:
                self._thread = threading.Thread(target=self._start_send, args=(protocol, file_path),
                                                kwargs={**kwargs},
                                                name='dvb_stream')
            self._thread.setDaemon(True)
            self._thread.start()
        if iswait:
            time.sleep(2)

    def _start_live555_server(self):
        '''
        run live555
        video should put in /home/coco/live/mediaServer/video/
        multiple player use path rtsp://192.168.50.240:8554/video/DRA_MTV.ts to play
        @return:
        '''
        iplist = getIfconfig()
        if "192.168.1.100" in iplist:
            self.live555_popen = self.ssh_pipe.send_cmd('cd /home/aml/live/mediaServer;./live555MediaServer')
        else:
            self.live555_popen = self.ssh_pipe.send_cmd('cd /home/amlogic/live/mediaServer;./live555MediaServer')
        time.sleep(3)

    def _start_dektec_dtu_315_server(self, file_path, **kwargs):
        '''
        run dtplay
        DtPlay myfile.ts -r 38000000 -t 100 -n 2 -m RAW
        @param file_path: file path
        @param kwargs: -r xxx -t xxx ...
        @return:
        '''
        value = ''.join([f'-{k} {v} ' for k, v in kwargs.items()])
        cmd = f'{self.DTPLAY_PATH}/{self.DTPLAY_COMMAND} {file_path} {value}'
        logging.info(f"cmd: {cmd}")
        # TODO @chao.li : need verify
        self.dtplay_popen = self.ssh_pipe.send_cmd(cmd)
        time.sleep(3)

    def _stop_popen(self, popen):
        # kill live555
        os.kill(popen, signal.SIGTERM)
        popen.terminate()
        time.sleep(5)

    def _start_send(self, protocol, file_path, **kwargs):
        '''
        stitch vlc command
        @param protocol: udp or rtsp or rtp
        @param file_path: video file path such like /home/amlogic/video/nndj.mp4
        @return: command :str
        '''
        # udp vlc -vvv ~/coco/DRA_MTV.ts --sout='#duplicate{dst=udp{dst=239.1.2.1:1234},dst=display}'
        # rtsp vlc -vvv ~/coco/DRA_MTV.ts --sout='#duplicate{dst=rtp{sdp=rtsp://:8554/1},dst=display}'
        # rtp vlc -vvv ~/coco/DRA_MTV.ts --sout='#duplicate{dst=rtp{dst=239.1.1.1,port=5004,mux=ts},dst=display}'
        command = "/snap/bin/vlc -vvv '%s' --sout='#duplicate{dst=%s,dst=display}' >/dev/null 2>\&1 \&"
        protocol_dict = {
            'udp': 'udp{dst=239.1.2.1:1234}',
            'udp1': 'udp{dst=239.1.2.2:1235}',
            'rtsp': 'rtp{sdp=rtsp://:8554/1}',
            'rtp': 'rtp{dst=239.1.1.1,port=5004,mux=ts}'
        }
        if not file_path:
            raise IOError("pls set local playback file path.")
        if protocol not in ['udp', 'udp1', 'rtsp', 'rtp', 'QAM64']:
            raise ValueError("Doesn't support such protocol , pls select udp|rtsp|rtp")
        try:
            if protocol == 'rtsp':
                # push stream over live555
                self._start_live555_server()
                return
            if protocol == 'QAM64':
                self._start_dektec_dtu_315_server(file_path, **kwargs)
                return
            # channel = self.ssh_pipe.client.get_transport().open_session()
            # channel.exec_command(command % (file_path, protocol_dict[protocol]))
            print(command % (file_path, protocol_dict[protocol]))
            self.ssh_pipe.send_cmd(command % (file_path, protocol_dict[protocol]))
        except Exception as e:
            logging.warning("Can't setup stream")
        # while True:
        #     try:
        #         rl, wl, xl = select.select([channel], [], [], 0.0)
        #         if len(rl) > 0:
        #             print(channel.recv(1024))
        #     except KeyboardInterrupt:
        #         channel.close()
        #         self.ssh_pipe.client.close()
        #     time.sleep(1)

    def stop_send(self):
        '''
        kill the streaming thread at the end of case execution
        @return:
        '''
        p_lookup_vlc_thread_cmd = 'ps -e | grep vlc'
        p_vlc_thread_list = self.ssh_pipe.send_cmd(p_lookup_vlc_thread_cmd)[0].strip()
        logging.info(f'vlc thread:{p_vlc_thread_list}')
        if 'vlc' in p_vlc_thread_list:
            p_vlc_pid = re.search('(.*?) vlc', p_vlc_thread_list, re.M | re.I).group(1).strip().split(" ")[0]
            self.ssh_pipe.send_cmd(f'kill {p_vlc_pid}')
            logging.info(f'vlc thread:{p_vlc_pid} is killed.')
            return
        else:
            logging.info('there is no vlc thread.')
        p_lookup_live555_thread_cmd = 'ps -e | grep live555'
        p_live555_thread_list = self.ssh_pipe.send_cmd(p_lookup_live555_thread_cmd)[0].strip()
        logging.info(f'live555 thread:{p_live555_thread_list}')
        if 'live555MediaSer' in p_live555_thread_list:
            # self._stop_popen(self.live555_popen)
            p_live555_pid = re.search('(.*?) live555MediaSer', p_live555_thread_list, re.M | re.I).group(1).strip().split(" ")[0]
            self.ssh_pipe.send_cmd(f'kill {p_live555_pid}')
            logging.info(f'live555 thread:{p_live555_pid} is killed.')
            return
        else:
            logging.info('there is no live555 thread.')
        p_lookup_dtplay_thread_cmd = 'ps -e | grep Dtplay'
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

# # stream demo
# vlc = StreamProvider()
# file_path = vlc.get_file_path('MP4', 'SiSTAR')[0]
# vlc.start_send('rtp', file_path)
# vlc.start_send('rtp', file_path,r=38000000,t=100,n=2,m=RAW)
# # Todo
# print('Continue do some test action')
