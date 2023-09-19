#!/bin/bash
ADB_SN=$1
power_relay=$2
MAX_COUNT=3
COUNT=0
workspace=$(pwd)

while [ $COUNT -lt $MAX_COUNT ]; do
    ${workspace}/AutoTestRes/bin/powerRelay ${power_relay} all off
    sleep 10
    ${workspace}/AutoTestRes/bin/powerRelay ${power_relay} all on
    sleep 120
    adb -s $ADB_SN shell "am start -n com.android.tv.settings/.MainSettings"
    sleep 5
    for i in {0..15}
    do
        adb -s $ADB_SN shell "input keyevent 20"
    done
    adb -s $ADB_SN shell "input keyevent 19;input keyevent 19;input keyevent 23"
    sleep 2
    adb -s $ADB_SN shell "input keyevent 19;input keyevent 19;input keyevent 20;input keyevent 23"
    sleep 2
    adb -s $ADB_SN shell "input keyevent 19;input keyevent 20;input keyevent 20;input keyevent 23"
    sleep 2
    adb -s $ADB_SN shell "input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 23"
    sleep 2
    adb -s $ADB_SN shell "input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 23"
    sleep 300
    all_devices=$(adb devices)
    if [[ $all_devices =~ $ADB_SN ]]; then
        adb -s $ADB_SN shell mkdir /sdcard/temp
        adb -s $ADB_SN shell uiautomator dump /sdcard/temp/1.xml 2>&1 | tee 1.log
        xml_content=$(adb -s $ADB_SN shell cat sdcard/temp/1.xml)
        if [[ $xml_content =~ "id/remote_pairing_video" ]]; then
            echo "$ADB_SN is now in remote pairing mode, Factory reset successfully!"
            break
        else
            echo "$ADB_SN may factory reset failed , Try again!"
            # adb -s $ADB_SN shell "am force-stop com.android.tv.settings/.MainSettings"
            COUNT=$((COUNT+1))
        fi
    else
        echo "$ADB_SN may power on failed , Use powerRelay to start device"
        ${workspace}/AutoTestRes/bin/powerRelay ${power_relay} all off
        sleep 10
        ${workspace}/AutoTestRes/bin/powerRelay ${power_relay} all on
        sleep 300
        adb -s $ADB_SN shell mkdir /sdcard/temp
        adb -s $ADB_SN shell uiautomator dump /sdcard/temp/1.xml 2>&1 | tee 1.log
        xml_content=$(adb -s $ADB_SN shell cat sdcard/temp/1.xml)
        if [[ $xml_content =~ "id/remote_pairing_video" ]]; then
            echo "$ADB_SN is now in remote pairing mode, Factory reset successfully!"
            break
        else
            echo "$ADB_SN may factory reset failed , Try again!"
            # adb -s $ADB_SN shell "am force-stop com.android.tv.settings/.MainSettings"
            COUNT=$((COUNT+1))
        fi
    fi
done
if [ $COUNT -eq $((MAX_COUNT-1)) ]; then
    echo "Factory reset failed after 3 times. Please check!"
    exit 1
fi
exit 0
