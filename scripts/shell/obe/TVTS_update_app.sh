#!/bin/bash

workspace=$(pwd)
RES=$workspace/obe_txt
cd $workspace
ADB_SN=$1
adb -s $ADB_SN shell mkdir /sdcard/temp
timeout=1800
counter=0
#adb -s $ADB_SN root
echo "$ADB_SN Start update Google TV Movies & TV"
#apk_folder=/home/amlogic/TVTS_APK
#for apk_file in $(ls "$apk_folder"/*.apk | sort); do
#  echo "Installing $apk_file >>>>>>>>"
#  adb -s $ADB_SN install -r "$apk_file"
#done
#echo "All apk installed successfully"
#exit 0
function get_button_coordinates {
    if [[ -z $1 ]]; then
        echo "Error: Missing button text"
        return 1
    fi
    button_text="$1"
    button=$(xmllint --xpath "//node[@text='${button_text}']" ${RES}/window_dump.xml)
    if [[ -z $button ]]; then
        echo "Error: Button not found"
        return 1
    fi
    bounds=$(echo $button | grep -oE 'bounds="[^"]+"')
    if [[ -z $bounds ]]; then
        echo "Error: Bounds not found for button '$button_text'"
        return 1
    fi
    left=$(echo $bounds | grep -oE "[0-9]+" | sed -n '1p')
    top=$(echo $bounds | grep -oE "[0-9]+" | sed -n '2p')
    right=$(echo $bounds | grep -oE "[0-9]+" | sed -n '3p')
    bottom=$(echo $bounds | grep -oE "[0-9]+" | sed -n '4p')
    if [[ -z $left || -z $top || -z $right || -z $bottom ]]; then
        echo "Error: Failed to get all four coordinates for button '$button_text'"
        return 1
    fi
    x=$(( ($left + $right) / 2 ))
    y=$(( ($top + $bottom) / 2 ))
    echo "$x $y"
}
# open google play store
adb -s $ADB_SN shell "am start -n com.android.vending/com.google.android.finsky.tvmainactivity.TvMainActivity"
sleep 10
adb -s $ADB_SN shell "input keyevent 19"
sleep 3
adb -s $ADB_SN shell "input keyevent 21"
sleep 3
adb -s $ADB_SN shell "input keyevent 20"
sleep 3
adb -s $ADB_SN shell "input keyevent 22"
sleep 3
adb -s $ADB_SN shell "input text \"Google TV\";input keyevent 66"
adb -s $ADB_SN shell uiautomator dump /sdcard/temp/window_dump.xml
adb -s $ADB_SN pull /sdcard/temp/window_dump.xml $RES
if [[ $(cat ${RES}/window_dump.xml) =~ "Enable" ]];then
    echo "Google TV is disabled,enter \"Enable\" to enable it!"
    coordinates=$(get_button_coordinates "Enable")
    echo ">Enable< coordinates:${coordinates}"
    adb -s $ADB_SN shell "input tap ${coordinates}"
    sleep 20
fi
adb -s $ADB_SN shell "input keyevent 19;input keyevent 19;input keyevent 19;input keyevent 19"
sleep 2
adb -s $ADB_SN shell "input keyevent 22;input keyevent 22;input keyevent 22;input keyevent 22;input keyevent 23"
sleep 2
adb -s $ADB_SN shell "input keyevent 23"
sleep 2
adb -s $ADB_SN shell "input keyevent 23"
sleep 5
adb -s $ADB_SN shell uiautomator dump /sdcard/temp/window_dump.xml
if [[ $(adb -s $ADB_SN shell cat /sdcard/temp/window_dump.xml) =~ "Update all" ]];then
    adb -s $ADB_SN shell "input keyevent 23"
    while [ $counter -lt $timeout ]; do
        adb -s $ADB_SN shell uiautomator dump /sdcard/temp/window_dump.xml
        if [[ $(adb -s $ADB_SN shell cat /sdcard/temp/window_dump.xml) =~ "No updates available" ]];then
            echo "Update apps finished, return home"
            sleep 3
            adb -s $ADB_SN shell "input keyevent 4;input keyevent 4;input keyevent 4;input keyevent 4;input keyevent 4;input keyevent 3"
            break
        fi
        if [[ $(adb -s $ADB_SN shell cat /sdcard/temp/window_dump.xml) =~ "Update all" ]];then
            adb -s $ADB_SN shell "input keyevent 23"
        fi
        echo "Updating apps, wait>>>>>>>>>>>"
        sleep 20
        counter=$((counter+20))
        echo "Has checked for ${counter} seconds"
    done
    exit 0
else
    echo "May open update failed!"
    exit 1
fi
# open google TV movie
#adb -s $ADB_SN "am start -n com.google.android.videos/com.google.android.apps.play.movies.tv.usecase.home.TvHomeActivity"
#adb -s $ADB_SN shell "am start -n com.android.tv.settings/.device.apps.AppsActivity"


