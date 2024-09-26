#!/bin/bash
BASIC=${1:-"google"}
RETRY=${2:-"first"}
LOOP=$3
workspace=$(pwd)
RES=$workspace/obe_txt
cd $workspace
COUNT=0
EXECUTE_OOBE_COUNT=0
while [ $COUNT -lt 10 ]; do
    echo "Pair bluetooth_remote for $COUNT times"
    python3 $RES/bluetooth_powerRelay.py
    sleep 10
    if [ "$RETRY" = "retry" ]; then
        devices=()
        file_path=$(find . -name "oobe_fail_devices.txt")
        while read -r line || [[ -n $line ]]; do
            devices+=("$line")
        done <"$file_path"
    else
        if [[ $workspace =~ "Hybrid_CTS_Autotest" ]]; then
	    if [[ -z "$LOOP" ]]; then
            	devices=("ohm0000000031" "ohm0000000035" "ohm0000000032" "ohm0000000033" "ohm0000000034" "ohm0000000036")
	    else
		devices=("ohm0000000036")
	    fi
        elif [[ $workspace =~ "Hybrid_GTS_Autotest" ]]; then
            devices=("gts00000644")
        elif [[ $workspace =~ "Hybrid_NTS_Autotest" ]]; then
            devices=("ap222s905y4hoc603")
	elif [[ $workspace =~ "Hybrid_VTS_Autotest" ]]; then
	    devices=("vts00000665")
        else
            devices=("oppen000643" "oppen000645" "oppen000655" "oppen000603")
        fi
    fi
    for device in "${devices[@]}"; do
        # adb -s $device root
        adb -s $device shell mkdir /sdcard/temp
        adb -s $device shell uiautomator dump /sdcard/temp/1.xml 2>&1 | tee 1.log
        xml_content=$(adb -s $device shell cat sdcard/temp/1.xml)
        if [[ $xml_content =~ "id/remote_pairing_video" ]]; then
            echo "$device is now in remote pairing mode, Continue to pair bluetooth_remote!"
        elif [[ $xml_content =~ "Home" ]] || [[ $xml_content =~ "Library" && $xml_content =~ "Apps" ]]; then
            echo "${device} is now in the home page. This may indicate a failed image upgrade or the OOBE process has passed."
	elif [[ $xml_content =~ "Restart" ]]; then
            echo "$device now in sleep mode, reboot it!"
            adb -s $device reboot
            sleep 60
        else
            echo "${device} Not in remote pairing, Start pass OOBE>>>>>>>>"
	    adb -s $device shell "input keyevent 4"
            if [ "$BASIC" = "basic" ]; then
                bash $RES/OOBE_FOR_USER.sh $device $BASIC >./obe_txt/"$device"_basic_oobe.log
                EXECUTE_OOBE_COUNT=$((EXECUTE_OOBE_COUNT + 1))
		break
            else
                bash $RES/OOBE_FOR_USER.sh $device >./obe_txt/"$device"_oobe.log
                EXECUTE_OOBE_COUNT=$((EXECUTE_OOBE_COUNT + 1))
		break
            fi
        fi
    done
    if [ $EXECUTE_OOBE_COUNT -eq ${#devices[@]} ]; then
        echo "All devices has executed OOBE"
        break
    else
        COUNT=$((COUNT + 1))
    fi
done
if [ $COUNT -ge 10 ]; then
    echo "Some devices failed to pair bluetooth_remote after 10 attempts, please check OOBE..."
    exit 1
else
    exit 0
fi
