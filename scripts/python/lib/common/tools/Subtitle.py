import os
import re
import signal
import threading
from random import Random
from lib.common.system.Permission import Permission
from lib.common.system.ADB import ADB
import logging
import time
from util.Decorators import set_timeout, stop_thread


class Subtitle(ADB):
    CMD_INSIDE_COMMAND = 'logcat -s SubtitleViewAdaptor | grep showText'
    CMD_EXTRA_COMMAND = 'logcat -s SubtitleViewAdaptor | grep showBitmap'
    direction_dict = {
        'extra': "showBitmap",
        'inside': "showText"
    }
    CMD_SCTE35 = "shell logcat -s amlsource | grep AmlPlayerScte35Parser"

    def __init__(self):
        super(Subtitle, self).__init__()
        self.flag = True
        self.error = 0
        self.got_spu = ''
        self.show_spu = ''
        self.got_spu_pts = []
        self.show_spu_pts = []
        self.subtitle_window = ''
        self._subtitleCheckCmdLists = [
            '-s Presentation',
            '-s Presentation | grep "Show SPU"',
            '-s SubtitleRender | grep AndroidHidlRemoteRender',
            '-s SubtitleServer | grep postDisplayData',
            '-s SubtitleManager | grep CC_text',
            '-s SubtitleManager | grep DisplayRect',
            '-s SubtitleViewAdaptor | grep "showBitmap:w-"',
            '-s TeletextParser | grep "get_dvb_teletext_spu"',
            '-s Scte27Parser | grep langCallback',
            '-s CCSubtitleView | grep "showJsonStr"',
            '-s DvbParser | grep dvbsub_decode',
            '-s TeletextParser | grep "get_dvb_teletext_spu"',
        ]

        self.scte35Parser_keywords = [
            'splice section received',
            'Command type',
            'notifySpliceInsert'
        ]

    # @set_timeout(300)
    def check_subtitle(self, logcat_tag='SubtitleViewAdaptor'):
        """check play subtitle"""
        logging.info('Cheking subtitle info')
        logcat = self.popen('logcat -s ' + logcat_tag)
        for subtitle_type in self.direction_dict.keys():
            logging.debug(subtitle_type)
        while True:
            line = logcat.stdout.readline()
            if 'unexpected EOF!' in line:
                raise ValueError('logcat buffer crash ,no data in file')
            info = ''
            if "showBitmap:w-" in line:
                logging.info("extra subtitle")
                info = re.findall(r'showBitmap:w-(\d*), h-(\d*)', line, re.S)[0]
            if "showText" in line:
                logging.info("inside subtitle")
                info = re.findall(r'showText:(.*?)', line, re.S)[0]
            logging.info(info)
            if info:
                break

    def check_subtitle_loop(self):
        while True:
            logging.info('start check subtitle loop')
            self.check_subtitle()

    def start_subtitle_thread(self):
        if not hasattr(self, 'b'):
            self.b = threading.Thread(target=self.check_subtitle_loop,
                                      name='subtitleThread')
            self.b.setDaemon(True)
            self.b.start()
            logging.info('startsubtitleThread')

    # def stop_subtitle_thread(self):
    #     if isinstance(self.b, threading.Thread):
    #         logging.info('stopsubtitleThread')
    #         stop_thread(self.b)

    def check_subtitle_dataloop(self, subtitleType, apk_name):
        while True:
            logging.info('start check subtitle loop')
            self.subtitle_check_data(subtitleType, apk_name)
            assert self.flag, 'The subtitle is abnormal.'

    def start_subtitle_datathread(self, subtitleType, apk_name=''):
        self.subtitleThread = threading.Thread(target=self.check_subtitle_dataloop, args=(subtitleType, apk_name),
                                               name='subtitleThread')
        self.subtitleThread.setDaemon(True)
        self.subtitleThread.start()

    def check_subtitle_thread(self, subtitleType='Dvb', apk_name=''):
        self.start_subtitle_datathread(subtitleType, 'LiveTv')
        assert self.subtitleThread.is_alive(), 'The subtitle thread is not alive.'

    def stop_subtitle_data_thread(self):
        if isinstance(self.subtitleThread, threading.Thread):
            logging.info('stopsubtitleThread')
            stop_thread(self.subtitleThread)

    def count_time(self, time_list):
        return int(time_list[0]) * 3600 + int(time_list[1]) * 60 + float(time_list[2])

    def subtitle_check_data(self, subtitle_type='', apk_name='videoplayer'):
        logging.info("subtitle type is: " + subtitle_type)
        self.run_shell_cmd('logcat -G 20m')
        self.gotSpu_time_list = []
        self.showSpu_time_list = []
        for i in range(len(self._subtitleCheckCmdLists)):
            locals()['logcat' + str(i)] = self.popen('shell logcat ' + self._subtitleCheckCmdLists[i])
        i = 0
        start_time = time.time()
        count = 0
        while time.time() - start_time < 10:
            # 1. check spu pts
            line_presentation = locals()['logcat0'].stdout.readline()
            logging.debug(f'line_presentation : {line_presentation}')
            if "Got  SPU: TimeStamp:" in line_presentation:
                logging.debug(line_presentation)
                self.got_spu = \
                    re.findall(
                        r'TimeStamp:(\d*) startAtPts=(\d*) ItemPts=(\d*)\((\d*)\) duration:(\d*)\((\d*)\) data:('
                        r'\S*)\((\S*)\)',
                        line_presentation, re.S)[0]
                self.gotSpu_time_list.append(self.count_time(line_presentation[6:18].split(':')))
                logging.debug(self.gotSpu_time_list)
                # check pts
                if self.got_spu:
                    if int(self.got_spu[3]) < 0:
                        self.error += 1
                        logging.info('got spu <0')
                        break
                    # if int(self.got_spu[6], 0) == 0:
                    #     self.error += 1
                    #     break
                    self.got_spu_pts.append(self.got_spu[3])
                    # if i >= 1:
                    #     if int(self.got_spu_pts[i]) < int(self.got_spu_pts[i - 1]):
                    #         self.error += 1
                    #         logging.info('not ok')
                    # check gotSpu and showSpu print time
                    # if int(self.gotSpu_time_list[i]) < int(self.showSpu_time_list[i - 1]):
                    #     logging.info('please check got_spu info and show_spu info in log')
                    #     self.error += 1
                    # break
                    # i += 1
                # 2. check subtitle to show or not.
                line_presentation_show = locals()['logcat1'].stdout.readline()
                logging.debug(line_presentation_show)
                if "Show SPU:" in line_presentation_show:
                    self.show_spu = \
                        re.findall(
                            r'TimeStamp:(\d*) startAtPts=(\d*) ItemPts=(\d*)\((\d*)\) duration:(\d*)\((\d*)\) data:('
                            r'\S*)\((\S*)\)',
                            line_presentation_show, re.S)[0]
                    logging.debug(self.show_spu)
                    # check pts
                    if self.show_spu:
                        if int(self.show_spu[3]) < 0:
                            self.error += 1
                            logging.info('show_spu pts < 0')
                            break
                    # if self.got_spu[3] != self.show_spu[3] and self.got_spu[7] != self.show_spu[7]:
                    #     self.error += 1

                    self.showSpu_time_list.append(self.count_time(line_presentation_show[6:18].split(':')))
                    logging.debug(self.showSpu_time_list)

                # 3. check SubtitleRender postSubtitleData
                line_render = locals()['logcat2'].stdout.readline()
                logging.debug(line_render)
                if 'in AndroidHidlRemoteRender' in line_render:
                    data_size = re.findall(
                        r'in AndroidHidlRemoteRender:postSubtitleData type:(\d*), width=(\d*), height=(\d*) data=('
                        r'\S*) size=(\d*)',
                        line_render, re.S)[0]
                    if data_size and int(data_size[4]) == 0:
                        self.error += 1
                        logging.info('subtitle data is 0')
                        break

                # 4. check SubtitleServer got postDisplayData
                if apk_name == 'videoplayer':
                    line_server = locals()['logcat3'].stdout.readline()
                    logging.info(f'line_server : {line_server}')
                    if 'postDisplayData' in line_server:
                        postDisplayData = re.findall(
                            r'postDisplayData type:(\d*), width=(\d*), height=(\d*) size=(\S*)',
                            line_server, re.S)[0]
                        logging.info(postDisplayData)
                        if subtitle_type == 'Teletext':
                            logcat_adaptor = locals()['logcat5'].stdout.readline()
                            logging.info(f'logcat_adaptor : {logcat_adaptor}')
                            self.subtitle_window = \
                                re.findall(r'DisplayRect=Rect(.*?) show bitmap scaleW:(\S*), scaleH:(\S*)',
                                           logcat_adaptor,
                                           re.S)[0]
                            logging.info(self.subtitle_window)
                        elif subtitle_type == 'CC':
                            logcat_cc = locals()['logcat4'].stdout.readline()
                            logging.info(f'logcat_adaptor : {logcat_cc}')
                            if 'startSubtitle TEXT CC_text' in logcat_cc:
                                self.subtitle_window = re.findall(
                                    r'startSubtitle TEXT CC_text= {"type":"(\S*)","windows":(\[.*?\])}',
                                    logcat_cc, re.S)[0]
                                logging.debug(self.subtitle_window)
                                if self.subtitle_window:
                                    if self.subtitle_window[1] == '[]':
                                        self.error += 1
                                        logging.info('show subtitle window is null,please check')
                        elif subtitle_type == 'Dvb' or 'Scte27':
                            logcat_adaptor = locals()['logcat6'].stdout.readline()
                            logging.info(f'logcat_adaptor : {logcat_adaptor}')
                            self.subtitle_window = re.findall(r'showBitmap:w-(\d*), h-(\d*)', logcat_adaptor, re.S)[0]
                            logging.debug(self.subtitle_window)
                        else:
                            pass
                elif apk_name == 'LiveTV':
                    if subtitle_type == 'Teletext':
                        TeletextParser = locals()['logcat7'].stdout.readline()
                        logging.debug(f'TeletextParser : {TeletextParser}')
                        self.subtitle_window = re.findall(r'TeletextParser', TeletextParser, re.S)[0]
                        logging.debug(self.subtitle_window)
                    elif subtitle_type == 'CC':
                        CCSubtitleView = locals()['logcat9'].stdout.readline()
                        logging.debug(f'CCSubtitleView : {CCSubtitleView}')
                        self.subtitle_window = re.findall(r'showJsonStr', CCSubtitleView, re.S)[0]
                        logging.debug(self.subtitle_window)
                    elif subtitle_type == 'scte27':
                        Scte27Parser = locals()['logcat8'].stdout.readline()
                        self.subtitle_window = re.findall(r'Scte27Parser', Scte27Parser, re.S)[0]
                        logging.debug(self.subtitle_window)
                    elif subtitle_type == 'Dvb':
                        DvbParser = locals()['logcat10'].stdout.readline()
                        self.subtitle_window = re.findall(r'DvbParser', DvbParser, re.S)[0]
                        logging.debug(self.subtitle_window)
                    elif subtitle_type == 'HOH':
                        HOHParser = locals()['logcat11'].stdout.readline()
                        self.subtitle_window = re.findall(r'HOHParser', HOHParser, re.S)[0]
                        logging.debug(self.subtitle_window)

            # 5. check subtitle show sync or not.
            # if ('2 fade SPU:' in line_presentation) or ('1 fade SPU:' in line_presentation):
            if abs(int(self.got_spu[0]) - int(self.got_spu[3]) / 90000) > 0.5:
                # count += 1
                logging.info(f'video play and subtitle show is not sync: {count}')
                # if count >= 2:
                self.error += 1
        logging.info(
            f'subtitle.error : {self.error}  ;subtitle.got_spu : {self.got_spu}; subtitle.show_spu : {self.show_spu} ; subtitle.subtitle_window: {self.subtitle_window}')
        if (self.error == 0) & (self.got_spu != '') & (self.show_spu != ''):
            logging.info('The subtitle shows is normal.')
        else:
            logging.info('There are some problems with the subtitle shows')
            self.flag = False

    def seek_time(self, video):
        total_time = 0
        duration = ''
        rc, output = self.run_terminal_cmd("ffprobe " + self.logdir + '/' + video, output_stderr=True)
        for line in output:
            linestr = line.decode('utf-8')
            if "Duration:" in linestr:
                logging.info(linestr)
                duration = re.findall(r'Duration: (\d*):(\d*):(\d*.\d*),', linestr)[0]
                break
        if duration != '':
            total_time = (int(float(duration[2]) + int(duration[1]) * 60 + int(duration[0]) * 3600)) * 1000
        return total_time

    def seek_random(self, subtitleType, total_time, seek_repeat_time=1):
        assert seek_repeat_time > 0
        self.clear_logcat()
        if total_time > 0:
            i = 1
            self.start_subtitle_datathread(subtitleType)
            assert self.subtitleThread.is_alive()
            while i <= seek_repeat_time:
                seek_postime = Random().randint(0, total_time)
                if total_time - seek_postime > 10000:
                    logging.info('random seek position is: ' + str(seek_postime))
                    seek_command = "am broadcast -a com.amlogic.vplayer.seekkey --el seek_pos " + str(seek_postime)
                    self.run_shell_cmd(seek_command)
                    time.sleep(10)
                    i += 1
                else:
                    continue
            # self.stop_subtitle_data_thread()
        else:
            logging.info('please check video time')

    # change to teletext graphic pattern and screenshot
    def teletext_check(self):
        self.keyevent('KEYCODE_DPAD_CENTER')
        for i in range(4):
            self.keyevent('KEYCODE_DPAD_RIGHT')
        self.enter()
        for i in range(5):
            self.keyevent('KEYCODE_DPAD_RIGHT')
        self.enter()
        time.sleep(2)
        self.keyevent('KEYCODE_DPAD_DOWN')
        self.keyevent('KEYCODE_DPAD_DOWN')
        self.enter()
        self.keyevent('KEYCODE_DPAD_LEFT')
        self.enter()
        time.sleep(5)
        self.screenshot('teletext', layer="osd+video")
