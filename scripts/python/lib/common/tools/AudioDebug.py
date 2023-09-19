import logging
import os
import shutil
import threading
import time
import zipfile
from pathlib import Path

from lib.common.system.ADB import ADB

adb = ADB()


class AudioDebugCfg:
    def __init__(self):
        self.m_capture_mode = 0
        self.m_debug_info_enable = 0
        self.m_dump_data_enable = 0
        self.m_logcat_enable = 0
        self.m_tombstone_enable = 0
        self.m_print_debug_enable = 0
        self.m_auto_debug_times = 0
        self.m_create_zipfile = 0
        self.m_home_click = False


class AmlAudioDebug(AudioDebugCfg):
    DEBUG_CAPTURE_MODE_AUTO = 0
    DEBUG_CAPTURE_MODE_MUNUAL = 1
    DEFAULT_CAPTURE_MODE = DEBUG_CAPTURE_MODE_AUTO
    DEFAULT_AUTO_MODE_DUMP_TIME_S = 3

    AML_DEBUG_DIRECOTRY_ROOT = adb.logdir + "/aml_debug"
    AML_DEBUG_PLATFORM_DIRECOTRY_LOGCAT = '/data/logcat.txt'
    AML_DEBUG_PLATFORM_DIRECOTRY_DMESG = '/data/dmesg.txt'
    AML_DEBUG_PLATFORM_DIRECOTRY_TOMBSTONE = '/data/tombstones/'
    AML_DEBUG_PLATFORM_DIRECOTRY_COMMON_INFO = '/data/common_info.txt'
    AML_DEBUG_TOOL_ICO_PATH = ':/debug.ico'
    AML_DEBUG_DIRECOTRY_CONFIG = AML_DEBUG_DIRECOTRY_ROOT + '/config.ini'

    AML_DEBUG_MODULE_AUDIO = 1

    moduleDirPathDict = {
        AML_DEBUG_MODULE_AUDIO: 'audio'
    }

    AML_DEBUG_LOG_LEVEL_V = 'V'
    AML_DEBUG_LOG_LEVEL_D = 'D'
    AML_DEBUG_LOG_LEVEL_I = 'I'
    AML_DEBUG_LOG_LEVEL_W = 'W'
    AML_DEBUG_LOG_LEVEL_E = 'E'
    AML_DEBUG_LOG_LEVEL_F = 'F'

    log_func = print
    adb_cur_dev = ''

    def __init__(self):
        # self.log = log_fuc
        super().__init__()
        # self.__debugCfg = AudioDebugCfg()
        self.RUN_STATE_STARTED = 1
        self.RUN_STATE_STOPED = 2
        self._cur_state = -1
        self._m_isplaying = False
        self._dump_cmd_outfilepath = '/data/dump_audio.log'
        self._adb_dump_cmdlists = [
            'cat /proc/asound/cards',
            'cat /proc/asound/pcm',
            'cat /proc/asound/card0/pcm*c/sub0/status',
            'cat /proc/asound/card0/pcm*c/sub0/hw_params',
            'cat /proc/asound/card0/pcm*c/sub0/sw_params',
            'cat /proc/asound/card0/pcm*p/sub0/status',
            'cat /proc/asound/card0/pcm*p/sub0/hw_params',
            'cat /proc/asound/card0/pcm*p/sub0/sw_params',
            'cat /sys/class/amhdmitx/amhdmitx0/aud_cap',
            'cat /sys/class/amaudio/dts_enable',
            'cat /sys/class/amaudio/dolby_enable',
            'ls -al /odm/lib/*Hw*',
            'ls -al /vendor/lib/*Hw*',
            'dumpsys hdmi_control',
            'dumpsys media.audio_policy',
            'dumpsys audio',
            'dumpsys media.audio_flinger',
            'tinymix'
        ]

        self._adb_dump_dataclear_cmdlists = [
            'setenforce 0',
            'touch /data/audio_spk.pcm /data/audio_dtv.pcm /data/alsa_pcm_write.pcm',
            'mkdir /data/audio /data/audio_out /data/vendor/audiohal/ -p',
            'chmod 777 /data/audio /data/audio_out /data/vendor/audiohal/ /data/audio_spk.pcm /data/audio_dtv.pcm /data/alsa_pcm_write.pcm',
            'rm /data/audio/* /data/vendor/audiohal/* -rf',
            'rm ' + self._dump_cmd_outfilepath + ' -rf',
            'rm ' + self.AML_DEBUG_PLATFORM_DIRECOTRY_COMMON_INFO + ' -rf',
        ]

        self._adb_dump_data_startlists = [
            'setprop vendor.media.audiohal.indump 1',
            'setprop vendor.media.audiohal.outdump 1',
            'setprop vendor.media.audiohal.alsadump 1',
            'setprop vendor.media.audiohal.a2dpdump 1',
            'setprop vendor.media.audiohal.tvdump 1',
            'setprop vendor.media.audiohal.btpcm 1',
            'setprop vendor.media.audiohal.ms12dump 0xfff',
            'setprop media.audiohal.indump 1',
            'setprop media.audiohal.outdump 1',
            'setprop media.audiohal.alsadump 1',
            'setprop media.audiohal.a2dpdump 1',
            'setprop media.audiohal.ms12dump 0xfff',
        ]

        self._adb_dump_data_stoplists = [
            'setprop vendor.media.audiohal.indump 0',
            'setprop vendor.media.audiohal.outdump 0',
            'setprop vendor.media.audiohal.alsadump 0',
            'setprop vendor.media.audiohal.a2dpdump 0',
            'setprop vendor.media.audiohal.btpcm 0',
            'setprop vendor.media.audiohal.ms12dump 0',
            'setprop vendor.media.audiohal.tvdump 0',
            'setprop media.audiohal.indump 0',
            'setprop media.audiohal.outdump 0',
            'setprop media.audiohal.alsadump 0',
            'setprop media.audiohal.a2dpdump 0',
            'setprop media.audiohal.ms12dump 0',
        ]

        self._adb_logcat_startlists = [
            'setprop vendor.media.audio.hal.debug 4096',
            'setprop media.audio.hal.debug 4096',
        ]

        self._adb_logcat_stoplists = [
            'setprop vendor.media.audio.hal.debug 0',
            'setprop media.audio.hal.debug 0',
        ]

        self._dump_filelists = [
            'vendor/etc/audio_policy_configuration.xml',
            'vendor/etc/audio_policy_volumes.xml',
            '/data/audio',
            '/data/audio_out',
            '/data/vendor/audiohal/',
            self._dump_cmd_outfilepath,
            self.AML_DEBUG_PLATFORM_DIRECOTRY_LOGCAT,
        ]
        self._now_pull_pcpath = ''
        self._now_pull_pctime = ''

    def log(self, info, level='D'):
        print(level + ' [AUDIO] ' + info)

    def start_capture(self):
        if self.m_capture_mode == self.DEBUG_CAPTURE_MODE_AUTO:
            self.log('Auto mode: Start to capture the info...')
        elif self.m_capture_mode == self.DEBUG_CAPTURE_MODE_MUNUAL:
            self.log('Manual mode: Start to capture the info...')
        if self._cur_state == self.RUN_STATE_STARTED:
            self.log('current already started, do nothing', self.AML_DEBUG_LOG_LEVEL_I)
            return
        self._cur_state = self.RUN_STATE_STARTED
        # 1. Create the audio dump directory on PC, and prepare env to debug.
        self._now_pull_pctime = self.pre_create_directory(self.AML_DEBUG_MODULE_AUDIO)
        self._now_pull_pcpath = self.get_path_by_module(self._now_pull_pctime, self.AML_DEBUG_MODULE_AUDIO)

        self._prepare_debug_env()
        curpath = self.AML_DEBUG_DIRECOTRY_ROOT + '/' + self._now_pull_pctime
        if not self.m_home_click:
            self.cap_common_debug_info(curpath)
        if self.m_logcat_enable and self.m_home_click == False:
            # open the audio hal debug level for capture logcat
            self._capture_logcat_enable_prop()
        if self.m_capture_mode == self.DEBUG_CAPTURE_MODE_AUTO:
            # 2. Capture the debug info and write it to txt file.
            self._capture_debug_text()
        if self.m_logcat_enable and self.m_home_click == False:
            self.logcat_start()
        # 4. Capture the audio data.
        self._capture_audio_data_start()

        if self.m_capture_mode == self.DEBUG_CAPTURE_MODE_AUTO:
            if self.m_logcat_enable and self.m_home_click == False:
                if not self.m_dump_data_enable:
                    self.log('3.1 Please wait ' + str(self.m_auto_debug_times) + 's for logcat...')
                    time.sleep(self.m_auto_debug_times)
                else:
                    self.log('3.1 Start auto capture logcat...')
                # 5. Kill the logcat thread, stop logcat.
                self.log('3.2 Stop auto capture logcat...')
                # self.__capture_logcat_disable_prop()
                adb.run_shell_cmd('setprop vendor.media.audio.hal.debug 0;setprop media.audio.hal.debug 0')
                self.logcat_stop()
            if not self.m_home_click:
                self.cap_common_debug_info(curpath)
            # 6. Pull the all debug files to PC
            if not self.m_home_click:
                self.pull_common_info_to_pc(curpath)
            self._pull_capture_debug_info_to_pc()
            self._print_help_info()
            self._cur_state = self.RUN_STATE_STOPED
            self._capture_clear_all_files()

    def stop_capture(self, stopcaptureFinish):
        if self._cur_state != self.RUN_STATE_STARTED:
            self.log('stop_capture: current no start, do nothing')
            return
        if self.m_capture_mode != AmlAudioDebug.DEBUG_CAPTURE_MODE_MUNUAL:
            self.log('stop_capture: current not MUNAUL mode, not support stop!!!')
            return
        self._manual_capture_stop()
        stopcaptureFinish()

    def open_logcat(self):
        self._capture_logcat_enable_prop()

    def close_logcat(self):
        self._capture_logcat_disable_prop()

    def _manual_capture_stop(self):
        curpath = self.AML_DEBUG_DIRECOTRY_ROOT + '\\' + self._now_pull_pctime
        self.log('2.2 MUNUAL mode: fetching the audio data end.')
        if self.m_dump_data_enable:
            self._capture_audio_data_prop_disable()
        if self.m_logcat_enable and self.m_home_click == False:
            self.log('3.2 Stop manual capture logcat...')
            self._capture_logcat_disable_prop()

        if self.m_debug_info_enable:
            self._capture_debug_text()
        if not self.m_home_click:
            self.cap_common_debug_info(curpath)
            self.pull_common_info_to_pc(curpath)
        self._pull_capture_debug_info_to_pc()
        self._print_help_info()
        self._cur_state = self.RUN_STATE_STOPED

    def getCurDebugPath(self):
        return self._now_pull_pcpath

    def _capture_debug_text(self):
        if not self.m_debug_info_enable:
            return
        self.log('1.1 Please wait a moment, starting to dump debugging information...')
        self.log('1.2 Cat the some info to ' + self._dump_cmd_outfilepath + ' file')
        dumpCmdListTemp = []
        for adbDumpCmd in self._adb_dump_cmdlists:
            dumpCmdListTemp.append('echo ' + adbDumpCmd + ' >> ' + self._dump_cmd_outfilepath)
            dumpCmdListTemp.append(adbDumpCmd + ' >> ' + self._dump_cmd_outfilepath)
        self._exe_adb_shell_cmd(dumpCmdListTemp)

    def _capture_audio_data_start(self):
        if not self.m_dump_data_enable:
            return
        self._capture_audio_data_prop_enable()
        self.log('2.1 AUTO mode: Start fetching the audio data, wait for ' + str(
            self.m_auto_debug_times) + ' seconds...')
        if self.m_capture_mode == self.DEBUG_CAPTURE_MODE_AUTO:
            time.sleep(self.m_auto_debug_times)
            self._capture_audio_data_prop_disable()
            self.log('2.2 AUTO mode: fetching the audio data end.')

    def _prepare_debug_env(self):
        if not self.m_home_click:
            self._capture_logcat_disable_prop()

        self._capture_audio_data_prop_disable()
        self._capture_clear_all_files()

    def _pull_capture_debug_info_to_pc(self):
        self.log('Pull all file to PC ...')
        curpath = self.AML_DEBUG_DIRECOTRY_ROOT + '/' + self._now_pull_pctime
        for dumpFile in self._dump_filelists:
            if (((self.m_home_click == True or self.m_logcat_enable == False)
                 and dumpFile == self.AML_DEBUG_PLATFORM_DIRECOTRY_LOGCAT)
                    or (self.m_dump_data_enable == False and self._dump_cmd_outfilepath == dumpFile)):
                continue
            exeCmdStr = 'pull ' + dumpFile + ' ' + self._now_pull_pcpath
            adb.pull(dumpFile, self._now_pull_pcpath)
        if self.m_tombstone_enable and self.m_home_click == False:
            self.pull_tombstones_to_pc(curpath)

        if self.m_create_zipfile:
            zip_src_dir = self.AML_DEBUG_DIRECOTRY_ROOT + '/' + self._now_pull_pctime
            zip_dst_file = self.AML_DEBUG_DIRECOTRY_ROOT + '/' + self._now_pull_pctime + '.zip'
            self.log('Zipping director:' + zip_src_dir + ' to ' + zip_dst_file)
            self.zip_compress(zip_src_dir, zip_dst_file)
            shutil.rmtree(zip_src_dir, ignore_errors=True)
            # shutil.move(zip_dst_dir, self.__nowPullPcPath)

    def _capture_audio_data_prop_enable(self):
        self._exe_adb_shell_cmd(self._adb_dump_data_startlists)

    def _capture_audio_data_prop_disable(self):
        self._exe_adb_shell_cmd(self._adb_dump_data_stoplists)

    def _capture_clear_all_files(self):
        if not self.m_home_click:
            adb.run_shell_cmd('rm ' + self.AML_DEBUG_PLATFORM_DIRECOTRY_LOGCAT + ' -rf',
                              self.m_print_debug_enable)
        self._exe_adb_shell_cmd(self._adb_dump_dataclear_cmdlists)

    def _capture_logcat_enable_prop(self):
        self._exe_adb_shell_cmd(self._adb_logcat_startlists)

    def _capture_logcat_disable_prop(self):
        self._exe_adb_shell_cmd(self._adb_logcat_stoplists)

    def _exe_adb_shell_cmd(self, cmdLists):
        exeCmdStr = ''
        for i, cmd in enumerate(cmdLists):
            # print(cmd)
            exeCmdStr += cmd + ';'
            if self.m_print_debug_enable and 'echo' not in cmd:
                logging.info(cmd)
        adb.run_shell_cmd(exeCmdStr)

    def _print_help_info(self):
        if self.m_create_zipfile:
            target_file = self.AML_DEBUG_DIRECOTRY_ROOT + '/' + self._now_pull_pctime + '.zip'
        else:
            target_file = self._now_pull_pcpath
        print('###############################################################################################')
        print('##                                                                                           ##')
        print('##  Please send folder %-40s' % target_file + ' to RD colleagues! Thank You! ##')
        print('##                                                                                           ##')
        print('###############################################################################################')
        self.log('Please send folder ' + target_file + ' to RD colleagues! Thank You!', self.AML_DEBUG_LOG_LEVEL_I)

    def pre_create_directory(self, createByModule):
        if not Path(self.AML_DEBUG_DIRECOTRY_ROOT).exists():
            self.log(self.AML_DEBUG_DIRECOTRY_ROOT + " folder does not exist, create it.",
                     self.AML_DEBUG_LOG_LEVEL_I)
            os.mkdir(self.AML_DEBUG_DIRECOTRY_ROOT)
            os.system('chmod -R 777 ' + self.AML_DEBUG_DIRECOTRY_ROOT)
        curTime = time.strftime("%Y%m%d_%H-%M-%S", time.localtime())
        curPullPcTimePath = self.AML_DEBUG_DIRECOTRY_ROOT + "/" + curTime
        self.log('pre_create_directory Current date:' + \
                 time.strftime("%Y-%m-%d %H:%M:%S",
                               time.localtime()) + ', directory is: ' + curPullPcTimePath,
                 self.AML_DEBUG_LOG_LEVEL_I)
        # os.makedirs(curPullPcTimePath)
        os.mkdir(curPullPcTimePath)
        os.system('chmod -R 777 ' + curPullPcTimePath)
        if createByModule in self.moduleDirPathDict:
            modulePath = curPullPcTimePath + "/" + self.moduleDirPathDict[createByModule]
            os.mkdir(modulePath)
            os.system('chmod -R 777 ' + modulePath)
            self.log('pre_create_directory create:' + modulePath)
        else:
            self.log('__pre_create_directory: createByModule:' + createByModule + ' invalid.',
                     self.AML_DEBUG_LOG_LEVEL_E)
        return curTime

    def get_path_by_module(self, time, id):
        return self.AML_DEBUG_DIRECOTRY_ROOT + "/" + time + "/" + self.moduleDirPathDict[id]

    def cap_common_debug_info(self, pc_path):
        adb.run_shell_cmd(
            'echo ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ >> '
            + self.AML_DEBUG_PLATFORM_DIRECOTRY_COMMON_INFO)
        adb.run_shell_cmd('date >> ' + self.AML_DEBUG_PLATFORM_DIRECOTRY_COMMON_INFO)
        adb.run_shell_cmd('ps -ef >> ' + self.AML_DEBUG_PLATFORM_DIRECOTRY_COMMON_INFO)

    def logcat_start(self, callbackFinish='', delayEndS=-1):
        logcatProcThread = threading.Thread(target=self._logcat_wait_thread,
                                            args=(callbackFinish, delayEndS))
        logcatProcThread.setDaemon(True)
        logcatProcThread.start()
        # logcatProcThread.join()

    def _logcat_wait_thread(self, callbackFinish, delayEndS):
        self.log('__logcat_wait_thread: time:' + str(delayEndS) + 's, logcat loading...',
                 self.AML_DEBUG_LOG_LEVEL_I)

        logcatProcThread = threading.Thread(target=self._logcat_run_thread)
        logcatProcThread.setDaemon(True)
        logcatProcThread.start()
        if delayEndS != -1:
            time.sleep(delayEndS)
            self.logcat_stop()
            # callbackFinish()

    def _logcat_run_thread(self):
        self.log('__logcat_run_thread: Start logcat+++++')
        adb.run_shell_cmd(
            'logcat -G 40M;logcat -c;logcat >> ' + self.AML_DEBUG_PLATFORM_DIRECOTRY_LOGCAT)
        self.log('__logcat_run_thread: Exit logcat------')

    def logcat_stop(self):
        adb.run_shell_cmd("ps -ef |grep -v grep|grep logcat| awk '{print $2}'|xargs kill -9")

    def pull_common_info_to_pc(self, pc_path):
        adb.pull(self.AML_DEBUG_PLATFORM_DIRECOTRY_COMMON_INFO, pc_path)

    def pull_tombstones_to_pc(self, pc_path):
        adb.run_shell_cmd('pull "' + self.AML_DEBUG_PLATFORM_DIRECOTRY_TOMBSTONE + '" ' + pc_path,
                          True)

    @staticmethod
    def zip_compress(srcPathName, targetPathName):
        z = zipfile.ZipFile(targetPathName, 'w', zipfile.ZIP_DEFLATED)
        for dirpath, dirnames, filenames in os.walk(srcPathName):
            fpath = dirpath.replace(srcPathName, '')
            fpath = fpath and fpath + os.sep or ''
            for filename in filenames:
                z.write(os.path.join(dirpath, filename), fpath + filename)
        z.close()
