#!/bin/bash
workspace=$(pwd)
RES=$workspace/obe_txt
file_path=$(find . -name "oobe_fail_devices.txt")
if [ -n "${file_path}" ]; then
    rm -f "${file_path}"
fi
OOBE_PASS_COUNT=0
if [[ $workspace =~ "Android_T_Hybrid_XTS_Autotest" ]]; then
    devices=("AMLS905Y4AP222248" "ap2228019621984101029" "ohm0000000032" "ohm0000000033" "ohm0000000034" "ohm0000000036")
elif [[ $workspace =~ "GTS_Autotest" ]]; then
    devices=("gts00000644")
elif [[ $workspace =~ "STS_Autotest" ]]; then
    devices=("ap2225c9589716052b3b8")
else
    devices=("gts00000644" "vts00000665" "ap222d9721140512b18" "ap222s905y4hoc645" "oppen000655")
fi
for device in "${devices[@]}"
    do
        adb -s ${device} shell "input keyevent 3"
        sleep 3
        if [[ $(adb -s ${device} shell dumpsys activity activities < /dev/null)  =~ "com.google.android.apps.tv.launcherx/.home.HomeActivity" ]];then
            echo "${device} in google TV mode"
            OOBE_PASS_COUNT=$((OOBE_PASS_COUNT+1))
        elif [[ $(adb -s ${device} shell dumpsys activity activities < /dev/null)  =~ "com.google.android.apps.tv.launcherx/.home.VanillaModeHomeActivity" ]];then
            echo "${device} in basic TV mode"
            OOBE_PASS_COUNT=$((OOBE_PASS_COUNT+1))
        else
            echo "${device} may fail in passing OOBE"
            echo "${device}" >> $RES/oobe_fail_devices.txt
        fi
    done
if [[ $workspace =~ "Android_T_Hybrid_XTS_Autotest" ]]; then
    if [ $OOBE_PASS_COUNT -gt 4 ]; then
        echo "More than or equal 5 devices pass OOBE, Start CTS Test!"
        exit 0
    else
        echo "Less than 5 devices pass OOBE, Retry!"
        exit 1
    fi
fi
exit 0