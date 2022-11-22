import logging
import re
import subprocess
import threading
import time
from lib.common.system.Permission import Permission
from lib.common.system.ADB import ADB
from util.Decorators import stop_thread


class ProbeInfo(ADB):
    CMD_SET_PERIOD = 'setprop vendor.media.probe.period 1000'
    CMD_INFO = 'logcat -s amlsource | grep ReportProbe'
    AMLSOURCE = 'setprop media.ammediaplayer.enable 1;setprop iptv.streamtype 1'

    Subtitle_ProbeInfo = ["Subtitle Height", "Subtitle Width", 'Subtitle iso639Code',
                          'Subtitle invalid timestamp count',
                          'Subtitle invalid data count', 'Subtitle available count']

    Total_VideoDecoderStats = ['Video type name', 'Video Height', 'Video Width', 'Video pixelAspectRatio',
                               'Video activeFormatDescription', 'Video displayed frames', 'Video decoder error count',
                               'Video overflow count', 'Video underflow count', 'Video dropped frames',
                               'Video invalid timestamp count', 'Video invalid data count', 'Video FrameRate',
                               'Video DecodedFrames', 'Video LostFrames', 'Video ConcealedFrames',
                               'Video IDecodedFrames', 'Video ILostFrames', 'Video IConcealedFrames',
                               'Video PDecodedFrames', 'Video PLostFrames', 'Video PConcealedFrames',
                               'Video BDecodedFrames', 'Video BLostFrames', 'Video BConcealedFrames',
                               'Video AVResynchCounter', 'Video ContentAspectRatio']
    Total_AudioDecoderStats = ['Audio SampleRate:', 'Audio numChannels', 'Audio channelConfiguration',
                               'Audio decoded frames', 'Audio output frames', 'Audio decoded error count',
                               'Audio overflow count', 'Audio underflow count', 'Audio discarded frames',
                               'Audio codec capacility', 'Audio invalid timestamp count', 'Audio invalid data count']

    def __init__(self):
        super(ProbeInfo, self).__init__()
        self.permission = Permission()
        self.error_count = 0
        self.encode_type_str = ''
        self.fps_str = ''
        self.sampleRate_str = ''
        self.video_info = []

    def probe_info_logcat(self):
        logcat_file = open(self.logdir + '/info.log', 'w')
        cmd = 'adb -s ' + self.serialnumber + ' shell logcat -s amlsource | grep ReportProbe'
        log = subprocess.Popen(cmd.split(), stdout=logcat_file)
        time.sleep(3)
        self.stop_save_logcat(log, logcat_file)
        # with open(logcat_file.name, 'r') as f:
        #     result = f.read()
        # return result

    def check_probe_info(self):
        t = 0
        with open(self.logdir + '/info.log', 'r') as f:
            total_info = f.read()
        # 1.check logcat probe info
        for i in self.Subtitle_ProbeInfo:
            if i not in total_info:
                logging.info(f'no this probe info--{i}')
                self.error_count += 1
        for i in self.Total_VideoDecoderStats:
            if i not in total_info:
                logging.info(f'no this probe info--{i}')
                self.error_count += 1
            # 2.check basic probe info data
            else:
                # self.video_info = [self.encode_type_str, self.resolution_str[1], self.resolution_str[0],self.fps_str]
                video_basicProbe = ["Video type name", 'Video Height', "Video Width", 'Video FrameRate']
                if i in video_basicProbe:
                    if i == video_basicProbe[0]:
                        temp_data = re.findall(rf'{video_basicProbe[t]}: \S\((\S*)\)', total_info)[0]
                    else:
                        temp_data = re.findall(rf'{video_basicProbe[t]}: (\d*)', total_info)[0]
                    if temp_data != self.video_info[t]:
                        self.error_count += 1
                        logging.info(
                            f'probe info data: {video_basicProbe[t]} is different from the ffmpeg parsed video info')
                    t += 1
        for i in self.Total_AudioDecoderStats:
            if i not in total_info:
                logging.info(f'no this probe info--{i}')
            else:
                if i == "Audio SampleRate:":
                    sampleRate = re.findall(r'Audio SampleRate: (\d*)', total_info)[0]
                    if sampleRate != self.sampleRate_str:
                        self.error_count += 1
                        logging.info('probe info data is different from the ffmpeg parsed audio info')

    def get_video_info(self, video_file=''):
        # video_file = 'iptv_test.ts'
        # pull video_file to pc
        rc, output = self.run_terminal_cmd("ffprobe " + self.logdir + '/' + video_file, output_stderr=True)
        for line in output:
            linestr = line.decode('utf-8')
            logging.info(f"linestr: {linestr}")
            if 'Video:' in linestr:
                encode_type_str = re.findall(r'Video: (\w+)', linestr)[0].upper()
                self.video_info.append(encode_type_str)
                self.resolution_str = re.findall(r'([0-9]{3,4})x([0-9]{3,4})', linestr)[0]
                self.fps_str = str(round(float(re.findall(r', (\d*.\d*) fps', linestr)[0])))
                self.video_info = [encode_type_str, self.resolution_str[1], self.resolution_str[0], self.fps_str]
                logging.info(
                    f'video info: encode_type--{encode_type_str}, resolution--{self.resolution_str}, fps--{self.fps_str}')
            if 'Audio' in linestr:
                self.sampleRate_str = re.findall(r'(\d*) Hz', linestr)[0]
                logging.info(f'audio info: sampleRate--{self.sampleRate_str}Hz')
        return self.video_info

    def logcat(self):
        while True:
            self.probe_info_logcat()

    def start_logcat_thread(self):
        if not hasattr(self, 's'):
            self.s = threading.Thread(target=self.logcat,
                                      name='logcat')
            logging.info('startLogcatThread')
            self.s.setDaemon(True)
            self.s.start()

    def stop_logcat_thread(self):
        if isinstance(self.s, threading.Thread):
            logging.info('stopLogcatThread')
            stop_thread(self.s)

    def check_probe_decodedata(self, status=''):
        # video play or other status
        with open(self.logdir + '/info.log', 'r') as f:
            result = f.read()
        self.decode_probe = ['Video displayed frames', 'Video DecodedFrames', 'Video IDecodedFrames',
                             'Video PDecodedFrames', 'Video BDecodedFrames', 'Audio decoded frames',
                             'Audio output frames']
        # 3.check decode probe info data
        for decode_probe in self.decode_probe:
            if decode_probe in result:
                probe = re.findall(rf'{decode_probe}: (\d*)', result)
                logging.info(f'{decode_probe}:' + str(probe))
                for i in range(len(probe) - 1):
                    if status == 'video_play':
                        if int(probe[i + 1]) <= int(probe[i]):
                            logging.info(f'please check "{decode_probe}" decode data in probe info ')
                            self.error_count += 1
                    elif status == 'video_stop':
                        if int(probe[i + 1]) != int(probe[i]):
                            logging.info(f'please check "{decode_probe}" decode data in probe info ')
                            self.error_count += 1
                    else:
                        # TODO other status probe info check
                        pass

            else:
                self.error_count += 1
