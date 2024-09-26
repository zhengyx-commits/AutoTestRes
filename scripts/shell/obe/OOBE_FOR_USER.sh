#!/bin/bash
#set +x
if [ $# -lt 1 ]; then
    echo "Must pass the adb devices number and be the first parameter"
    exit 1
fi
workspace=$(pwd)
mkdir -p obe_txt
RES=$workspace/obe_txt
cd $workspace
ADB_SN=$1
BASIC=$2
# adb -s $ADB_SN shell 'echo 2 > /sys/class/remote/amremote/protocol'
adb -s $ADB_SN shell mkdir /sdcard/temp
adb -s $ADB_SN shell "input keyevent 4;input keyevent 4"

WIFI_INTERFACE=0
PARTENER_INTERFACE=0
LUNCH_INTERFACE=0

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

for i in {0..20}
do
    echo "${i}"
    adb -s $ADB_SN shell "uiautomator dump /sdcard/temp/window_dump.xml"  2>&1 | tee 1.log
    adb -s $ADB_SN pull /sdcard/temp/window_dump.xml $RES
    sleep 2
    if [[ $(cat 1.log) =~ "ERROR: could not get idle state." ]];then
        adb -s $ADB_SN shell "input keyevent 4"
        adb -s $ADB_SN shell "input keyevent 4"
    fi
    if [[ $(cat ${RES}/window_dump.xml) =~ "Before pairing your Bluetooth devices, make sure they're in pairing mode." ]];then
        echo "Exit pairing bluetooth remote"
        adb -s $ADB_SN shell "input keyevent 4;input keyevent 4;"
    fi
    if [[ $(cat ${RES}/window_dump.xml) =~ "English (United States)" ]];then
        echo "choose language"
        coordinates=$(get_button_coordinates "English (United States)")
        echo ">English (United States)< coordinates:${coordinates}"
        adb -s $ADB_SN shell "input tap ${coordinates}"
    fi
    if [[ $(cat ${RES}/window_dump.xml) =~ "Quickly set up your TV with your Android phone?" ]];then
        echo "use phone to set up android tv"
        coordinates=$(get_button_coordinates "Skip")
        echo ">Skip< coordinates:${coordinates}"
        adb -s $ADB_SN shell "input tap ${coordinates}"
    fi
    if [[ $(cat ${RES}/window_dump.xml) =~ "Afghanistan" ]];then
        echo "choose country"
        coordinates=$(get_button_coordinates "Afghanistan")
        echo ">Afghanistan< coordinates:${coordinates}"
        adb -s $ADB_SN shell "input tap ${coordinates}"
    fi
    if [[ $(cat ${RES}/window_dump.xml) =~ "Set up Google TV" ]];then
        if [ -n "$BASIC" ];then
            echo "Set up basic TV"
            coordinates=$(get_button_coordinates "Set up basic TV")
            echo ">Set up Google TV< coordinates:${coordinates}"
            adb -s $ADB_SN shell "input tap ${coordinates}"
            sleep 3
        else
            echo "Set up Google TV"
            coordinates=$(get_button_coordinates "Set up Google TV")
            echo ">Set up Google TV< coordinates:${coordinates}"
            adb -s $ADB_SN shell "input tap ${coordinates}"
            sleep 3
        fi
    fi
    if [[ $(cat ${RES}/window_dump.xml) =~ "You're connected to" ]];then
        echo "Has connected wifi,Continue"
        coordinates=$(get_button_coordinates "Continue")
        echo ">Continue< of You're connected to coordinates:${coordinates}"
        adb -s $ADB_SN shell "input tap ${coordinates}"
        sleep 20
    fi
    if [[ $(cat ${RES}/window_dump.xml) =~ "You're connected using Ethernet" ]];then
        echo "Has connected ethernet,Continue"
        coordinates=$(get_button_coordinates "Continue")
        echo ">Continue< of You're connected to coordinates:${coordinates}"
        adb -s $ADB_SN shell "input tap ${coordinates}"
        sleep 20
    fi
    if [[ $(cat ${RES}/window_dump.xml) =~ "Select your Wi-Fi network" ]];then
        echo "Choose a other wifi to connect"
        for j in {0..60}
        do
            adb -s $ADB_SN shell "input keyevent 20"
        done
        for j in {0..5}; do
            adb -s $ADB_SN shell "uiautomator dump /sdcard/temp/window_dump.xml"
            adb -s $ADB_SN pull /sdcard/temp/window_dump.xml $RES
            if [[ $(cat ${RES}/window_dump.xml) =~ "Other network" ]]; then
                coordinates=$(get_button_coordinates "Other network…")
                echo ">Other network…< coordinates:${coordinates}"
                adb -s $ADB_SN shell "input tap ${coordinates}"
                sleep 2
            fi
            if [[ $(cat ${RES}/window_dump.xml) =~ "Enter name of Wi-Fi" ]]; then
                adb -s $ADB_SN shell "input text openwrt_5g;input keyevent 66"
                sleep 10
            fi
            if [[ $(cat ${RES}/window_dump.xml) =~ "Type of security" ]]; then
                coordinates=$(get_button_coordinates "WPA/WPA2-Personal")
                echo ">WPA/WPA2-Personal< coordinates:${coordinates}"
                adb -s $ADB_SN shell "input tap ${coordinates}"
            fi
            if [[ $(cat ${RES}/window_dump.xml) =~ "Enter password for" ]]; then
                adb -s $ADB_SN shell "input text 1234567890;input keyevent 66"
                sleep 60
                if [[ $(adb -s $ADB_SN shell "cmd wifi status") =~ "Wifi is connected to \"openwrt_5g\"" ]]; then
                    echo "Wifi set up success"
                    break
                else
                    echo "Wifi set up failed"
                    adb -s $ADB_SN shell "cmd wifi connect-network openwrt_5g wpa2 1234567890"
                    adb -s $ADB_SN shell "input keyevent 4;input keyevent 4;"
                fi
            fi
        done
    fi
    if [[ $(cat ${RES}/window_dump.xml) =~ "Make the most of your TV" ]];then
        coordinates=$(get_button_coordinates "Sign In")
        echo ">Sign In< coordinates:${coordinates}"
        adb -s $ADB_SN shell "input tap ${coordinates}"
        sleep 10
        adb -s $ADB_SN shell "input text amltest9@amlogic.com;input keyevent 66"
        sleep 10
        adb -s $ADB_SN shell "input text Qatest123!"
        adb -s $ADB_SN shell "input keyevent 66"
        sleep 30
    fi
    if [[ $(cat ${RES}/window_dump.xml) =~ "Sign in - Google Accounts" ]];then
        adb -s $ADB_SN shell "input text amltest9@amlogic.com;input keyevent 66"
        sleep 10
        adb -s $ADB_SN shell "input text Qatest123!"
        adb -s $ADB_SN shell "input keyevent 66"
        sleep 30
    fi
    if [[ $(cat ${RES}/window_dump.xml) =~ "Terms of Service" ]];then
        if [[ $(cat ${RES}/window_dump.xml) =~ "text=\"View more\"" ]];then
            coordinates=$(get_button_coordinates "View more")
            echo "Terms of Service >View more< coordinates:${coordinates}"
            adb -s $ADB_SN shell "input tap ${coordinates}"
        else
            coordinates=$(get_button_coordinates "Accept")
            echo "Terms of Service >Accept< coordinates:${coordinates}"
            adb -s $ADB_SN shell "input tap ${coordinates}"
        fi
    fi
    if [[ $(cat ${RES}/window_dump.xml) =~ "Stay in the know" ]];then
        coordinates=$(get_button_coordinates "No thanks")
        echo "Stay in the know >No thanks< coordinates:${coordinates}"
        adb -s $ADB_SN shell "input tap ${coordinates}"
        sleep 5
    fi
    if [[ $(cat ${RES}/window_dump.xml) =~ "Did you know?" ]];then
        coordinates=$(get_button_coordinates "Got it")
        echo "Stay in the know >Got it< coordinates:${coordinates}"
        adb -s $ADB_SN shell "input tap ${coordinates}"
        sleep 5
    fi
    if [[ $(cat ${RES}/window_dump.xml) =~ "Google Services" ]];then
        coordinates=$(get_button_coordinates "Accept")
        echo "Google Services >Accept< coordinates:${coordinates}"
        adb -s $ADB_SN shell "input tap ${coordinates}"
        sleep 5
    fi
    if [[ $(cat ${RES}/window_dump.xml) =~ "Get better voice control of your TV" ]];then
        coordinates=$(get_button_coordinates "Continue")
        echo "Get better voice control of your TV >Continue< coordinates:${coordinates}"
        adb -s $ADB_SN shell "input tap ${coordinates}"
        sleep 5
    fi
    if [[ $(cat ${RES}/window_dump.xml) =~ "text=\"Google Assistant\"" ]];then
        coordinates=$(get_button_coordinates "Continue")
        echo "Google Assistant >Continue< coordinates:${coordinates}"
        adb -s $ADB_SN shell "input tap ${coordinates}"
        sleep 3
    fi
    if [[ $(cat ${RES}/window_dump.xml) =~ "Search across all your TV apps" ]];then
        coordinates=$(get_button_coordinates "Allow")
        echo "Search across all your TV apps >Allow< coordinates:${coordinates}"
        adb -s $ADB_SN shell "input tap ${coordinates}"
        sleep 5
    fi
    if [[ $(cat ${RES}/window_dump.xml) =~ "Activate Voice Match" ]];then
        coordinates=$(get_button_coordinates "I agree")
        echo "Activate Voice Match >I agree< coordinates:${coordinates}"
        adb -s $ADB_SN shell "input tap ${coordinates}"
        sleep 2
    fi
    if [[ $(cat ${RES}/window_dump.xml) =~ "Get personal results" ]];then
        coordinates=$(get_button_coordinates "Turn on")
        echo "Get personal results >Turn on< coordinates:${coordinates}"
        adb -s $ADB_SN shell "input tap ${coordinates}"
        sleep 2
    fi
    if [[ $(cat ${RES}/window_dump.xml) =~ "Get the most out of your Google Assistant" ]];then
        coordinates=$(get_button_coordinates "Yes")
        echo "Get the most out of your Google Assistant >Yes< coordinates:${coordinates}"
        adb -s $ADB_SN shell "input tap ${coordinates}"
        sleep 2
    fi
    if [[ $(cat ${RES}/window_dump.xml) =~ "Install additional apps" ]];then
        coordinates=$(get_button_coordinates "Continue")
        echo "Install additional apps >Continue< coordinates:${coordinates}"
        adb -s $ADB_SN shell "input tap ${coordinates}"
        sleep 2
    fi
    if [[ $(cat ${RES}/window_dump.xml) =~ "You're signed in with" ]];then
        coordinates=$(get_button_coordinates "Continue")
        echo "You're signed in with >Continue< coordinates:${coordinates}"
        adb -s $ADB_SN shell "input tap ${coordinates}"
        sleep 2
    fi
    if [[ $(cat ${RES}/window_dump.xml) =~ "Get the full Assistant experience" ]];then
        coordinates=$(get_button_coordinates "Turn on")
        echo "Get the full Assistant experience >Turn on< coordinates:${coordinates}"
        adb -s $ADB_SN shell "input tap ${coordinates}"
        sleep 2
    fi
    if [[ $(cat ${RES}/window_dump.xml) =~ "Choose your subscriptions" ]];then
        sleep 10
        coordinates=$(get_button_coordinates "Confirm")
        echo "Choose your subscriptions >Confirm< coordinates:${coordinates}"
        adb -s $ADB_SN shell "input tap ${coordinates}"
        sleep 30
        timeout=600
        counter=0
        while [ $counter -lt $timeout ]; do
            adb -s $ADB_SN shell uiautomator dump /sdcard/temp/1.xml
            if [[ $(adb -s $ADB_SN shell cat /sdcard/temp/1.xml) =~ "Your Google TV experience is ready" ]];then
                echo "Apps installation completed"
                sleep 5
                break
            fi
            echo "Installing apps, wait>>>>>>>>>>>"
            sleep 10
            counter=$((counter+10))
            echo "Has checked for ${counter} seconds"
        done
        #echo "Install app Check timeout"
    fi
    if [[ $(cat ${RES}/window_dump.xml) =~ "Your Google TV experience is ready" ]];then
        coordinates=$(get_button_coordinates "Start exploring")
        echo ">Start exploring< coordinates:${coordinates}"
        adb -s $ADB_SN shell "input tap ${coordinates}"
        sleep 10
        if [[ $(adb -s $ADB_SN shell dumpsys window | grep mCurrentFocus) =~ "com.google.android.apps.tv.launcherx/com.google.android.apps.tv.launcherx.home.HomeActivity" ]];then
            echo "Launch screen set up success"
            break
        else
            echo "Launch screen set up success not"
        fi
    fi
    if [[ $(cat ${RES}/window_dump.xml) =~ "Your ohm is powered by" ]];then
        adb -s $ADB_SN shell "input keyevent 22;input keyevent 22;input keyevent 22;input keyevent 22;input keyevent 22"
        sleep 10
        if [[ $(adb -s $ADB_SN shell dumpsys window | grep mCurrentFocus) =~ "com.google.android.tvlauncher/com.google.android.tvlauncher.MainActivity" ]];then
            echo "Launch screen set up success"
            break
        else
            echo "Launch screen set up success not"
        fi
    fi
    if [[ $(cat ${RES}/window_dump.xml) =~ "Your franklin_hybrid is powered by" ]];then
        adb -s $ADB_SN shell "input keyevent 22;input keyevent 22;input keyevent 22;input keyevent 22;input keyevent 22"
        sleep 10
        if [[ $(adb -s $ADB_SN shell dumpsys window | grep mCurrentFocus) =~ "com.google.android.tvlauncher/com.google.android.tvlauncher.MainActivity" ]];then
            echo "Launch screen set up success"
            break
        else
            echo "Launch screen set up success not"
        fi
    fi
done
#set +x
echo "Set up device Stay awake"
adb -s $ADB_SN shell "settings put global stay_on_while_plugged_in 1"
if [[ ${workspace} =~ "TVTS" ]] || [[ ${workspace} =~ "GTS" ]];then
    echo "TVTS and GTS Test :Open settings verify_adb_installs"
    adb -s $ADB_SN shell "settings put global verifier_verify_adb_installs 0"
fi
if [[ ${workspace} =~ "Hybrid_CTS_Autotest" ]]; then
    echo "CTS Test :Open location and close Verify apps over USB"
    adb -s $ADB_SN shell "settings put global verifier_verify_adb_installs 0"
    adb -s $ADB_SN shell "settings put secure location_mode 3"
    sleep 3
    adb -s $ADB_SN shell uiautomator dump /sdcard/temp/window_dump.xml
    adb -s $ADB_SN pull /sdcard/temp/window_dump.xml $RES
    if [[ $(cat ${RES}/window_dump.xml) =~ "Turn on location" ]];then
        # ${RES}/AndroidUI -action click -adb ${ADB_SN} -t "Agree"
        coordinates=$(get_button_coordinates "Agree")
        echo "coordinates:${coordinates}"
        adb -s $ADB_SN shell "input tap ${coordinates}"
    fi
    sleep 5
fi
if [[ ${workspace} =~ "NTS" ]]; then
    echo "NTS Test :Switch wifi to RAE"
    adb -s $ADB_SN shell "cmd wifi remove-suggestion openwrt_5g"
    adb -s $ADB_SN shell "cmd wifi forget-network 0"
    adb -s $ADB_SN shell "cmd wifi connect-network r3001802 wpa2 WIFIY26PBG"
    sleep 20
    if [[ $(adb -s $ADB_SN shell "wpa_cli status") =~ "ssid=r3001802" ]];then
        echo "Wifi switch success"
    else
        echo "Wifi switch failed,try again"
        adb -s $ADB_SN shell "cmd wifi connect-network r3001802 wpa2 WIFIY26PBG"
        sleep 10
    fi
fi
if [[ ${workspace} =~ "STS" ]] || [[ ${workspace} =~ "VTS" ]]; then
    echo "No need to forget bluetooth!"
else
    echo "Start to forgot paired Bluetooth remote control"
    for x in {0..3}
    do
        echo "$x"
        adb -s $ADB_SN shell "am start -n com.android.tv.settings/.MainSettings"
        sleep 3
        adb -s $ADB_SN shell "input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;"
        adb -s $ADB_SN shell "input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;"
        sleep 2
        adb -s $ADB_SN shell "input keyevent 19"
        sleep 2
        adb -s $ADB_SN shell "input keyevent 23"
        sleep 5
        adb -s $ADB_SN shell uiautomator dump /sdcard/temp/window_dump.xml
        if [[ $(adb -s $ADB_SN shell cat /sdcard/temp/window_dump.xml) =~ "B12" ]];then
            echo "This devices has paired B12 remote, Start forget it."
            adb -s $ADB_SN shell "input keyevent 20;input keyevent 20;input keyevent 20;"
            sleep 2
            adb -s $ADB_SN shell "input keyevent 23"
            sleep 2
            adb -s $ADB_SN shell "input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;"
            sleep 2
            adb -s $ADB_SN shell "input keyevent 23"
            sleep 2
            adb -s $ADB_SN shell "input keyevent 19;input keyevent 19;input keyevent 19;"
            sleep 2
            adb -s $ADB_SN shell "input keyevent 23"
            sleep 2
            adb -s $ADB_SN shell uiautomator dump /sdcard/temp/window_dump.xml
            if [[ $(adb -s $ADB_SN shell cat /sdcard/temp/window_dump.xml) =~ "Connected" ]];then
                echo "Forget Bluetooth remote Failed,retry"
                adb -s $ADB_SN shell "input keyevent 4"
                adb -s $ADB_SN shell "input keyevent 4"
            else
                echo "Forget Bluetooth remote successfully,return home"
                adb -s $ADB_SN shell "input keyevent 3"
                adb -s $ADB_SN shell "input keyevent 3"
                break
            fi
        else
            echo "This devices has not paired B12 remote, return home"
            adb -s $ADB_SN shell "input keyevent 4"
            adb -s $ADB_SN shell "input keyevent 4"
            break
        fi
    done
fi
exit 0
