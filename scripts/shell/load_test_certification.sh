#!/bin/bash

# Defined Dir path
Start_Test_Time=`date '+%Y.%m.%d_%H.%M'`
Auto_Script="${WORKSPACE}/AutoTestRes/scripts/shell"
Auto_Bin="${WORKSPACE}/AutoTestRes/bin"
Auto_Image="${WORKSPACE}/AutoTestRes/image"
Download_Path="${WORKSPACE}/Temp_Image"
echo $TEST_NODE_PWD | sudo -S chmod +777 -R $Auto_Bin
if [ ! -d "result_comparison" ]; then
    cp -r "${Auto_Script}/result_comparison" ./
fi

# Defined DUT ADB SN INFO ARRAY
devices_json_new="$TEST_DEVICES_JSON"
devices_list=$(echo "$devices_json_new" | jq -r '. | to_entries | map("\(.key)=\(.value)") | join(" ")')
declare -A Devices_Array
for pair in $devices_list; do
  key=${pair%=*}
  value=${pair#*=}
  Devices_Array["$key"]=$value
done

##################################################################################
# Defined function.
##################################################################################
function func_rebootDutByRelayDelayTime() {
    sleep_time=$1
    PowerRelay_Serial_Port=$2
    ${Auto_Bin}/powerRelay $PowerRelay_Serial_Port 1 off
    sleep 3
    ${Auto_Bin}/powerRelay $PowerRelay_Serial_Port 1 on
    echo "Sleep $1 seconds to wait DUT Power off/on."
    sleep $sleep_time
}

function func_checkUpgradeDutStatus() {
    # Get update error info:
    update_image_log=$(cat ${Auto_Bin}/update/upgradeDutStatuslLog.txt)
    echo "DEBUG: Check upgrade status log start:"
    echo $update_image_log
    echo "DEBUG: Check upgrade status log end"
    if [[ ! $update_image_log =~ "Upgrade image successful" ]]; then
        ps -ef | grep reboot_logging | grep ${DUT_Serial_Port} | grep -v grep | awk '{print $2}' | xargs kill -9
        echo "=================PRE-TEST SERIAL LOG START================="
        cat $WORKSPACE/AutoTestRes/log/pretest.txt
        echo "=================PRE-TEST SERIAL LOG END================="
        rm -f ${Auto_Bin}/update/upgradeDutStatuslLog.txt
        return 1
    fi
    return 0
}

function func_checkAdbStatus() {
    adb_sn=$1
    i=1
    while [[ $i -lt 5 ]]
    do
        test_adb=`adb devices | grep $adb_sn`
        echo "Loop times: $i adb command result: $test_adb"
        if [[ $test_adb =~ "recovery" ]]; then
            echo "DUT is in recovery mode"
            return 1
        elif [[ $test_adb =~ "offline" ]]; then
            echo "DUT is offline"
            return 2
        elif [[ $test_adb =~ "no permissions" ]]; then
            echo "DUT is no permissions"
            echo $TEST_NODE_PWD | sudo -S adb kill-server
            sleep 5
            echo $TEST_NODE_PWD | sudo -S adb start-server
            sleep 10
            return 0
        elif [[ $test_adb =~ "device" ]]; then
            echo "DUT is in normal status."
            return 0
        fi
        sleep 2
        i=$[ $i + 1 ]
    done
    echo "Can not find adb devices, SN is: $adb_sn"
    return 9
}

function func_checkFastbootStatus() {
    adb_sn=$1
    i=1
    while [[ $i -lt 5 ]]
    do
    test_fastboot=`fastboot devices | grep $adb_sn`
    echo "Loop times: $i fastboot command result: $test_fastboot"
    if [[ $test_fastboot =~ "recovery" ]]; then
        echo "DUT is in recovery mode"
        return 1
    elif [[ $test_fastboot =~ "offline" ]]; then
        echo "DUT is offline"
        return 2
    elif [[ $test_fastboot =~ "no permissions" ]]; then
        echo "DUT is no permissions"
        echo $TEST_NODE_PWD | sudo -S adb kill-server
        sleep 5
        echo $TEST_NODE_PWD | sudo -S adb start-server
        sleep 10
        return 0
    elif [[ $test_fastboot =~ "fastboot" ]]; then
        echo "DUT is in fastboot status."
        return 0
    fi
    sleep 2
    i=$[ $i + 1 ]
    done
    echo "Can not find fastboot devices, SN is: $adb_sn"
    return 9
}

function func_downloadImgFile() {
    url=$1
    is_build_compress=$2
    if [[ $is_build_compress =~ 'yes' ]]; then
        echo -e " --- Download file: $url\nDownloading ..."
        wget -q -c $url -O ${Download_Path}/aml_upgrade_package_img.tar.bz2

        echo " --- untar aml_upgrade_package_img.tar.bz2 ..."
        tar -xjf ${Download_Path}/aml_upgrade_package_img.tar.bz2 -C ${Download_Path}

        if [ $? -ne 0 ]; then
            echo " --- untar aml_upgrade_package_img.tar.bz2 failure,exit!"
            sleep 120
            exit 1
        fi
    else
        echo -e " --- Download file: $url\nDownloading ..."
        wget -q -c $url -O ${Download_Path}/aml_upgrade_package.img
    fi
    cp ${Download_Path}/aml_upgrade_*.img ${Auto_Image}/aml_upgrade_package.img
}

function func_downloadFastboottgzFile() {
    url=$1
    echo -e " --- Download file: $url\nDownloading ..."
    wget -q -c $url -O ${Download_Path}/fastboot_package.tgz
    echo " --- Extract tgz file: fastboot_package.tgz ..."
    tar -zxvf ${Download_Path}/fastboot_package.tgz -C $Auto_Image
    if [[ $? -ne 0 ]]; then
        echo " --- Extract fastboot_package.tgz failure,exit!"
        sleep 120
        exit 1
    fi
}

function func_downloadFastbootFile() {
    url=$1
    echo -e " --- Download file: $url\nDownloading ..."
    wget -q -c $url -O ${Download_Path}/fastboot_package.zip
    echo " --- Unzip zip file: fastboot_package.zip ..."
    unzip ${Download_Path}/fastboot_package.zip -d $Auto_Image
    if [ $? -ne 0 ]; then
        echo " --- Unzip fastboot_package.zip failure,exit!"
        sleep 120
        exit 1
    fi
}

function func_killRebootLoggingThread() {
    DUT_Serial_Port=$1
    ps -ef | grep reboot_logging | grep ${DUT_Serial_Port} | grep -v grep | awk '{print $2}' | xargs kill -9
    #echo "Check reboot_logging after kill thread start"
    ps -ef | grep reboot_logging | grep -v grep # check reboot_logging thread kill or not
    #echo "Check reboot_logging after kill thread end"
}

function func_checkUrlStatus() {
    get_http_code=`curl -I -m 10 -o /dev/null -s -w %{http_code} $1`
    echo "$1 status is: $get_http_code"
    if [[ $get_http_code != "200" ]]; then
        return 1
    else
        return 0
    fi
}

function func_checkManualBuild() {
    func_checkUrlStatus $1;
    if [ $? -ne 0 ]; then
        echo " --- Manual Test image is not available, Error code: HTTP 404"
        return 1
    else
        return 0
    fi
}

function func_updateDutByFastboot() {
    adb_sn=$1
    if [[ $TEST_BOARD =~ "boreal" ]]; then
        cp "${Auto_Script}/flash-all.sh" "${Auto_Image}/boreal-flash-all.sh"
        bash "${Auto_Image}/boreal-flash-all.sh" $adb_sn > "${WORKSPACE}/${adb_sn}.txt"
        sleep 180
        func_checkAdbStatus $adb_sn
    fi
}

function func_updateDutByAdnlTool() {
    DUT_Serial_Port=$1
    PowerRelay_Serial_Port=$2
    adb_sn=$3
    echo "upgrade_image.sh:(1)${DUT_Serial_Port} (2)${PowerRelay_Serial_Port} (3)${Auto_Image}/aml_upgrade_package.img (4)true"
    flock -x ~/.autoTestflashImage.lock \
    -c "bash ${WORKSPACE}/upgrade_image.sh \
    ${DUT_Serial_Port} \
    ${PowerRelay_Serial_Port} \
    ${Auto_Image}/aml_upgrade_package.img \
    true" > "${WORKSPACE}/${adb_sn}.txt"
    func_checkUpgradeDutStatus;
    updateStatus=$?
    if [[ $updateStatus -ne 0 ]]; then
        echo "@@@@@@ Upgrade image fail, exit test! @@@@@@"
        sleep 120
        exit 1
    fi
    func_rebootDutByRelayDelayTime 180 $PowerRelay_Serial_Port;
    func_checkAdbStatus $adb_sn;
    dutStatus=$?
    if [[ $dutStatus -ne 0 ]]; then
        func_killRebootLoggingThread $DUT_Serial_Port;
        echo "====================  SERIAL PORT LOG START ========================"
        exit 1
    fi
}

function func_burnOemAndGsi() {
    device=$1
    if [[ $TEST_BOARD =~ "gtv" ]] && [[ ! $TEST_BOARD =~ "hybrid" ]]; then
        read -r oem_ms12 <<< "$(find . -maxdepth 1 -type f -name '*gtv_oem_ms12*.img' | head -1)"
    elif [[ $TEST_BOARD =~ "hybrid" ]]; then
        read -r oem_ms12 <<< "$(find . -maxdepth 1 -type f -name '*hybrid_oem_ms12*.img' | head -1)"
    fi
    read -r boot_debug <<< "$(find . -maxdepth 1 -type f -name '*boot-debug*.img' | head -1)"
    read -r system <<< "$(find . -maxdepth 1 -type f -name 'system.img' | head -1)"
    if [[ -z "$oem_ms12" ]]; then
        if [[ $TEST_TARGET == "vts" ]]; then
            echo "VTS test,go on!"
        else
            echo "oem_ms12.img not found,please copy it to workspace!"
            return 1
        fi
    fi
    if [[ $TEST_TARGET == "vts" ]]; then
        if [[ -z "$boot_debug" ]] || [[ -z "$system" ]]; then
            echo "boot-debug.img or system.img not found,please copy it to workspace!"
            return 1
        fi
    fi
    adb -s "$device" reboot bootloader
    fastboot -s "$device" wait-for-device
    fastboot -s "$device" flashing unlock_critical
    fastboot -s "$device" flashing unlock
    if [[ -n "$oem_ms12" ]]; then
        fastboot -s "$device" flash oem "$oem_ms12"
    fi
    if [[ $TEST_TARGET == "vts" ]]; then
        fastboot -s "$device" flash vendor_boot "$boot_debug"
        fastboot -s "$device" reboot fastboot
        fastboot -s "$device" delete-logical-partition product_a
        fastboot -s "$device" delete-logical-partition product_b
        fastboot -s "$device" delete-logical-partition product
        fastboot -s "$device" flash system "$system"
        fastboot -s "$device" reboot bootloader
        fastboot -s "$device" -w
        fastboot -s "$device" reboot
    else
        fastboot -s "$device" flashing lock
        fastboot -s "$device" reboot
    fi
    sleep 180
    return 0
}

# Check flash image lock file exist or not
[[ ! -e ~/.autoTestflashImage.lock ]] && touch ~/.autoTestflashImage.lock
echo "Manual_TEST_IMAGE_URL:$TEST_IMAGE_URL"

#Create or delete img temp files
if [[ ! -d ${Download_Path} ]]; then
    mkdir -p ${Download_Path}
else
    rm -rf ${Download_Path}/*
fi
if [[ ! -d ${Auto_Image} ]]; then
    mkdir -p ${Auto_Image}
else
    rm -rf ${Auto_Image}/*
fi

#If user version,exit test,Except certification test!
#if [ $TEST_BUILD_VARIANT = "user" ]; then
#    if [[ ! $TEST_TARGET =~ (_CTS|_TVTS|_VTS|_GTS|_NTS) ]]; then
#        echo "android build is user version! Automation not support user version to test, exit!"
#        exit 1
#    fi
#fi

#Power on/off device
if [[ ! $TEST_BOARD =~ "boreal" ]]; then
    for device in "${!Devices_Array[@]}"; do
        dev_info="${Devices_Array[$device]}"
        IFS="," read serial_path powerRelay_path <<< "$dev_info"
        echo "device:${device}  serial_path:${serial_path}  powerRelay_path:${powerRelay_path}"
        func_rebootDutByRelayDelayTime 90 $powerRelay_path &
    done
    wait
fi
##################################################################################
#download firmware.
##################################################################################
echo " --- Start to download firmware"
if [[ $TEST_SERIES =~ "Android" ]]; then
        echo " --- --- if TEST_SERIES is Android, $TEST_IMAGE_URL"
    if [[ ${TEST_IMAGE_URL} =~ 'http://' ]]; then  # if 'http://' is exist in TEST_IMAGE_URL, then run
        func_checkManualBuild ${TEST_IMAGE_URL}
        file_server=$TEST_IMAGE_URL
        echo " --- --- Android TEST_IMAGE_URL: $file_server:"
        if [[ $file_server =~ '.bz2' ]]; then
            build_info=$(echo $file_server | awk -F '/' '{ i=1; while(i<=NF) {if( $i ~ /[A-Za-z].+-.+-.+-.+-.+-/) print $i; i++} }')
            echo "bz2 Build information: $build_info"
            image_URL=$file_server
            is_build_compress='yes'
            func_downloadImgFile $file_server $is_build_compress
            echo " --- --- func_downloadImgFile: done"
        elif [[ $file_server =~ '.img' ]]; then
            echo "img Build information: $file_server"
            image_URL=$file_server
            is_build_compress='no'
            func_downloadImgFile $file_server $is_build_compress
            echo " --- --- func_downloadImgFile: done"
        elif [[ $file_server =~ '.zip' ]]; then
            build_info=$(echo $file_server | awk -F '/' '{ i=1; while(i<=NF) {if( $i ~ /[A-Za-z].+-.+-.+-.+-.+-/) print $i; i++} }')
            echo " Zip Build information: $build_info"
            image_URL=$file_server
            func_downloadFastbootFile $file_server
            echo " --- --- func_downloadFastbootFile: done"
        elif [[ $file_server =~ '.tgz' ]]; then
            build_info=$(echo $file_server | awk -F '/' '{ i=1; while(i<=NF) {if( $i ~ /[A-Za-z].+-.+-.+-.+-.+-/) print $i; i++} }')
            echo " tgz Build information: $build_info"
            image_URL=$file_server
            func_downloadFastboottgzFile $file_server
            echo " --- --- func_downloadFastboot tgz File: done"
        else
            if [[ $TEST_SERIES =~ "Android_U" || $TEST_SERIES =~ "Android_S" || $TEST_SERIES =~ "Android_R" ]]; then
                echo " --- --- Android_S / Android_U Build information:"
                build_info=$(echo $file_server | awk -F '/' '{ i=1; while(i<=NF) {if( $i ~ /[A-Za-z].+-.+-.+-.+-.+-/) print $i; i++} }')
                date_str=$(echo $file_server | awk -F '/' '{ i=1; while(i<=NF) {if( $i ~ /^[0-9]+-/) print $i; i++} }')
                mdate1=$(echo $date_str | tr -cd "[0-9]")
                if [[ $TEST_SERIES =~ "Android_U" ]]; then
                    url=${file_server}aml_upgrade_signed_img-${mdate1}-${TEST_BUILD_NUMBER}.tar.bz2
                else
                    url=${file_server}aml_upgrade_img-${mdate1}-${TEST_BUILD_NUMBER}.tar.bz2
                fi
                get_http_code=`curl -I -m 10 -o /dev/null -s -w %{http_code} $url`
                echo "$url status is: $get_http_code"
                if [ $get_http_code != "200" ]; then
                    echo "${TEST_SERIES} Test image is not available, Error code: HTTP 404,exit test!"
                    exit 1
                else
                    image_URL=$url
                    is_build_compress='yes'
                    func_downloadImgFile $image_URL $is_build_compress
                fi
            fi
        fi
    fi
fi

##################################################################################
#Burn upgrade img.
##################################################################################
if [[ $TEST_SERIES =~ "Android_S" || $TEST_SERIES =~ "Android_U" || $TEST_SERIES =~ "Android_R" ]]; then
    echo " --- Start to upgrade firmware from $TEST_SERIES"
    if [ ! -f "upgrade_image.sh" ]; then
        wget -O upgrade_image.sh "http://10.18.11.98/Resource/Scripts/upgrade_image_temp.sh"
    fi
    cd ${Auto_Image}
    if [ ! -L flashImageTool ]; then
        echo "ln -s ${Auto_Bin}/flashImageTool flashImageTool"
        ln -s ${Auto_Bin}/flashImageTool flashImageTool
    fi
    if [ ! -L tc_flash-all.sh ]; then
        echo "ln -s ${Auto_Script}/tc_flash-all.sh tc_flash-all.sh"
        ln -s ${Auto_Script}/tc_flash-all.sh tc_flash-all.sh
    fi
    if [[ $UPGRADE_MODE =~ "fastboot" ]];then
        for device_id in "${!Devices_Array[@]}"; do
            func_updateDutByFastboot $device_id &
        done
        wait
    elif [[ $UPGRADE_MODE =~ "adnl" ]];then
        for device_id in "${!Devices_Array[@]}"; do
            dev_info="${Devices_Array[$device_id]}"
            IFS="," read serial_path powerRelay_path <<< "$dev_info"
            func_updateDutByAdnlTool $serial_path $powerRelay_path $device_id &
        done
        wait
    else
        echo "Burning mode not currently supported,exit test!"
        exit 1
    fi
fi

##################################################################################
#Burn oem and gsi img,only certification test
##################################################################################
cd ${WORKSPACE}
if [[ $TEST_TARGET =~ (cts|vts|gts|sts) ]]; then
    echo "Start burn oem_ms12 | vendor_boot | system"
    for device_id in "${!Devices_Array[@]}"; do
        {
            func_burnOemAndGsi $device_id
            if [[ $TEST_TARGET == "vts" ]] || [[ $TEST_BUILD_VARIANT == "userdebug" ]]; then
                adb -s "$device_id" root
            fi
#            adb -s "$device_id" shell cmd wifi set-wifi-enabled enabled
#            if [[ ! $TEST_WIFI_SSID == "NULL" ]]; then
#                if [[ $TEST_BOARD =~ "boreal" ]]; then
#                    adb -s "$device_id" shell cmd wifi add-suggestion "$TEST_WIFI_SSID" wpa2 "$TEST_WIFI_PWD"
#                else
#                    adb -s "$device_id" shell cmd wifi connect-network "$TEST_WIFI_SSID" wpa2 "$TEST_WIFI_PWD"
#                fi
#            fi
#            adb -s "$device_id" shell "settings put global stay_on_while_plugged_in 1"
        } &
    done
    wait
fi

echo "############################################################################################"
echo "DUT update and burn OEM | vendor_boot has finished,Start Certification ${TEST_TARGET^^} Test"
echo "############################################################################################"
exit 0
