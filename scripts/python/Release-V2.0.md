# This framework names AutoTestRes and is for Android system testing. 

## Release version
v2.0  date: 20230920

## Optimized Features.
In this version, we have made several functionality optimizations to enhance the efficiency and user experience of our product. Here are some key optimized features:

### 1. aut.sh

- **Description:** The "aut.sh" script is used to install dependencies required for the environment, as well as the streaming environment, and more.

- **Impact:** The goal is to execute this script in order to have all the required dependencies and environment set up automatically.

### 2. Stream Provider (streaming media)

- **Description:** The "resManager.py" script is changed and get streams from ftp server.

- **Impact:** Unified the source of streaming.


### 3. DVB Stream Provider

- **Description:** The stream provider named Dt2115bRC.exe can be used for DVB-C/S/T.

- **Impact:** Compatible with DVB-C/S/T.

### 4. Optimized retry results

- **Description:** Added the ability to specify the number of retries when running tests using the command python3 localtest_runner.py --all --retest 2, where 2 indicates the number of retries.

- **Impact:** Improved result accuracy.

## New Features:
### 1. DVB-S/T

- **Environment setup:** Configure dvb stream provider: Dt2115bRc.exe.
  
- **Test contents:** Scan, playback.
  
- **1.3 checkpoint:** Same as above 1.2 section.

### 2. Certification

- **Environment setup:** Details refer XTS release note.
  
- **Test contents:** GTS/VTS/CTS/TVTS/STS.
  
### 3. KPI

- **Environment setup:** Same local network when testing streaming media. Details refer release note.
  
- **Test contents:** Streaming media (start (live,vod)/live switch/seek(vod)/speed(live) to start). 
  
- **1.3 checkpoint:** kpi result will save to db.

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
