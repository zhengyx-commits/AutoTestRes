#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time    : 2022/4/13 16:37
# @Author  : chao.li
# @Site    :
# @File    : AudioCheck.py
# @Software: PyCharm

import re
import threading
from lib.common.system.ADB import ADB
from . import Check
import logging
import os
import numpy as np
from pydub import AudioSegment
from pydub.silence import split_on_silence
import pathlib
import wave
import subprocess
import inspect
import pyaudio
from scipy.io import wavfile
import matplotlib.pyplot as plt

TV_Platform = 0  # 0:stb,1:tv
CHUNK = 2048
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 48000  # 44100, 16000, 18000, 48000
RECORD_SECONDS = 5
VIDEO_AUDIO_FILENAME = "video_audio.wav"
RECORD_AUDIO_FILENAME = "record_audio.wav"
RECORD_AUDIO_SPECTRUM = "spectrum_plot.png"
# index=6 #input_device_index = 2


class AudioCheck(ADB, Check):
    '''
    Singleton class,should not be inherited

    Attributes:
        TINY_MIX_COMMAND : tinymix command
        VOLUME_COMMAND : media volume command

    '''

    _INSTANCE_LOCK = threading.Lock()

    TINY_MIX_COMMAND = 'tinymix'
    VOLUME_COMMAND = 'media volume --stream 3 --get'

    def __init__(self):
        ADB.__init__(self, 'Player', unlock_code="", stayFocus=True)
        Check.__init__(self)

    def __new__(cls, *args, **kwargs):
        if not hasattr(AudioCheck, "_instance"):
            with AudioCheck._INSTANCE_LOCK:
                if not hasattr(AudioCheck, "_insatnce"):
                    AudioCheck._instance = object.__new__(cls)
        return AudioCheck._instance

    def get_audio_type(self):
        '''
        Retrieve the audio type using the tinymix command.
        Returns:
            audio_type (str): The audio type.
        '''
        audio_info = self.checkoutput(self.TINY_MIX_COMMAND)
        audio_type = re.findall(r'HDMIIN Audio Type\s+(\w+)', audio_info, re.S)[0]
        logging.debug(audio_type)
        return audio_type

    def get_volume(self):
        '''
        Retrieve the software volume value using the media volume command.
        Returns:
            volume (int): The volume value.
        '''
        volume_info = self.checkoutput(self.VOLUME_COMMAND)
        volume = re.findall(r'volume is (\d+) in range', volume_info, re.S)[0]
        logging.debug(volume)
        return int(volume)

    def get_device_info(self):
        '''
        Retrieve information about the input audio devices.
        Returns:
            index (int): Index of the selected audio input device.
        '''
        global index
        p = pyaudio.PyAudio()
        print("Number of input devices:", p.get_device_count())
        print("------- Input Devices -------")
        for i in range(p.get_device_count()):
            dev_info = p.get_device_info_by_index(i)
            if 'HDU7H+Mic' in dev_info['name'] or 'USB Audio' in dev_info['name']:
                index = i
            if dev_info["maxInputChannels"] > 0:
                print("Index:", i)
                print("Name:", dev_info["name"])
                print("Input channels:", dev_info["maxInputChannels"])
                print("---------------------------")
        p.terminate()
        return index

    def record_audio(self, index):
        '''
        Record audio from the specified input audio device.
        Args:
            index (int): Index of the selected audio input device.
        '''
        p = pyaudio.PyAudio()
        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK,
                        input_device_index=index)
        print("Start recording")
        frames = []
        for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK)
            frames.append(data)
        print("Done recording")
        stream.stop_stream()
        stream.close()
        p.terminate()
        wf = wave.open(RECORD_AUDIO_FILENAME, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        frames.clear()
        del frames

    def check_mute(self, outputfile_str):
        '''
        Check if the audio in the specified file is muted.
        Args:
            outputfile_str (str): Path to the audio file.
        Returns:
            is_muted (bool): True if audio is muted, False otherwise.
        '''
        path = pathlib.Path(outputfile_str)
        if path.exists():
            ext = os.path.splitext(outputfile_str)
            if ext[1] == '.raw':
                if 0 == TV_Platform:
                    voice_data = AudioSegment.from_file(file=outputfile_str, format="pcm", sample_width=2,
                                                        frame_rate=48000, channels=2)
                else:
                    voice_data = AudioSegment.from_file(file=outputfile_str, format="pcm", sample_width=4,
                                                        frame_rate=48000, channels=8)
            else:
                voice_data = AudioSegment.from_wav(file=outputfile_str)
            print('volume dBFS/rms/seconds', voice_data.dBFS, voice_data.rms, voice_data.duration_seconds)
            if float(voice_data.dBFS) < -50.0:
                print("check_mute voice_data.dBFS < -50 : no sound return fail currunt line:",
                      inspect.currentframe().f_lineno)
                return False
            else:
                print("check_mute pass")
                return True
        else:
            print("no outputfile_str file return fail", outputfile_str, 'currunt line:',
                  inspect.currentframe().f_lineno)
            return False

    def plot_spectrum(self, audio_file, save_file=None, log_scale=False):
        '''
        Plot the magnitude spectrum of the audio file.
        Args:
            audio_file (str): Path to the audio file.
            save_file (str): Path to save the plot.
            log_scale (bool): Whether to use a logarithmic scale for the y-axis.
        '''
        sample_rate, audio_data = wavfile.read(audio_file)
        fft_data = np.fft.fft(audio_data)
        magnitude_spectrum = np.abs(fft_data)
        plt.figure(figsize=(10, 6))
        if log_scale:
            plt.semilogy(magnitude_spectrum)
        else:
            plt.plot(magnitude_spectrum)
        plt.title('Magnitude Spectrum')
        plt.xlabel('Frequency (Hz)')
        plt.ylabel('Magnitude')
        plt.grid(True)
        plt.show(block=False)
        plt.pause(5)
        if save_file:
            plt.savefig(save_file)
            print(f"Saved spectrum plot as '{save_file}'")

    def check_noise(self, audio_file, window_size=100, threshold_factor=0.1):
        '''
        Check for noise in the audio file.
        Args:
            audio_file (str): Path to the audio file.
            window_size (int): Size of the sliding window for dynamic thresholding.
            threshold_factor (float): Factor to adjust the dynamic threshold.
        Returns:
            has_noise (bool): True if noise is detected, False otherwise.
        '''
        sample_rate, audio_data = wavfile.read(audio_file)
        fft_data = np.fft.fft(audio_data)
        magnitude_spectrum = np.abs(fft_data)
        energy = np.sum(magnitude_spectrum)
        thresholds = self.dynamic_threshold(magnitude_spectrum, window_size, threshold_factor)
        max_magnitude = np.max(magnitude_spectrum)
        noise_mask = magnitude_spectrum < thresholds
        noise_spectrum = magnitude_spectrum[noise_mask]
        noise_energy = np.sum(noise_spectrum)
        noise_ratio = noise_energy / energy
        if noise_ratio > 0.1:
            print("Detected noise in the audio file.")
            return True
        else:
            print("No noise detected in the audio file.")
            return False

    def dynamic_threshold(self, signal, window_size, threshold_factor):
        '''
        Calculate the dynamic threshold for noise detection.
        Args:
            signal (np.array): Input audio signal.
            window_size (int): Size of the sliding window.
            threshold_factor (float): Factor to adjust the threshold sensitivity.
        Returns:
            dynamic_threshold (list): List of dynamic thresholds.
        '''
        dynamic_threshold = []
        for i in range(len(signal)):
            start = max(0, i - window_size)
            end = min(len(signal), i + window_size)
            window = signal[start:end]
            threshold = np.mean(window) * threshold_factor
            dynamic_threshold.append(threshold)
        return dynamic_threshold

    def check_audio_breaks(self, outputfile_str):
        '''
        Check for audio breaks in the specified audio file.
        Args:
            outputfile_str (str): Path to the audio file.
        Returns:
            has_breaks (bool): True if audio breaks are detected, False otherwise.
        '''
        ext = os.path.splitext(outputfile_str)
        if ext[1] == '.raw':
            if TV_Platform == 0:
                sound = AudioSegment.from_file(file=outputfile_str, format="pcm", sample_width=2, frame_rate=48000,
                                               channels=2)
            else:
                sound = AudioSegment.from_file(file=outputfile_str, format="pcm", sample_width=4, frame_rate=48000,
                                               channels=8)
        else:
            sound = AudioSegment.from_wav(file=outputfile_str)
        chunks = split_on_silence(sound,
                                  min_silence_len=1,
                                  silence_thresh=-60,
                                  keep_silence=0)
        total_sound = sound[:1]
        for i, chunk in enumerate(chunks):
            total_sound += chunk
        total_sound.export(outputfile_str, format="wav")
        print(outputfile_str + " extraction completed")
        if len(chunks) == 1:
            print("check_audio_breaks pass")
            return True
        else:
            print("check_audio_breaks ng: staccato return fail section:", len(chunks), 'current line:',
                  inspect.currentframe().f_lineno)
            return False

    def extract_audio(self, input_video, output_audio, sample_rate=44100, channels=2):
        '''
        Extract audio from the input video file.
        Args:
            input_video (str): Path to the input video file.
            output_audio (str): Path to save the extracted audio file.
            sample_rate (int): Sampling rate of the audio.
            channels (int): Number of audio channels.
        '''
        command = [
            "ffmpeg",
            "-i", input_video,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", str(sample_rate),
            "-ac", str(channels),
            output_audio
        ]
        try:
            subprocess.run(command, check=True)
            print("Audio extracted successfully!")
        except subprocess.CalledProcessError as e:
            print(f"Error extracting audio: {e}")


if __name__ == '__main__':
    audioCheck = AudioCheck()
    index = audioCheck.get_device_info()
    audioCheck.record_audio(index)
    audioCheck.check_mute(RECORD_AUDIO_FILENAME)
    audioCheck.plot_spectrum(RECORD_AUDIO_FILENAME, RECORD_AUDIO_SPECTRUM, log_scale=True)
    audioCheck.check_noise(RECORD_AUDIO_FILENAME)
    audioCheck.check_audio_breaks(RECORD_AUDIO_FILENAME)
    input_video = "BKK2019_4Services_NF_v7.ts"
    audioCheck.extract_audio(input_video, VIDEO_AUDIO_FILENAME)
