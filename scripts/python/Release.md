# This framework names AutoTestRes and is for Android system testing. 

## Release version
v1.0

## Main support two products: ott_hybrid(IPTV/DVB-C) and wifi.
###1. IPTV:
#### 1.1 test contents
Stream provider protocol: http, hlsV3, rtp, rtsp, udp, dvb-c.  
Stream format: h264 1080p/4k, h265 1080p/4k/4kP60, mpeg2 1080p/1080i, also include PID changed stream.  
Basic test operations: start play, pause, resume, stop, seek, microspeed(0.5, 1.5), switch channel, switch window(multi way:2 and 4), offline and restore network, suspend.
#### 1.2 checkpoint
Support check stuttering, avsync, abnormal behavior(kernel panic, crash and so on).

###2. DVB-C
####2.1 environment setup
Configure dvb stream provider: Dt2115bRc.exe.
####2.2 test contents
Functions: decode, playback, pvr, stress, switch channel, switch aspect ratio, switch subtitle(teletext, scte27, cc, dvb text), switch audio track.
####2.3 checkpoint
Same as above 1.2 section.

###3. wifi
####3.1 environment setup
pc and router should in same network.  
only support ASUS RT-AX88U.
DUT should enable adb.
#### 3.2 test contents
Function: connect
Wi-Fi type:  
2G 11N/Legacy/40Mhz/20Mhz/1 channel/6 channel/11 channel/wpa2/wpa3/pmf/aes, special ssid, conceal ssid.
5G ax/legacy/80Mhz/40Mhz/20Mhz/161 channel/36 channel/ 52 channel/wpa2/wpa3/pmf/aes, special ssid, conceal ssid.

## How to use
###1. configure target.json
if you want to run ott hybrid cases, prj should replace ott_hybrid. 
like this {
    "target": {
        "prj": "ott_hybrid"
    }
}.
###2. configure device id in config.json
"ott_hybrid": {
            "device_id": "ohm8096a104c1010814",
            "ipaddr": "10.18.32.170",
            "serial_port": "/dev/ott_hybrid_ah212_connector",
            "baudrate": 921600,
            "build_version": "S"
        }  
###3. view test case
cd python  
python3 localtest_runner.py -l  
like:  
| 26 | AATS_OTT_FUNC_MULTI_HTTP_TS_H264_1080                                 | kejun.chen    | tests/OTT_Hybrid/MULTI/test_OTT_Sanity_Multi_HTTP_TS_H264_1080.py                               |
| 27 | AATS_OTT_FUNC_MULTI_HTTP_TS_H265_1080                                 | kejun.chen    | tests/OTT_Hybrid/MULTI/test_OTT_Sanity_Multi_HTTP_TS_H265_1080.py                               |
| 28 | AATS_OTT_FUNC_MULTI_HTTP_TS_MPEG2_1080                                | kejun.chen    | tests/OTT_Hybrid/MULTI/test_OTT_Sanity_Multi_HTTP_TS_MPEG2_1080.py                              |
| 29 | AATS_OTT_FUNC_MULTI_HTTP_TS_H264_4k                                   | kejun.chen    | tests/OTT_Hybrid/MULTI/test_OTT_Sanity_Multi_HTTP_TS_H264_4k.py                                 |

###4. run single test case
cd python  
python3 localtest_runner.py -m AATS_OTT_FUNC_MULTI_HTTP_TS_H264_1080

###5. run all test cases
cd python  
python3 localtest_runner.py --all

## License
Copyright 2021 Amlogic.com, Inc. or its affiliates. All rights reserved.   

AMLOGIC PROPRIETARY/CONFIDENTIAL.  

THESE MATERIALS ARE PROVIDED ON AN "AS IS" BASIS. AMLOGIC SPECIFICALLY
DISCLAIMS, WITH RESPECT TO THESE MATERIALS, ALL WARRANTIES, EXPRESS,
IMPLIED, OR STATUTORY, INCLUDING THE IMPLIED WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT.
