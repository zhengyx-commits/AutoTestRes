#!/bin/bash
#set +x
workspace=$(pwd)
RES=$workspace/obe_txt
cd $workspace
ADB_SN=$1
adb devices
adb -s $ADB_SN root
adb -s $ADB_SN shell svc bluetooth disable
adb -s $ADB_SN shell 'echo 2 > /sys/class/remote/amremote/protocol'
adb -s $ADB_SN shell input keyevent 4
adb -s $ADB_SN shell input keyevent 4

adb -s $ADB_SN shell mkdir /data/temp
echo hello
WIFI_INTERFACE=0
PARTENER_INTERFACE=0
LUNCH_INTERFACE=0

for i in {0..20}
do
    echo "$i"
    adb -s $ADB_SN shell uiautomator dump /data/temp/1.xml  2>&1 | tee 1.log
    if [[ $(cat 1.log) =~ "ERROR: could not get idle state." ]];then
        adb -s $ADB_SN shell input keyevent 23
        adb -s $ADB_SN shell input keyevent 23
    fi
    #choose language
    if [[ $(adb -s $ADB_SN shell cat data/temp/1.xml) =~ "English (United States)" ]];then
        ${RES}/AndroidUI -action click -adb ${ADB_SN} -t "English (United States)"
        adb -s $ADB_SN shell input keyevent 23
    fi

    #use phone to set up android tv
    if [[ $(adb -s $ADB_SN shell cat data/temp/1.xml) =~ "Quickly set up your TV with your Android phone?" ]];then
        ${RES}/AndroidUI -action click -adb ${ADB_SN} -t "Skip"
    fi

    if [[ $(adb -s $ADB_SN shell cat data/temp/1.xml) =~ "Afghanistan" ]];then
        ${RES}/AndroidUI -action click -adb ${ADB_SN} -t "Afghanistan"
    fi

    if [[ $(adb -s $ADB_SN shell cat data/temp/1.xml) =~ "Set up basic TV" ]];then
        ${RES}/AndroidUI -action click -adb ${ADB_SN} -t "Set up basic TV"
        sleep 5
    fi

    #connect wifi
    #connect wifi
    if [[ $(adb -s $ADB_SN shell cat data/temp/1.xml) =~ "You're connected to" ]];then
        ${RES}/AndroidUI -action click -adb ${ADB_SN} -t "Continue"
   	sleep 20
	echo "Wifi set up success"	
    fi
    if [[ $(adb -s $ADB_SN shell cat data/temp/1.xml) =~ "Select your Wi-Fi network" ]];then
        adb -s $ADB_SN shell "input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20"
        adb -s $ADB_SN shell "input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20"
        adb -s $ADB_SN shell "input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20"
        adb -s $ADB_SN shell "input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20"
        adb -s $ADB_SN shell "input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20"
        adb -s $ADB_SN shell "input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20"
        adb -s $ADB_SN shell "input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20"
        adb -s $ADB_SN shell "input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20"
        adb -s $ADB_SN shell "input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20;input keyevent 20"
        ${RES}/AndroidUI -action click -adb ${ADB_SN} -t "Other network…"
        adb -s $ADB_SN shell "input text XTS_ASUS_5G;input keyevent 66"
        ${RES}/AndroidUI -action click -adb ${ADB_SN} -t "WPA/WPA2-Personal"
        adb -s $ADB_SN shell "input text XPxp5lxts;input keyevent 66"
        sleep 35
        if [[ $(adb -s $ADB_SN shell "wpa_cli status") =~ "ssid=XTS_ASUS_5G" ]];then
            echo "Wifi set up success"
        else
            echo "Wifi set up failed"
        fi
        adb -s $ADB_SN shell "input keyevent 66"
        sleep 30
        adb -s $ADB_SN shell "input keyevent 4"
    fi
    
    if [[ $(adb -s $ADB_SN shell cat data/temp/1.xml) =~ "Make the most of your TV" ]];then
        ${RES}/AndroidUI -action click -adb ${ADB_SN} -t "Sign In"
        sleep 30
        #adb -s $ADB_SN shell "input text 'netwang88@gmail.com';input keyevent 66"
        #adb -s $ADB_SN shell "input text 'yan.fang@amlogic.com';input keyevent 66"
        adb -s $ADB_SN shell "input text 'zhiheng.xie@amlogic.com';input keyevent 66"
        sleep 10
        #adb -s $ADB_SN shell "input text 'Amlqa?2022a';input keyevent 66"
        #adb -s $ADB_SN shell "input text 'Tomato3ama.';input keyevent 66"
        adb -s $ADB_SN shell input text 'xzhXZH123456'
        adb -s $ADB_SN shell input keyevent 66
        sleep 30
    fi
    if [[ $(adb -s $ADB_SN shell cat data/temp/1.xml) =~ "Sign in - Google Accounts" ]];then
        #adb -s $ADB_SN shell "input text 'netwang88@gmail.com';input keyevent 66"
        #adb -s $ADB_SN shell "input text 'yan.fang@amlogic.com';input keyevent 66"
        adb -s $ADB_SN shell "input text 'zhiheng.xie@amlogic.com';input keyevent 66"
        sleep 10
        #adb -s $ADB_SN shell "input text 'Amlqa?2022a';input keyevent 66"
        #adb -s $ADB_SN shell "input text 'Tomato3ama.';input keyevent 66"
        adb -s $ADB_SN shell input text 'xzhXZH123456'
        adb -s $ADB_SN shell input keyevent 66
        sleep 30
    fi
    if [[ $(adb -s $ADB_SN shell cat data/temp/1.xml) =~ "Terms of Service" ]];then
        ${RES}/AndroidUI -action click -adb ${ADB_SN} -t "Accept"
    fi
    if [[ $(adb -s $ADB_SN shell cat data/temp/1.xml) =~ "Stay in the know" ]];then
        ${RES}/AndroidUI -action click -adb ${ADB_SN} -t "No thanks"
    fi
    if [[ $(adb -s $ADB_SN shell cat data/temp/1.xml) =~ "Google Services" ]];then
        ${RES}/AndroidUI -action click -adb ${ADB_SN} -t "Accept"
        sleep 5
    fi
    if [[ $(adb -s $ADB_SN shell cat data/temp/1.xml) =~ "Get better voice control of your TV" ]];then
        ${RES}/AndroidUI -action click -adb ${ADB_SN} -t "Continue"
        sleep 5
    fi
    if [[ $(adb -s $ADB_SN shell cat data/temp/1.xml) =~ "Adding finishing touches" ]];then
        sleep 15
    fi
    if [[ $(adb -s $ADB_SN shell cat data/temp/1.xml) =~ "Google Assistant" ]];then
        ${RES}/AndroidUI -action click -adb ${ADB_SN} -t "Continue"
    fi
    if [[ $(adb -s $ADB_SN shell cat data/temp/1.xml) =~ "Search across all your TV apps" ]];then
        ${RES}/AndroidUI -action click -adb ${ADB_SN} -t "Allow"
        sleep 15
    fi
    if [[ $(adb -s $ADB_SN shell cat data/temp/1.xml) =~ "Get personal results" ]];then
        ${RES}/AndroidUI -action click -adb ${ADB_SN} -t "Turn on"
    fi
    if [[ $(adb -s $ADB_SN shell cat data/temp/1.xml) =~ "Get the most out of your Google Assistant" ]];then
        ${RES}/AndroidUI -action click -adb ${ADB_SN} -t "Yes"
    fi

    if [[ $(adb -s $ADB_SN shell cat data/temp/1.xml) =~ "Install additional apps" ]];then
        ${RES}/AndroidUI -action click -adb ${ADB_SN} -t "Continue"
    sleep 5
    fi
    if [[ $(adb -s $ADB_SN shell cat data/temp/1.xml) =~ "You're signed in with" ]];then
        ${RES}/AndroidUI -action click -adb ${ADB_SN} -t "Continue"
    fi
    
    if [[ $(adb -s $ADB_SN shell cat data/temp/1.xml) =~ "Get the full Assistant experience" ]];then
        ${RES}/AndroidUI -action click -adb ${ADB_SN} -t "Turn on"
    fi

    if [[ $(adb -s $ADB_SN shell cat data/temp/1.xml) =~ "Choose your subscriptions" ]];then
        ${RES}/AndroidUI -action click -adb ${ADB_SN} -t "Confirm"
        sleep 8
        while :
        do
            adb -s $ADB_SN shell uiautomator dump /data/temp/1.xml  2>&1 | tee 1.log
            if [[ $(adb -s $ADB_SN shell cat data/temp/1.xml) =~ "Installing your apps" ]];then
                sleep 5
             else
                break
            fi
        done
    fi
    if [[ $(adb -s $ADB_SN shell cat data/temp/1.xml) =~ "Your Google TV experience is ready" ]];then
        ${RES}/AndroidUI -action click -adb ${ADB_SN} -t "Start exploring"
        sleep 10
        if [[ $(adb shell dumpsys window | grep mCurrentFocus) =~ "com.google.android.apps.tv.launcherx/com.google.android.apps.tv.launcherx.home.HomeActivity" ]];then
            echo "Launch screen set up success"
            exit 0
        else
            echo "Launch screen set up success not"
        fi
    fi
    if [[ $(adb -s $ADB_SN shell cat data/temp/1.xml) =~ "Your ohm is powered by" ]];then
        adb -s $ADB_SN shell "input keyevent 22;input keyevent 22;input keyevent 22;input keyevent 22;input keyevent 22"
        sleep 10
        if [[ $(adb shell dumpsys window | grep mCurrentFocus) =~ "com.google.android.tvlauncher/com.google.android.tvlauncher.MainActivity" ]];then
            echo "Launch screen set up success"
            exit 0
        else
            echo "Launch screen set up success not"
        fi
    fi
    if [[ $(adb -s $ADB_SN shell cat data/temp/1.xml) =~ "Your franklin_hybrid is powered by" ]];then
        adb -s $ADB_SN shell "input keyevent 22;input keyevent 22;input keyevent 22;input keyevent 22;input keyevent 22"
        sleep 10
        if [[ $(adb shell dumpsys window | grep mCurrentFocus) =~ "com.google.android.tvlauncher/com.google.android.tvlauncher.MainActivity" ]];then
            echo "Launch screen set up success"
            exit 0
        else
            echo "Launch screen set up success not"
        fi
    fi
done
#set +x
