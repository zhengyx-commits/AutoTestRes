#!/bin/bash


function usage() {
  echo "Usage: $0 -b [Current Build number] \
  -e [build_root_path] \
  -d [ADB_SN] \
  -f [Project_series] \
  -g [Secure boot parames] \
  -h [DUT chipid] \
  -i [BUILD_INFO] \
  -j [Upgrade_IMG_tool] \
  -k [Rdk_TestPlan] \
  -l [Rdk_Device_Name] \
  -m [Manual_Test_Image_URL] \
  -n [Build_Number] \
  -o [DUT_Baudrate] \
  -p [Project] \
  -q [Test_job_url] \
  -r [PowerRelay_Serial_Port] \
  -s [DUT_Serial_Port] \
  -u [TestPlanName] \
  -v [userdebug|engine] \
  -w [Jenkins_Workspace] \
  -c [patch_test] \
  [-h help]"

  exit 1
}

if [ $# -lt 13 ]; then
  usage
fi


while getopts ":b:c:d:e:f:g:h:i:j:k:l:m:n:o:p:q:r:s:u:v:w:h" opt
do
    case $opt in
        b)
    echo "argument: $opt $OPTARG"
    BUILD_NUMBER=$OPTARG
    ;;
        c)
    echo "argument: $opt $OPTARG"
    PATCHSET_IDS=$OPTARG
    ;;
        d)
    echo "argument: $opt $OPTARG"
    DUT_ADB_SN=$OPTARG
    ;;
        e)
    echo "argument: $opt $OPTARG"
    BUILD_ROOT_PATH=$OPTARG
    ;;
        f)
    echo "argument: $opt $OPTARG"
    PROJECT_SERIES=$OPTARG
    ;;
        g)
    echo "argument: $opt $OPTARG"
    SECURE_BOOT_PARAMES=$OPTARG
    ;;
        h)
    echo "argument: $opt $OPTARG"
    CHIPID=$OPTARG
    ;;
        i)
    echo "argument: $opt $OPTARG"
    BUILD_INFO=$OPTARG
    ;;
        j)
    echo "argument: $opt $OPTARG"
    UPDATE_TOOL=$OPTARG
    ;;
        k)
    echo "argument: $opt $OPTARG"
    RDK_TESTPLAN=$OPTARG
    ;;
        l)
    echo "argument: $opt $OPTARG"
    RDK_DEVICE=$OPTARG
    ;;
        m)
    echo "argument: $opt $OPTARG"
    Test_Image_URL=$OPTARG
    ;;
        n)
    echo "argument: $opt $OPTARG"
    Test_BUILD_NUMBER=$OPTARG
    ;;
        o)
    echo "argument: $opt $OPTARG"
    DUT_SERIAL_PORT_BAUDRATE=$OPTARG
    ;;
        p)
    echo "argument: $opt $OPTARG"
    TEST_BOARD_TYPE=$OPTARG
    ;;
        q)
    echo "argument: $opt $OPTARG"
    TEST_JOB_URL=$OPTARG
    ;;
        r)
    echo "argument: $opt $OPTARG"
    PowerRelay_Serial_Port=$OPTARG
    ;;
        s)
    echo "argument: $opt $OPTARG"
    DUT_Serial_Port=$OPTARG
    ;;
        u)
    echo "argument: $opt $OPTARG"
    TEST_PLAN_NAME=$OPTARG
    ;;
        v)
    echo "argument: $opt $OPTARG"
    TEST_VARIANT_TYPE=$OPTARG
    ;;
        w)
    echo "argument: $opt $OPTARG"
    WORKSPACE=$OPTARG
    ;;
        h)
    usage
    ;;
        \?)
    echo "invalid argument: $opt"
    usage
    ;;
    esac
done

HOSTNAME=$(hostname -I | awk '{print $1}')

if [[ $HOSTNAME == "192.168.1.100" ]]; then
    SERVER_IP="10.18.7.34"
elif [[ $HOSTNAME == "192.168.1.105" ]]; then
    SERVER_IP="10.18.7.30"
else
    SERVER_IP=$HOSTNAME
fi
echo "TEST_HOST_IP: $SERVER_IP"
echo "TEST_BOARD_TYPE:$TEST_BOARD_TYPE"
echo "TEST_VARIANT_TYPE:$TEST_VARIANT_TYPE"
echo "TEST_BUILD_NUMBER:$Test_BUILD_NUMBER"
echo "CHANGEID_PATCHSET: $PATCHSET_IDS"
echo "SECURE_BOOT_PARAMES: $SECURE_BOOT_PARAMES"
echo "BUILD_STATUS: $BUILD_STATUS"

# For AATS special arguments, need to configure it on the specific project
OTHER_ARGS=
LOGCAT_THREAD=

# For fail retest condition
FAIL_RETEST=

# Define hourly change ids
HOURLY_CHANGE_IDS=

# Default paramesters setting
TEST_TIMER=3600

# Check flash image lock file exist or not
if [ ! -e ~/.autoTestflashImage.lock ]; then
    touch ~/.autoTestflashImage.lock
fi

#============== shield by wxl 20210317 ===================================================
:<<!
# start reboot logging, and save the file to $WORKSPACE/AutoFramework/log/pretest.txt
if [ ! -d "$WORKSPACE/AutoTestRes/log/" ];then
    mkdir -p $WORKSPACE/AutoTestRes/log
else
    if [ -f "$WORKSPACE/AutoTestRes/log/pretest.txt" ];then
        rm $WORKSPACE/AutoTestRes/log/pretest.txt
    fi
fi
!
#========================================================================================

# Manual parse
echo "Manual_Test_Image_URL:$Test_Image_URL"

BUILD_JOB_URL=${TEST_JOB_URL}${BUILD_NUMBER}
echo "Current Test Job URL: ${BUILD_JOB_URL}"

#Get Console location
IP_STR=$(ifconfig | grep 10.18)
if [ -z "$IP_STR" ]; then
    where_is_console=shenzhen
    if [ ${TEST_BOARD_TYPE} == "p291_iptv" ]; then
        TEST_IMAGE_SITE="firmware-sz.amlogic.com/shenzhen/"
    else
    TEST_IMAGE_SITE="10.28.8.100/shenzhen"
    TEST_IMAGE_SITE_REVERSE=("10.18.11.97/shanghai" "10.18.11.6/shanghai" "10.88.11.22/xian")
    RECOVERY_IMAGE_SERVER_SZ="10.28.8.6/files/jenkins/RECOVERY_DUT_IMAGE"
    fi
else
    where_is_console=shanghai
    if [[ ${CHIPID} =~ "AH212" || ${CHIPID} =~ "bg201" ]]; then
        TEST_IMAGE_SITE="10.18.11.6/shanghai"
    else
    TEST_IMAGE_SITE="10.18.11.97/shanghai"
    TEST_IMAGE_SITE_REVERSE=("10.28.8.100/shenzhen" "10.88.11.22/xian")
    RECOVERY_IMAGE_SERVER_SH="10.18.11.31/files/RECOVERY_DUT_IMAGE"
    fi
fi

#============== shield by wxl 20210317 ===================================================
:<<!
#Get test type: Daily/PatchBuild/HourlyBuild
if [[ $TEST_PLAN_NAME =~ "HourlyBuild" ]]; then
    TASK_TYPE=HourlyBuild
    TEST_TIMER=300
elif [[ $TEST_PLAN_NAME =~ "PatchBuild" ]]; then
    TASK_TYPE=PatchBuild
elif [[ $TEST_PLAN_NAME =~ "DailyBuild_CI_YouTube" ]]; then
    TASK_TYPE=DailyBuild
    TEST_TIMER=7200
elif [[ $TEST_PLAN_NAME =~ "DailyBuild" ]]; then
    TASK_TYPE=DailyBuild
else
    TASK_TYPE=unknown
fi
!
#=====================================================================================

TASK_TYPE=unknown
echo "Task type is: $TASK_TYPE"

# check project need flash bootloader or not
skip_boot_project="t962e2_ab311 t962x3_ab301"

is_skip_boot_partition=no

for prj in $skip_boot_project
do
    if [ $prj = $TEST_BOARD_TYPE ]; then
        echo "INFO: This project will be flashing bootloader partition."
        is_skip_boot_partition=yes
    fi
done

# Defined DUT ADB SN INFO
ADB_SN=$DUT_ADB_SN
ADB_SN_OPTION="-s $DUT_ADB_SN"

FASTBOOT_SN=$DUT_ADB_SN
FASTBOOT_SN_OPTION="-s $DUT_ADB_SN"

# Auto check script path
AUTO_SCRIPT=$WORKSPACE/AutoTestRes/scripts/shell/
AUTO_REPORT=${WORKSPACE}/AutoTestRes/report
AUTO_BIN=${WORKSPACE}/AutoTestRes/bin
AUTO_LOG=${WORKSPACE}/AutoTestRes/log
AUTO_TMP=${WORKSPACE}/AutoTestRes/tmp
AUTO_IMAGE=$WORKSPACE/AutoTestRes/image
AUTO_OUTPUT=$WORKSPACE/AutoTestRes/output
AUTO_REPORT_TMP=$WORKSPACE/AutoTestRes/scripts/python/results
AUTO_RESULTS=$WORKSPACE/AutoTestRes/results
AUTO_DEVICECHK=$WORKSPACE/AutoTestRes/scripts/python/tools/device_check
AUTO_ALLURE=$WORKSPACE/AutoTestRes/scripts/python/allure_data

# project folder name
PRJ_FOLDER_NAME=$(sed -n "4p" ${AUTO_TMP}/test_job_info.txt)
OUTPUT_LOG_DIR=${AUTO_OUTPUT}/${PRJ_FOLDER_NAME}

# get patchset info
if [ "$PATCHSET_IDS" != "NULL" ]; then
    echo "It's patch test job"
    AUTO_REVIEW_INFO=/tmp/review.txt
    echo "" > $AUTO_REVIEW_INFO
else
    echo "It's not patch test job"
fi

DOWNLOAD_PATH=${WORKSPACE}/Temp_Image
if [ ! -d ${DOWNLOAD_PATH} ]; then
    mkdir -p ${DOWNLOAD_PATH}
else
    rm -rf ${DOWNLOAD_PATH}/*
fi

if [ ! -d ${AUTO_IMAGE} ]; then
    mkdir -p ${AUTO_IMAGE}
else
    rm -rf ${AUTO_IMAGE}/*
fi

#Check version type, if it is user version will not test
if [[ $TEST_PLAN_NAME =~ "HourlyBuild" ]];then
    echo "Automation open HourlyBuild user version test! 2020/12/28"
elif [[ $PROJECT_SERIES != "Android_K" && $TEST_VARIANT_TYPE = "user" ]]; then
    echo "android build is user version! Automation not support user version to test, exit!"

    if [ $PATCHSET_IDS != "NULL" ]; then
        echo '[INFO] android build is user version! Do not run test now' > $AUTO_REVIEW_INFO
        bash ${AUTO_SCRIPT}/add_comment4patchset.sh ${AUTO_BIN} ${AUTO_REVIEW_INFO} "${PATCHSET_IDS}"
    fi

    exit 0
fi

# Check CHIP ID
if [[ $CHIPID =~ "0x" ]]; then
    CHIPID=$(echo $CHIPID | awk '{print substr($1,3)}')
else
    CHIPID=CHIP_ID_IS_NULL
fi

## Define RECOVERY IMAGE PARAMES
read chip_soc prj_platform ota_key_type < <(echo $SECURE_BOOT_PARAMES | awk -F+ '{print $1,$2,$3}')


#============== shield by wxl 20210317 ===================================================
:<<!
secure_tool_path=${AUTO_BIN}/secureboot/toolV3
secure_key_path=${AUTO_BIN}/secureboot/keys
!
#=========================================================================================

# Date define
TODAY_MDATE=`date "+%Y-%m-%d"`
TODAY_MDATE1=`date "+%Y%m%d"`

YESTERDAY_MDATE=`date "+%Y-%m-%d" -d "-22hour"`
YESTERDAY_MDATE1=`date "+%Y%m%d" -d "-22hour"`

function func_rebootDutByRelayDelayTime() {
    if [[ $PROJECT_SERIES =~ "Boreal" ]]; then
        echo "Boreal no need to use the powerRelay!"
    else
        ${AUTO_BIN}/powerRelay $PowerRelay_Serial_Port all off
        sleep 3
        ${AUTO_BIN}/powerRelay $PowerRelay_Serial_Port all on
    fi
    echo "Flash image done, sleep $1 seconds to wait DUT boot complete."
    sleep $1
}


function func_checkUpgradeDutStatus() {
    # Get update error info:
    update_image_log=$(cat ${AUTO_BIN}/update/upgradeDutStatuslLog.txt)
    echo "DEBUG: Check upgrade status log start:"
    echo $update_image_log
    echo "DEBUG: Check upgrade status log end"
    if [[ ! $update_image_log =~ "Upgrade image successful" ]]; then
        ps -ef | grep reboot_logging | grep ${DUT_Serial_Port} | grep -v grep | awk '{print $2}' | xargs kill -9
        echo "=================PRE-TEST SERIAL LOG START================="
        cat $WORKSPACE/AutoTestRes/log/pretest.txt
        echo "=================PRE-TEST SERIAL LOG END================="
        rm -f ${AUTO_BIN}/update/upgradeDutStatuslLog.txt
        return 1
    fi
    return 0
}

function func_recoveryDUT(){
    # kill reboot logging process as setDutInUpdateMode needs to occupy the serial port
    func_killRebootLoggingThread;

    if [ ! -e "${DOWNLOAD_PATH}/${TEST_BOARD_TYPE}.img" ]; then
        echo "download file"
        if [[ $where_is_console =~ "shanghai" ]]; then
            RECOVERY_IMAGE_SERVER=$RECOVERY_IMAGE_SERVER_SH
        else
            RECOVERY_IMAGE_SERVER=$RECOVERY_IMAGE_SERVER_SZ
        fi

        echo "wget -c http://${RECOVERY_IMAGE_SERVER}/rescure_${PROJECT_SERIES}_${TEST_BOARD_TYPE}.img \
        -O ${DOWNLOAD_PATH}/rescure_${PROJECT_SERIES}_${TEST_BOARD_TYPE}.img"
        wget -q -c http://${RECOVERY_IMAGE_SERVER}/rescure_${PROJECT_SERIES}_${TEST_BOARD_TYPE}.img \
        -O ${DOWNLOAD_PATH}/rescure_${PROJECT_SERIES}_${TEST_BOARD_TYPE}.img
    fi

#============== shield by wxl 20210317 ===================================================
:<<!
        if [[ $SECURE_BOOT_PARAMES =~ "key" ]]; then
        echo "Encryption rescure_${PROJECT_SERIES}_${TEST_BOARD_TYPE}.img for securebootV3"

        bash $secure_tool_path/amlogic_secureboot_sign_whole_pkg.bash \
            --soc $chip_soc \
            --aml_key ${secure_key_path}/${chip_soc}_${prj_platform}_v1/aml-key/ \
            --avb_pem_key ${secure_key_path}/testkey_rsa2048.pem \
            --aml_img ${DOWNLOAD_PATH}/rescure_${PROJECT_SERIES}_${TEST_BOARD_TYPE}.img \
            --output ${AUTO_IMAGE}/aml_upgrade_package.img
    else
        # for none encryption image
        cp ${DOWNLOAD_PATH}/rescure_${PROJECT_SERIES}_${TEST_BOARD_TYPE}.img ${AUTO_IMAGE}/aml_upgrade_package.img
    fi
!
   cp ${DOWNLOAD_PATH}/rescure_${PROJECT_SERIES}_${TEST_BOARD_TYPE}.img ${AUTO_IMAGE}/aml_upgrade_package.img
#=========================================================================================

    if [ $is_skip_boot_partition = "yes" ]; then
        flock -x ~/.autoTestflashImage.lock \
        -c "bash ${WORKSPACE}/AutoTestRes/scripts/shell/upgrade_image.sh \
        $WORKSPACE \
        ${DUT_Serial_Port}
        ${DUT_SERIAL_PORT_BAUDRATE} \
        ${PowerRelay_Serial_Port} \
        aml_upgrade_package.img \
        false \
        ${UPDATE_TOOL}"
    else
        flock -x ~/.autoTestflashImage.lock \
        -c "bash ${WORKSPACE}/AutoTestRes/scripts/shell/upgrade_image.sh \
        $WORKSPACE \
        ${DUT_Serial_Port} \
        ${DUT_SERIAL_PORT_BAUDRATE} \
        ${PowerRelay_Serial_Port} \
        aml_upgrade_package.img \
        true \
        ${UPDATE_TOOL}"
    fi

    func_checkUpgradeDutStatus;

    func_rebootDutByRelayDelayTime 3;

    return 0
}

function func_checkAdbStatus() {
    i=1
    while [ $i -lt 5 ]
    do
        test_adb=`adb devices | grep $ADB_SN`
        echo "Loop times: $i adb command result: $test_adb"
        if [[ $test_adb =~ "recovery" ]]; then
            echo "DUT is in recovery mode"
            return 1
        elif [[ $test_adb =~ "offline" ]]; then
            echo "DUT is offline"
            return 2
        elif [[ $test_adb =~ "no permissions" ]]; then
            echo "DUT is no permissions"
            echo Linux2017 |sudo -S adb kill-server
            sleep 5
            echo Linux2017 |sudo -S adb start-server
            sleep 10
            return 0
        elif [[ $test_adb =~ "device" ]]; then
            echo "DUT is in normal status."
            return 0
        fi
        sleep 2
        i=$[ $i + 1 ]
    done
    echo "Can not find adb devices, SN is: $ADB_SN"
    return 9
}

function func_checkFastbootStatus() {
        i=1
        while [ $i -lt 5 ]
        do
        test_fastboot=`fastboot devices | grep $ADB_SN`
        echo "Loop times: $i fastboot command result: $test_fastboot"
        if [[ $test_fastboot =~ "recovery" ]]; then
            echo "DUT is in recovery mode"
            return 1
        elif [[ $test_fastboot =~ "offline" ]]; then
            echo "DUT is offline"
            return 2
        elif [[ $test_fastboot =~ "no permissions" ]]; then
            echo "DUT is no permissions"
            echo Linux2017 |sudo -S adb kill-server
            sleep 5
            echo Linux2017 |sudo -S adb start-server
            sleep 10
            return 0
        elif [[ $test_fastboot =~ "fastboot" ]]; then
            echo "DUT is in fastboot status."
            return 0
        fi
        sleep 2
        i=$[ $i + 1 ]
        done
        echo "Can not find fastboot devices, SN is: $ADB_SN"
        return 9
}

function func_checkDutAndRecovery() {
    func_checkAdbStatus;
    adbDevicesStatus=$?
    echo "Adb devices status code is: $adbDevicesStatus"

    if [ $adbDevicesStatus != 0 ]; then
        echo "=========>Rescure DUT by update tool"
        func_recoveryDUT;
        echo "waitting for dut reboot... 210s"
        sleep 120

        # check DUT status after rescure by upate tool.
        func_checkAdbStatus;
        adbDevicesStatus=$?
        test_type=`echo ${TEST_PLAN_NAME} | awk -F "_" '{print $4}'`

        if [ $adbDevicesStatus != 0 ]; then
            echo "!!! @@@@@@ Rescure DUT by update tool failure! Please check manually @@@@@@@!!!"
            ${AUTO_BIN}/easymail -t "jianhua.huang@amlogic.com" -c "xiaoliang.wang@amlogic.com" -f "NoReplyCI" -s "Rescure DUT FAILURE on ${test_type}_${PROJECT_SERIES}_${TEST_BOARD_TYPE}_${BUILD_NUMBER}" -C "${PROJECT_SERIES}_${TEST_BOARD_TYPE}_${BUILD_NUMBER};${TEST_PLAN_NAME};${TEST_JOB_URL}"
            return 2
        else
            echo "Rescure DUT by update tool success!"
            ${AUTO_BIN}/easymail -t "jianhua.huang@amlogic.com" -c "xiaoliang.wang@amlogic.com" -f "NoReplyCI" -s "Rescure DUT SUCCESS on ${test_type}_${PROJECT_SERIES}_${TEST_BOARD_TYPE}_${BUILD_NUMBER}" -C "${PROJECT_SERIES}_${TEST_BOARD_TYPE}_${BUILD_NUMBER};${TEST_PLAN_NAME};${TEST_JOB_URL}"
            return 1
        fi

    else
        return 0
    fi

}

function func_checkLinuxBaseProAdb(){
    func_checkAdbStatus;
    adbDevicesStatus=$?
    echo "Adb devices status code is: $adbDevicesStatus"
    if [ $adbDevicesStatus != 0 ]; then
        echo "Upgrade DUT image fail!"
        return 1
    fi
}

function func_adbIfaceLostReboot() {
    func_checkAdbStatus;
    dutStatus=$?
    if [ $dutStatus != 0 ]; then
        func_rebootDutByRelayDelayTime 60;
    fi
    return 0
}

function func_checkWorldCupDeviceNoAvailable() {
    i=1
    while [ $i -lt 20 ]
    do
        check_worldCup_device=`$WORKSPACE/AutoTestRes/bin/update/update identify`
        if [[ $check_worldCup_device =~ "can not find device" ]]; then
            echo "There is not any world cup device available, flash image directly."
            return 0
        else
            echo "There is world cup device available, waitting for 30 seconds and try again."
            sleep 60
        fi
        i=$[ $i + 1 ]
    done
}

function func_checkWorldCupDevice() {
    i=1
    while [ $i -lt 3 ]
    do
        check_worldCup_device=`$WORKSPACE/AutoTestRes/bin/update/update identify`
        if [[ $check_worldCup_device =~ "can not find device" ]]; then
            echo "There is not any world cup device available, waitting for 30 seconds and try again."
            sleep 10
        else
            echo "There is world cup device available, flash directly."
            return 0
        fi
        i=$[ $i + 1 ]
    done
}

function func_updateReportFile() {
    # $1 replace html str
    html_str=$1
    input_str=$(echo $2 | sed -e 's/\//\\\//g')

    if [[ ${html_str} =~ "Image URL" ]]; then
        replace_str="s/Image URL:<\/strong> \[REPLACE_STR\]/Image URL:<\/strong> ${input_str}/g"
    elif [[ ${html_str} =~ "FailReason" ]]; then
        replace_str="s/Pre-Test Stage: Running...<\/font>/Pre-Test Stage: ${input_str}<\/font>/g"
    elif [[ ${html_str} =~ "JenkinsBuildRUL" ]]; then
        replace_str="s/href=\"\[REPLACE_STR\]\" target/href=\"${input_str}\" target/g"
    else
        replace_str="NA"
    fi

    if [ "${replace_str}" != "NA" ]; then
        #echo "Replace str: ${replace_str}"
        if [ ! -z $3]; then
            if [[ 'report.html' =~ '$3' ]]; then
                sed -i "${replace_str}" ${AUTO_REPORT}/report.html
            elif [[  'report_template_upgradefail.html' =~ '$3' ]]; then
                sed -i "${replace_str}" ${AUTO_TMP}/report_template_upgradefail.html
            else
                echo "****** ERROR ****** Report file name is NULL"
            fi
        else
            sed -i "${replace_str}" ${AUTO_REPORT}/report.html
            sed -i "${replace_str}" ${AUTO_TMP}/report_template_upgradefail.html
        fi
    fi
}

function func_downloadImgFile() {
    URL=$1
    IS_BUILD_COMPRESS=$2
    IMGE_URL=$URL

    func_updateReportFile "Image URL" $URL;
    if [[ $IS_BUILD_COMPRESS =~ 'yes' ]]; then
        echo -e " --- Download file: $URL\nDownloading ..."
        wget -q -c $URL -O ${DOWNLOAD_PATH}/aml_upgrade_package_img.tar.bz2

        echo " --- untar aml_upgrade_package_img.tar.bz2 ..."
        tar -xjf ${DOWNLOAD_PATH}/aml_upgrade_package_img.tar.bz2 -C ${DOWNLOAD_PATH}

        if [ $? -ne 0 ]; then
            echo " --- untar aml_upgrade_package_img.tar.bz2 failure,exit!"
            func_updateReportFile "FailReason" "Untar aml_upgrade_package_img.tar.bz2 failure";
            func_preTestFailSaveLogs;
            sleep 120
            exit 1
        fi
    elif [[ $IS_BUILD_COMPRESS == 'iptv_ok' ]]; then
        echo -e " --- Download file: $URL\nDownloading ..."
        wget -q -c $URL -O ${DOWNLOAD_PATH}/aml_p291_prue_for_s905l_upgrade_package.img.tgz 

        echo " --- untar aml_p291_upgrade_package.img.tgz  ..."
        tar -xzf ${DOWNLOAD_PATH}/aml_p291_prue_for_s905l_upgrade_package.img.tgz  -C ${DOWNLOAD_PATH}

        if [ $? -ne 0 ]; then
            echo " --- untar aml_p291_prue_for_s905l_upgrade_package.img.tgz failure,exit!"
            func_updateReportFile "FailReason" "aml_p291_prue_for_s905l_upgrade_package.img.tgz failure";
            func_preTestFailSaveLogs;
            sleep 120
            exit 1
        fi
    elif [[ $IS_BUILD_COMPRESS == 'R_iptv_ok' ]]; then
        echo -e " --- Download file: $URL\nDownloading ..."
        wget -q -c $URL -O ${DOWNLOAD_PATH}/aml_S928X_upgrade_package.img.tgz

        echo " --- untar aml_S928X_upgrade_package.img.tgz   ..."
        tar -xzf ${DOWNLOAD_PATH}/aml_S928X_upgrade_package.img.tgz    -C ${DOWNLOAD_PATH}

        if [ $? -ne 0 ]; then
            echo " --- untar aml_S928X_upgrade_package.img.tgz  failure,exit!"
            func_updateReportFile "FailReason" "aml_S928X_upgrade_package.img.tgz  failure";
            func_preTestFailSaveLogs;
            sleep 120
            exit 1
        fi
    else
        echo -e " --- Download file: $URL\nDownloading ..."
        wget -q -c $URL -O ${DOWNLOAD_PATH}/aml_upgrade_package.img
    fi

#============== shield by wxl 20210317 ===================================================
:<<!
        if [[ $SECURE_BOOT_PARAMES =~ "key" ]]; then
        # for encryption image
        echo "Encryption aml_upgrade_package.img for securebootV3"

        bash $secure_tool_path/amlogic_secureboot_sign_whole_pkg.bash \
            --soc $chip_soc \
            --aml_key ${secure_key_path}/${chip_soc}_${prj_platform}_v1/aml-key/ \
            --avb_pem_key ${secure_key_path}/testkey_rsa2048.pem \
            --aml_img ${DOWNLOAD_PATH}/aml_upgrade_package.img \
            --output ${AUTO_IMAGE}/aml_upgrade_package.img
    else
        # for none encryption image
        cp ${DOWNLOAD_PATH}/aml_upgrade_package.img ${AUTO_IMAGE}/aml_upgrade_package.img
    fi
!
#=========================================================================================
    if [ ${TEST_BOARD_TYPE} == "p291_iptv" ]; then
        cp ${DOWNLOAD_PATH}/aml_p291_prue_for_s905l_upgrade_package.img ${AUTO_IMAGE}/aml_p291_prue_for_s905l_upgrade_package.img
    elif [ ${TEST_BOARD_TYPE} == "s928x_iptv" ]; then
        cp ${DOWNLOAD_PATH}/aml_S928X_upgrade_package.img ${AUTO_IMAGE}/aml_upgrade_package.img
    else
        cp ${DOWNLOAD_PATH}/aml_upgrade_package.img ${AUTO_IMAGE}/aml_upgrade_package.img
    fi
}

function func_downloadFastboottgzFile() {
    URL=$1
    IMGE_URL=$URL

    func_updateReportFile "Image URL" $URL;

    echo -e " --- Download file: $URL\nDownloading ..."
    wget -q -c $URL -O ${DOWNLOAD_PATH}/fastboot_package.tgz
    echo " --- Extract tgz file: fastboot_package.tgz ..."
    tar -zxvf ${DOWNLOAD_PATH}/fastboot_package.tgz -C $AUTO_IMAGE
    if [ $? -ne 0 ]; then
        echo " --- Extract fastboot_package.tgz failure,exit!"
        func_updateReportFile "FailReason" "Extract fastboot_package.tgz failure";
        func_preTestFailSaveLogs;
        sleep 120
        exit 1
    fi
}

function func_downloadFastbootFile() {
    URL=$1
    IMGE_URL=$URL
    func_updateReportFile "Image URL" $URL;
    echo -e " --- Download file: $URL\nDownloading ..."
    wget -q -c $URL -O ${DOWNLOAD_PATH}/fastboot_package.zip
    echo " --- Unzip zip file: fastboot_package.zip ..."
    unzip ${DOWNLOAD_PATH}/fastboot_package.zip -d $AUTO_IMAGE
    if [ $? -ne 0 ]; then
        echo " --- Unzip fastboot_package.zip failure,exit!"
        func_updateReportFile "FailReason" "Unzip fastboot_package.zip failure";
        func_preTestFailSaveLogs;
        sleep 120
        exit 1
    fi
}
function func_downloadabiFile() {
    URL=$1
    IMGE_URL=$URL
    file=${IMGE_URL##*/}
    echo -e " --- Download file: $URL\nDownloading 64bit_abi_feature.log ..."
    wget -q -c $URL -O ${AUTO_TMP}/${file}
}

function func_downloadOtaFile() {
    echo "pass"
}

function func_updateDutByUpdateTool() {
    echo "pass"
}

function func_updateDutByFastbootTool() {
    echo "pass"
}

function func_updateDutByAdnlTool() {
    echo "pass"
}

function func_checkUrlStatus() {
    get_http_code=`curl -I -m 10 -o /dev/null -s -w %{http_code} $1`
    echo "$1 status is: $get_http_code"
    if [ $get_http_code != "200" ]; then
        return 1
    else
        return 0
    fi
}

function func_downloadTestImage() {
    flash_sw_file=$1
    FILESERVER=$2
    TODAY_MDATE=`date "+%Y%m%d"`
    YESTERDAY_MDATE=`date "+%Y%m%d" -d "-22hour"`

    if [[ $flash_sw_file =~ "fat" ]]; then
        URL=${FILESERVER}${TEST_BOARD_TYPE}-fastboot-flashall-${TODAY_MDATE}.zip
        func_checkUrlStatus $URL;
        ret=$?
        if [ $ret -ne 0 ]; then
            URL=${FILESERVER}${TEST_BOARD_TYPE}-fastboot-flashall-${YESTERDAY_MDATE}.zip
            func_checkUrlStatus $URL;
            ret=$?
            if [ $ret -ne 0 ]; then
                echo "fastboot Test image is not available, Error code: HTTP 404"
            fi
        fi
        func_downloadFastbootFile $URL;
    elif [[ $flash_sw_file =~ "abi" ]]; then
        URL=${FILESERVER}make_64bit_abi_feature.log
        func_checkUrlStatus $URL;
        ret=$?
        if [ $ret -ne 0 ]; then
            URL=${FILESERVER}make_64bit_abi_feature.log
            func_checkUrlStatus $URL;
            ret=$?
            if [ $ret -ne 0 ]; then
                echo " abi Test image is not available, Error code: HTTP 404"
            fi
        fi
        func_downloadabiFile $URL;
        URL=${FILESERVER}make_x86_64_abi_feature.log
        func_checkUrlStatus $URL;
        ret=$?
        if [ $ret -ne 0 ]; then
            URL=${FILESERVER}make_x86_64_abi_feature.log
            func_checkUrlStatus $URL;
            ret=$?
            if [ $ret -ne 0 ]; then
                echo " abi 2 Test image is not available, Error code: HTTP 404"
            fi
        fi
        func_downloadabiFile $URL;
    elif [[ $flash_sw_file =~ "img" ]]; then
        IS_BUILD_COMPRESS=no
        URL=${FILESERVER}aml_upgrade_package.img
        func_checkUrlStatus $URL;
        ret=$?
        if [ $ret -ne 0 ]; then
            IS_BUILD_COMPRESS=yes
            URL=${FILESERVER}aml_upgrade_img-${TODAY_MDATE}.tar.bz2
            func_checkUrlStatus $URL;
            ret=$?
            if [ $ret -ne 0 ]; then
                URL=${FILESERVER}aml_upgrade_img-${YESTERDAY_MDATE}.tar.bz2
                func_checkUrlStatus $URL;
                ret=$?
                if [ $ret -ne 0 ]; then
                    echo " img Test image is not available, Error code: HTTP 404"
                fi
            fi
        fi
        func_downloadImgFile $URL $IS_BUILD_COMPRESS;
    elif [[ $flash_sw_file =~ "aml_p291" ]]; then
        IS_BUILD_COMPRESS="iptv_ok"
        URL=${FILESERVER}aml_p291_prue_for_s905l_upgrade_package.img.tgz
        func_checkUrlStatus $URL;
        ret=$?
        if [ $ret -ne 0 ]; then
            echo " img Test image is not available, Error code: HTTP 404"
        fi
        func_downloadImgFile $URL $IS_BUILD_COMPRESS;
    elif [[ $flash_sw_file =~ "S928X" ]]; then
        IS_BUILD_COMPRESS="R_iptv_ok"
        URL=${FILESERVER}
        func_checkUrlStatus $URL;
        ret=$?
        if [ $ret -ne 0 ]; then
            echo " img Test image is not available, Error code: HTTP 404"
        fi
        func_downloadImgFile $URL $IS_BUILD_COMPRESS;
    elif [[ $flash_sw_file =~ "ota" ]]; then
        URL=${FILESERVER}${TEST_BOARD_TYPE}-ota-${TODAY_MDATE}.zip
        func_checkUrlStatus $URL;
        ret=$?
        if [ $ret -ne 0 ]; then
            URL=${FILESERVER}${TEST_BOARD_TYPE}-ota-${YESTERDAY_MDATE}.zip
            func_checkUrlStatus $URL;
            ret=$?
            if [ $ret -ne 0 ]; then
                echo " OTA Test image is not available, Error code: HTTP 404"
            fi
        fi
        func_downloadOtaFile $URL;
    fi

    IMGE_URL=$URL
    func_updateReportFile "Image URL" $URL;
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

function func_checkBuildURL() {
    IMAGE_SERVER_PATH=$1
    if [[ ${BUILD_ROOT_PATH} =~ "AH212_GTVS" ]]; then
        IMAGE_FAE_SERVER_PATH='Android_TV/Trunk'
#        echo "cc: ${BUILD_ROOT_PATH}"
    else
        IMAGE_FAE_SERVER_PATH=''
    fi
    FILESERVER=http://${TEST_IMAGE_SITE}/${IMAGE_SERVER_PATH}/${BUILD_INFO}/
    func_checkUrlStatus $FILESERVER;
    if [ $? -ne 0 ]; then

        FILESERVER=http://${TEST_IMAGE_SITE}/${IMAGE_SERVER_PATH}/${TODAY_MDATE}/${BUILD_INFO}/
        func_checkUrlStatus $FILESERVER;
        if [ $? -ne 0 ]; then
            FILESERVER=http://${TEST_IMAGE_SITE}/${IMAGE_SERVER_PATH}/${YESTERDAY_MDATE}/${BUILD_INFO}/
            func_checkUrlStatus $FILESERVER;
            if [ $? -ne 0 ]; then
                checkBuildFlag=1
                for TEMP_TEST_IMAGE_SITE_REVERSE in ${TEST_IMAGE_SITE_REVERSE[@]}
                do
                    FILESERVER=http://${TEMP_TEST_IMAGE_SITE_REVERSE}/${IMAGE_SERVER_PATH}/${BUILD_INFO}/
                    func_checkUrlStatus $FILESERVER;
                    if [ $? -ne 0 ]; then
                        FILESERVER=http://${TEMP_TEST_IMAGE_SITE_REVERSE}/${IMAGE_SERVER_PATH}/${IMAGE_FAE_SERVER_PATH}/${TODAY_MDATE}/${BUILD_INFO}/
                        func_checkUrlStatus $FILESERVER;
                        if [ $? -ne 0 ]; then
                            FILESERVER=http://${TEMP_TEST_IMAGE_SITE_REVERSE}/${IMAGE_SERVER_PATH}/${IMAGE_FAE_SERVER_PATH}/${YESTERDAY_MDATE}/${BUILD_INFO}/
                            func_checkUrlStatus $FILESERVER;
                            if [ $? -eq 0 ]; then
                                checkBuildFlag=0
                                break
                                #return 1
                            fi
                        else
                            checkBuildFlag=0
                            break
                        fi
                    else
                        checkBuildFlag=0
                        break
                    fi
                done
                return $checkBuildFlag
            fi
        fi
    fi
    return 0
}

function func_checkBuild(){
    URL_STATUS=1
    if [[ ${BUILD_ROOT_PATH} =~ ',' ]]; then
        IFS=","
        BUILD_ROOT_PATH_ARRAY=($BUILD_ROOT_PATH)
        for PATH_ITEM in ${BUILD_ROOT_PATH_ARRAY[@]}
        do
            echo "${PATH_ITEM}"
            func_checkBuildURL ${PATH_ITEM};
            if [ $? -eq 0 ]; then
                URL_STATUS=0
                break
            fi
        done
    else
        func_checkBuildURL ${BUILD_ROOT_PATH};
        if [ $? -eq 0 ]; then
            URL_STATUS=0
        fi
    fi

    if [ ${URL_STATUS} -eq 1 ]; then
        echo " PreTest Test image is not available, Error code: HTTP 404"
        func_updateReportFile "Image URL" $FILESERVER;
        func_updateReportFile "FailReason" "Test image is not available";
        func_preTestFailSaveLogs;
        sleep 120
        exit 1
    fi
}

function func_checkBuildVersion() {

    func_checkAdbStatus

    echo " --- --- Test_BUILD_NUMBER: $Test_BUILD_NUMBER"
    #GETPROP_BUILD_CMD = "getprop |grep ro.build.lab126.build]"
    AFTER_VERSION=`adb $ADB_SN_OPTION shell "getprop |grep ro.build.lab126.build]"`
    echo " --- --- AFTER_VERSION: $AFTER_VERSION"

    if [[ $AFTER_VERSION =~ ${Test_BUILD_NUMBER} ]]; then
       echo " --- --- --- Build is matched after upgrade: OK"
    else
       echo " --- --- --- Build is not matched after upgrade"
       break
    fi

    echo " --- func_checkBuildVersion:done"
}

function func_setDutIntoFastbootMode() {
    i=1
    while [ $i -lt 10 ]
    do
        fastboot_serial_check=`fastboot devices | grep $ADB_SN`
        echo "Loop times: $i fastboot devices command result: $fastboot_serial_check"
        if [[ $fastboot_serial_check =~ "fastboot" ]]; then
            echo "DUT is in fastboot mode."
            return 0
        else
            ((j=$i%3)) # retry by 3 times, reboot DUT and retry again.
            if [ $j -eq 0 ]; then
                echo "Retry $i times, reboot DUT and try again."
                echo "waitting for dut reboot...[1 minutes]"
                func_rebootDutByRelayDelayTime 60;
                adb $ADB_SN_OPTION reboot fastboot
            else
                echo "DUT is not in fastboot mode. Try again."
                adb $ADB_SN_OPTION reboot fastboot
            fi
        fi

        sleep 5
        i=$[ $i + 1 ]

        if [ $i -eq 8 ]; then
            return 9
        fi
    done
}

function func_startRebootLoggingThread() {
    : > ${AUTO_LOG}/pretest.txt # clear log  file
    ${AUTO_BIN}/reboot_logging -s ${DUT_Serial_Port} -b ${DUT_SERIAL_PORT_BAUDRATE} -t 900 &
}

function func_killRebootLoggingThread() {
    ps -ef | grep reboot_logging | grep ${DUT_Serial_Port} | grep -v grep | awk '{print $2}' | xargs kill -9
    #echo "Check reboot_logging after kill thread start"
    ps -ef | grep reboot_logging | grep -v grep # check reboot_logging thread kill or not
    #echo "Check reboot_logging after kill thread end"
}

function func_adbRemount() {
    echo "----------------------------------------------"
    adb -s $DUT_ADB_SN reboot bootloader || true
    sleep 10
    fastboot -s $DUT_ADB_SN flashing unlock_critical
    fastboot -s $DUT_ADB_SN flashing unlock
    echo "----------------------------------------------"
    echo " --- Fastboot unlock --- "
    echo " --- Now Reboot and disable AVB --- "
    echo "----------------------------------------------"
    fastboot -s $DUT_ADB_SN reboot
    echo " --- Waiting to Starting root and disable AVB "
    echo "----------------------------------------------"

    while true
    do
        adb -s $DUT_ADB_SN root >/dev/null 2>&1
        if [ $? = 0 ]
        then
            break
        else
            sleep 5
        fi

    done
    sleep 10

    adb -s $DUT_ADB_SN disable-verity
    echo " --- Finished and reboot. --- "
    adb -s $DUT_ADB_SN reboot
    echo " --- Waiting reboot and Starting remount --- "
    while true
    do
        adb -s $DUT_ADB_SN root >/dev/null 2>&1
        if [ $? = 0 ]
        then
            break
        else
            sleep 5
        fi

    done
    sleep 10
    adb -s $DUT_ADB_SN shell setenforce 0
    adb -s $DUT_ADB_SN remount

}

function func_preTestFailSaveLogs() {
    func_updateReportFile "JenkinsBuildRUL" "${BUILD_JOB_URL}/consoleText";
    logDirName=$(date +"%Y%m%d-%H%M%S")-${BUILD_INFO}
    LOG_DIR=${OUTPUT_LOG_DIR}/${logDirName}
    mkdir -p ${LOG_DIR}
    cp ${AUTO_TMP}/report_template_upgradefail.html ${AUTO_REPORT}/report.html
    cp -r ${AUTO_REPORT}/* ${LOG_DIR}/

    if [ $TASK_TYPE = "HourlyBuild" ]; then
        wget -c ${FILESERVER}project.xml -O ${LOG_DIR}/project.xml
        wget -c ${FILESERVER}changeid.txt -O ${LOG_DIR}/changeid.txt
        wget -c ${FILESERVER}repo_ajax.txt -O ${LOG_DIR}/repo_ajax.txt
        wget -c ${FILESERVER}cl_detail.html -O ${LOG_DIR}/cl_detail.html
        wget -c ${FILESERVER}unmergeable.txt -O ${LOG_DIR}/unmergeable.txt
        mv ${AUTO_TMP}/test_job_info.txt ${LOG_DIR}/test_job_info.txt
    fi
}

function func_saveResult() {
    echo " --- start to save result"

    if [ ! -d ${AUTO_RESULTS} ]; then
        mkdir -p ${AUTO_RESULTS}
    fi

    if [ -f ${AUTO_REPORT}/report.html ]; then
        rm ${AUTO_REPORT}/report.html
    fi

    if [ -f ${AUTO_REPORT}/result_summary.html ]; then
        rm ${AUTO_REPORT}/result_summary.html
    fi

    if [ -f ${AUTO_REPORT}/YUVCheckExcel.xlsx ]; then
        rm ${AUTO_REPORT}/YUVCheckExcel.xlsx
    fi

    cd ${AUTO_REPORT_TMP}
#    report_folder=`ls |grep -v YUVCheckExcel.xlsx`

    func_getStartTime;
    res=$(func_getStartTime)
    echo $res
    report_folder=`ls |grep $res`
    echo $report_folder

    #cp ${report_folder}/result_summary.html ${AUTO_REPORT}/report.html
    if [ -e "${report_folder}"/result_summary.html ]; then
        cp -f ${report_folder}/result_summary.html ${AUTO_REPORT}/
    else
        cp -f ${report_folder}/result_summary1.html ${AUTO_REPORT}/result_summary.html
    fi
    mv ${report_folder} ${AUTO_RESULTS}

    if [ -f ${AUTO_REPORT_TMP}/YUVCheckExcel.xlsx ]; then
        cp ${AUTO_REPORT_TMP}/YUVCheckExcel.xlsx ${AUTO_REPORT}/YUVCheckExcel.xlsx
    fi
    echo " --- end to save result"
}

function get_last_allure_report() {
    project=$1
    project_report_path="/home/amlogic/FAE/AutoTest/AllureReport/${project}"
    last_report=$(sshpass -p "Linux2023" ssh amlogic@10.18.11.98 "ls -lt ${project_report_path} | grep '^d' | head -n 1 | awk '{print \$9}'")
    if [ -n "$last_report" ]; then
        echo "Last report history found"
        sshpass -p "Linux2023" scp -r amlogic@10.18.11.98:${project_report_path}/${last_report}/report/history ${AUTO_ALLURE}
        scp_exit_code=$?
        if [[ $scp_exit_code -eq 0 ]]; then
            echo "Last report history datas successfully scp to new test datas"
        fi
    else
        echo "Last report history not found"
    fi
}

function func_environment_info() {
    ubuntu_version=$(lsb_release -r -s)
    python_version=$(python3 --version | cut -d " " -f 2)
    echo "Server=$SERVER_IP" > $AUTO_ALLURE/environment.properties
    echo "Ubuntu=$ubuntu_version" >> $AUTO_ALLURE/environment.properties
    echo "Python=$python_version" >> $AUTO_ALLURE/environment.properties
    echo "Build_Info=$BUILD_INFO" >> $AUTO_ALLURE/environment.properties
    echo "Test_Job_URL=$TEST_JOB_URL" >> $AUTO_ALLURE/environment.properties
}

function func_get_project_name() {
    local target="$1"
    local TEST_JOB_URL="$2"
    local project_name=""

    if [[ ${target} = "ott_hybrid_s_yuv" ]]; then
        project_name="Decoder Check(YUV)"
    elif [[ ${target} = "ott_hybrid" ]] && [[  "${TEST_JOB_URL}" =~ "Autotest_Basic" ]]; then
        project_name="IPTV Basic Play Control"
    elif [[ ${target} = "ott_hybrid_compatibility" ]]; then
        project_name="IPTV Compatibility"
    elif [[ "${TEST_JOB_URL}" =~ "Format_Compatibility" ]]; then
        project_name="Format Compatibility"
    elif [[ ${target} = "ott_sanity" ]] && [[ ! "${TEST_JOB_URL}" =~ "Android_U_Google_Boreal_Autotest_Sanity" ]]; then
        project_name="Sanity Test"
    elif [[ ${target} = "ott_hybrid_s_kpi" ]]; then
        project_name="KPI"
    elif [[ "${TEST_JOB_URL}" =~ "Stress" ]] && [[ ! "${target}" =~ "stress" ]]; then
        project_name="Stress"
    elif [[ ${target} = "dvb_stress" ]]; then
        project_name="DVB-Stress"
    elif [[ ${target} = "dvb_s" ]]; then
        project_name="DVB-S"
    elif [[ ${target} = "dvb_t" ]]; then
        project_name="DVB-T"
    elif [[ ${target} = "dvb_trunk" ]]; then
        project_name="DVB-C"
    elif [[ ${target} = "dvb_kpi" ]]; then
        project_name="DVB-KPI"
    elif [[ "${TEST_JOB_URL}" =~ "CAS" ]]; then
        project_name="CAS"
    elif [[ "${TEST_JOB_URL}" =~ "GTS_Autotest" ]]; then
        project_name="GTS"
    elif [[ "${TEST_JOB_URL}" =~ "CTS_Autotest" ]]; then
        project_name="CTS"
    elif [[ "${TEST_JOB_URL}" =~ "VTS_Autotest" ]]; then
        project_name="VTS"
    elif [[ "${TEST_JOB_URL}" =~ "STS_Autotest" ]]; then
        project_name="STS"
    elif [[ "${TEST_JOB_URL}" =~ "TVTS_Autotest" ]]; then
        project_name="TVTS"
    elif [[ "${target}" = "iptv_product_line_p_yuv" ]]; then
        project_name="Android P IPTV YUV"
    elif [[ "${target}" = "iptv_product_line_r_yuv" ]]; then
        project_name="Android R IPTV YUV"
    fi

    echo "$project_name"
}

function func_saveAllureReport() {
    echo " --- start to generate allure report"
    func_environment_info
    START_TIME=$(func_getStartTime)
    remote_user="amlogic"
    remote_password="Linux2023"
    remote_ip="10.18.11.98"
    target=$(jq -r '.target.prj' "$WORKSPACE/AutoTestRes/scripts/python/target.json")
    test_data_path="/home/amlogic/FAE/AutoTest/allure_test_data/$target"
    cas_data_path="/home/amlogic/FAE/AutoTest/allure_test_data/android_s_cas"
    stress_data_path="/home/amlogic/FAE/AutoTest/allure_test_data/android_s_stress"
    dvb_stress_data_path="/home/amlogic/FAE/AutoTest/allure_test_data/DVB_C_stress"
    report_path="/home/amlogic/FAE/AutoTest/AllureReport/$target/$START_TIME/report"
    if [[ "$WORKSPACE" =~ "_CAS" ]]; then
        sshpass -p "$remote_password" ssh "$remote_user@$remote_ip" "[ -d \"$cas_data_path/datas\" ] || mkdir -p \"$cas_data_path/datas\""
        sleep 1
        sshpass -p "$remote_password" scp -r "${AUTO_ALLURE}"/* "$remote_user@$remote_ip:\"$cas_data_path/datas\""
	scp_exit_code=$?
	if [[ $scp_exit_code -eq 0 ]]; then
	    echo "scp files successfully!"
	fi
    elif [[ "$WORKSPACE" =~ "Autotest_Multi_Stress" ]]; then
        sshpass -p "$remote_password" ssh "$remote_user@$remote_ip" "[ -d \"$stress_data_path/datas\" ] || mkdir -p \"$stress_data_path/datas\""
        sleep 1
        sshpass -p "$remote_password" scp -r "${AUTO_ALLURE}"/* "$remote_user@$remote_ip:\"$stress_data_path/datas\""
	scp_exit_code=$?
        if [[ $scp_exit_code -eq 0 ]]; then
            echo "scp files successfully!"
        fi
    elif [[ "$WORKSPACE" =~ "DVB_C" ]] && [[ "$WORKSPACE" =~ "Stress" ]]; then
        sshpass -p "$remote_password" ssh "$remote_user@$remote_ip" "[ -d \"$dvb_stress_data_path/datas\" ] || mkdir -p \"$dvb_stress_data_path/datas\""
        sleep 1
        sshpass -p "$remote_password" scp -r "${AUTO_ALLURE}"/* "$remote_user@$remote_ip:\"$dvb_stress_data_path/datas\""
	scp_exit_code=$?
        if [[ $scp_exit_code -eq 0 ]]; then
            echo "scp files successfully!"
        fi
    else
        get_last_allure_report  $target
        sshpass -p "$remote_password" ssh "$remote_user@$remote_ip" "[ -d \"$test_data_path/datas\" ] || mkdir -p \"$test_data_path/datas\""
        sleep 1
        sshpass -p "$remote_password" scp -r "${AUTO_ALLURE}"/* "$remote_user@$remote_ip:\"$test_data_path/datas\""
        scp_exit_code=$?
        if [[ $scp_exit_code -eq 0 ]]; then
            sshpass -p "$remote_password" ssh "$remote_user@$remote_ip" "allure generate \"$test_data_path/datas\" -o \"$report_path\" --clean"
            allure_exit_code=$?
            if [[ $allure_exit_code -eq 0 ]]; then
                echo "Allure Report successfully generated, delete test data!"
                sshpass -p "$remote_password" ssh "$remote_user@$remote_ip" "rm -rf \"$test_data_path/datas\""
            fi
        else
            echo "SCP file failed, can't generate report!"
        fi
    fi
    echo "Restore tox.ini file…………"
    sed -i '/^ *pytest -v -s/s@^ *pytest -v -s.*@    pytest -v -s {posargs}@' $WORKSPACE/AutoTestRes/scripts/python/tox.ini
    echo " --- end to generate allure report"

    html_file=""
    # 远程HTML文件路径和本地临时文件路径
    if [[ "$TEST_JOB_URL" =~ "SZ" ]]; then
        sz_html_file="/home/amlogic/FAE/AutoTest/shenzhen.html"
        html_file=$sz_html_file
    elif [[ "$SERVER_IP" =~ "XA" ]]; then
        xa_html_file="/home/amlogic/FAE/AutoTest/xian.html"
        html_file=$xa_html_file
    else
        sh_html_file="/home/amlogic/FAE/AutoTest/index.html"
        html_file=$sh_html_file
    fi
    remote_directory="/home/amlogic/FAE/AutoTest/"

    # 下载远程HTML文件到本地
#    sshpass -p "$remote_password" scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -P 22 "$remote_user@$remote_ip:$sh_html_file" "$local_html_file"

    project_name=$(func_get_project_name "$target" "$TEST_JOB_URL")

    android_version="Android_S"
    if [[ "${TEST_JOB_URL}" =~ "Android_U" ]]; then
      android_version="Android_U"
    fi

    class_name=$project_name
    test_report_prefix="http://aut.amlogic.com/AutoTest/AllureReport/$target/$START_TIME/report"

    chipset=""
    if [[ "$TEST_BOARD_TYPE" =~ "ohm" ]] && [[ ! "$TEST_BOARD_TYPE" =~ "tkl" ]] && [[ ! "$TEST_BOARD_TYPE" =~ "nocs" ]]; then
      chipset="S905X4"
    elif [[ "$TEST_BOARD_TYPE" =~ "oppen" ]] && [[ ! "$TEST_BOARD_TYPE" =~ "oppencas" ]] ; then
      chipset="S905Y4"
    elif [[ "$TEST_BOARD_TYPE" =~ "oppencas" ]]; then
      chipset="S905C3"
    elif [[ "$TEST_BOARD_TYPE" =~ "ohm_hybrid_tkldtvkit" ]]; then
      chipset="S905C2"
    elif [[ "$target" = "iptv_product_line_p_yuv" ]]; then
      chipset="P291"
    elif [[ "$target" = "iptv_product_line_r_yuv" ]]; then
      chipset="S928X"
    else
      chipset="S905C2L"
    fi
    # 调用远程服务器上的Python函数
    if [[ "$WORKSPACE" =~ "_CAS" ]] || [[ "$WORKSPACE" =~ "_Stress" ]]; then
        echo "wait all job run finished!"
    else
        sshpass -p "$remote_password" ssh "$remote_user@$remote_ip" "cd $remote_directory; python3 -c 'from replace_variables import generate_html_file; generate_html_file(\"$android_version\", \"$html_file\", \"$project_name\", \"$class_name\", \"$chipset\", \"$test_report_prefix\", \"$BUILD_JOB_URL\", \"$BUILD_NUMBER\")'"
    fi
}

function func_pushDeviceCheck() {
    echo " start to push device_check"

    adb root
    adb remount
    adb push ${AUTO_DEVICECHK} /system/bin/
}

# Check DUT status pre download image.
# If DUT adb status is "recovery/NA" will skip test
if [[ $PROJECT_SERIES =~ "Android" && $PROJECT_SERIES != "Android_K" && ! ${TEST_BOARD_TYPE} =~ "iptv" && $PROJECT_SERIES != "Android_T" ]]; then
    echo "Check DUT adb port status pre download image."
    echo "adb devices SN: $ADB_SN"
    func_checkDutAndRecovery;
    dutStatus=$?
    if [ $dutStatus -eq 2 ]; then
        func_updateReportFile "FailReason" "DUT was out of service<br>Due to upgrade pre version fail and rescure DUT by update tool fail";
        func_preTestFailSaveLogs;
        sleep 120
        exit 1
    fi
    echo "Check DUT adb port status pre download image---check done!"
else
    echo "Do not need check anything!"
fi

##################################################################################
#download firmware.
##################################################################################
echo " --- Start to download firmware"
if [[ $PROJECT_SERIES =~ "Android" ]]; then
        echo " --- --- if project_series is Android, $Test_Image_URL"
    if [[ ${Test_Image_URL} =~ 'http://' ]]; then  # if 'http://' is exist in Test_Image_URL, then run
        func_checkManualBuild ${Test_Image_URL}

        FILESERVER=$Test_Image_URL
        echo " --- --- Android test_image_url: $FILESERVER:"
        if [[ $FILESERVER =~ '.bz2' ]]; then
            #http://10.28.8.100/shenzhen/image/android/Android-K/trunk/2019-10-31/shmobile-user-android32-kernel32-AOSP-61/aml_upgrade_img-20191101.tar.bz2
            BUILD_INFO=$(echo $FILESERVER | awk -F '/' '{ i=1; while(i<=NF) {if( $i ~ /[A-Za-z].+-.+-.+-.+-.+-/) print $i; i++} }')
            echo "bz2 Build information: $BUILD_INFO"
            IMGE_URL=$FILESERVER
            IS_BUILD_COMPRESS='yes'
            func_downloadImgFile $FILESERVER $IS_BUILD_COMPRESS;
            echo " --- --- func_downloadImgFile: done"
        elif [[ $FILESERVER =~ '.img' ]]; then
            echo "img Build information: $FILESERVER"
            IMGE_URL=$FILESERVER
            IS_BUILD_COMPRESS='no'
            func_downloadImgFile $FILESERVER $IS_BUILD_COMPRESS;
            echo " --- --- func_downloadImgFile: done"
        elif [[ $FILESERVER =~ '.zip' ]]; then
            #http://10.28.8.100/shenzhen/image/android/Android-P/Android_TV/trunk/2019-11-20/curie-userdebug-android32-kernel32-GTVS-745/curie-fastboot-flashall-20191120.zip
            BUILD_INFO=$(echo $FILESERVER | awk -F '/' '{ i=1; while(i<=NF) {if( $i ~ /[A-Za-z].+-.+-.+-.+-.+-/) print $i; i++} }')
            echo " Zip Build information: $BUILD_INFO"
            IMGE_URL=$FILESERVER
            func_downloadFastbootFile $FILESERVER;
            echo " --- --- func_downloadFastbootFile: done"
        elif [[ $FILESERVER =~ '.tgz' ]]; then
            #http://qa-sz.amlogic.com:8882/#/CustomerBuild/TV/Jane/T950X4/09062021/release-almond-bt-PMAIN1_userdebug_1923.tgz
            BUILD_INFO=$(echo $FILESERVER | awk -F '/' '{ i=1; while(i<=NF) {if( $i ~ /[A-Za-z].+-.+-.+-.+-.+-/) print $i; i++} }')
            echo " tgz Build information: $BUILD_INFO"
            IMGE_URL=$FILESERVER
            func_downloadFastboottgzFile $FILESERVER;
            echo " --- --- func_downloadFastboot tgz File: done"
        elif [[ $FILESERVER =~ 'S928X' ]]; then
            echo " --- --- iptv / Android_R Build information:"
            URL=${FILESERVER}/aml_S928X_upgrade_package.img.tgz
            func_downloadTestImage "S928X" $URL;
        else
            if [[ ${TEST_BOARD_TYPE} =~ "iptv" || $PROJECT_SERIES =~ "Android_K" || $PROJECT_SERIES =~ "Android_T" || ${TEST_JOB_URL} =~ "DVB" || ${TEST_JOB_URL} =~ "Multi_Stress" || ${TEST_JOB_URL} =~ "KPI" || ${TEST_JOB_URL} =~ "Android_S_Hybrid_Openlinux_Autotest" || ${TEST_JOB_URL} =~ "Android_U_Hybrid_Openlinux_Autotest" ]]; then
                echo " --- --- iptv / Android_K Build information:"
                # http://10.28.8.100/shenzhen/image/android/Android-K/trunk/2019-09-10/shmobile-user-android32-kernel32-AOSP-8/
                BUILD_INFO=$(echo $FILESERVER | awk -F '/' '{ i=1; while(i<=NF) {if( $i ~ /[A-Za-z].+-.+-.+-.+-.+-/) print $i; i++} }')
                DATE_STR=$(echo $FILESERVER | awk -F '/' '{ i=1; while(i<=NF) {if( $i ~ /^[0-9]+-/) print $i; i++} }')
                MDATE1=$(echo $DATE_STR | tr -cd "[0-9]")

                URL=${FILESERVER}aml_upgrade_img-${MDATE1}-${Test_BUILD_NUMBER}.tar.bz2

                get_http_code=`curl -I -m 10 -o /dev/null -s -w %{http_code} $URL`
                echo "$URL status is: $get_http_code"

                if [ $get_http_code != "200" ]; then
                    echo " Android for K Test image is not available, Error code: HTTP 404"
                    func_updateReportFile "FailReason" "Test image is not available";
                else
                    IMGE_URL=$URL
                    IS_BUILD_COMPRESS='yes'
                    func_downloadImgFile $URL $IS_BUILD_COMPRESS;
                fi

            else
                BUILD_INFO=$(echo $FILESERVER | awk -F '/' '{ i=1; while(i<=NF) {if( $i ~ /[A-Za-z].+-.+-.+-.+-.+-/) print $i; i++} }')
                DATE_STR=$(echo $FILESERVER | awk -F '/' '{ i=1; while(i<=NF) {if( $i ~ /^[0-9]+-/) print $i; i++} }')
                TODAY_MDATE=$(echo $split_str | tr -cd "[0-9]")  # get the number string from split_str

                echo "Other Build information: $BUILD_INFO"
                func_downloadTestImage "fat" $FILESERVER;
            fi
        fi
    else
        # auto download
        func_checkBuild;
        # if task is hourly, add build path to test_job_info.txt file
        if [ $TASK_TYPE = "HourlyBuild" ]; then
            echo ${FILESERVER} >> ${AUTO_OUTPUT}/test_job_info.txt
            echo ${FILESERVER} >> ${AUTO_TMP}/test_job_info.txt
            #func_downloadTestImage "abi" $FILESERVER;
        fi

        if [[ ${TEST_BOARD_TYPE} =~ "iptv" || $PROJECT_SERIES =~ "Android_K" || ${UPDATE_TOOL} =~ "adnl" ]]; then
            #func_downloadTestImage "img" $FILESERVER;
            func_downloadTestImage "aml_p291" $FILESERVER;
        elif [[ ${UPDATE_TOOL} =~ "fastboot" ]]; then
            func_downloadTestImage "fat" $FILESERVER;
        fi
    fi # end of download android image from auto url

else
    echo "Download Linux image."
    if [[ ${Test_Image_URL} =~ 'http://' ]]; then  # if 'http://' is exist in Test_Image_URL, then run
        FILESERVER=${Test_Image_URL}
        if [[ $PROJECT_SERIES =~ "RTOS" ]]; then
            func_updateReportFile "Image URL" $Test_Image_URL;
            for files in ci_load.sh \
                        dspboot.bin \
                        rtos-uImage \
                        u-boot.bin \
                        u-boot.bin.usb.bl2
            do
                get_http_code=`curl -I -m 10 -o /dev/null -s -w %{http_code} ${FILESERVER}${files}`
                echo "$URL status is: $get_http_code"
                if [ $get_http_code == "404" ]; then
                    echo " Linux Test image is not available, Error code: HTTP 404"
                    func_updateReportFile "FailReason" "Test image is not available";
                    func_preTestFailSaveLogs;
                    sleep 120
                    exit 1
                fi
                URL=${FILESERVER}${files}
                echo -e "Download file: $URL\nDownloading ..."
                wget -q -c $URL -O ${DOWNLOAD_PATH}/${files}
            done

            # copy files to image folder
            cp ${DOWNLOAD_PATH}/* ${AUTO_IMAGE}/
            # copy adnl to image folder
            cp ${AUTO_BIN}/adnl ${AUTO_IMAGE}/

            IMGE_URL=$FILESERVER
        elif [[ $PROJECT_SERIES =~ "Kernel" ]]; then
            URL=${FILESERVER}aml_upgrade_package.img
            func_updateReportFile "Image URL" $URL;
            get_http_code=`curl -I -m 10 -o /dev/null -s -w %{http_code} $URL`
            echo "$URL status is: ${get_http_code}"
            if [ $get_http_code != "200" ]; then
                echo " Kernel Test image is not available, Error code: HTTP 404"
                func_updateReportFile "FailReason" "Test image is not available";
                func_preTestFailSaveLogs;
                sleep 120
                exit 1
            else
                echo -e "Download file: $URL\nDownloading ..."
                wget -q -c $URL -O ${DOWNLOAD_PATH}/aml_upgrade_package.img
                # copy files to image folder
                cp ${DOWNLOAD_PATH}/aml_upgrade_package.img ${AUTO_IMAGE}/
                IMGE_URL=$URL
            fi
        elif [[ $PROJECT_SERIES =~ "Bootloader" ]]; then
            echo "This is Bootloader user define parameter."

        else
#            URL=${FILESERVER}aml_upgrade_package.img
            URL=${FILESERVER}

            func_updateReportFile "Image URL" $URL;
            get_http_code=`curl -I -m 10 -o /dev/null -s -w %{http_code} $URL`
            echo "$URL status is: ${get_http_code}"
            if [ $get_http_code != "200" ]; then
                echo " Bootloader Test image is not available, Error code: HTTP 404"
                func_updateReportFile "FailReason" "Test image is not available";
                func_preTestFailSaveLogs;
                sleep 120
                exit 1
            else
                echo -e "Download file: $URL\nDownloading ..."
                wget -q -c $URL -O ${DOWNLOAD_PATH}/aml_upgrade_package_img.tgz
                echo " --- untar aml_upgrade_package_img.tgz ..."
                tar -xzvf ${DOWNLOAD_PATH}/aml_upgrade_package.img.tgz -C ${DOWNLOAD_PATH}  # .img
                if [ $? -ne 0 ]; then
                    echo " --- untar aml_upgrade_package_img.tgz failure,exit!"
                    func_updateReportFile "FailReason" "aml_upgrade_package_img.tgz failure failure";
                    func_preTestFailSaveLogs;
                    sleep 120
                    exit 1
                fi
#                wget -q -c $URL -O ${DOWNLOAD_PATH}/aml_upgrade_package.img
                # copy files to image folder
                cp ${DOWNLOAD_PATH}/aml_upgrade_package.img ${AUTO_IMAGE}/
                IMGE_URL=$URL
            fi
        fi
    else
        # Linux/RTOS/Kernel
        echo "Test image URL is NULL, download from autobuild URL"

        if [[ $PROJECT_SERIES =~ "RTOS" ]]; then
            func_checkBuild;
            func_updateReportFile "Image URL" $FILESERVER;
            for files in ci_load.sh \
                        dspboot.bin \
                        rtos-uImage \
                        u-boot.bin \
                        u-boot.bin.usb.bl2
            do
                func_checkUrlStatus ${FILESERVER}${files};
                ret=$?
                if [ $ret -ne 0 ]; then
                    echo " RTOS Test image is not available, Error code: HTTP 404"
                    func_updateReportFile "FailReason" "Test image is not available";
                    func_preTestFailSaveLogs;
                    sleep 120
                    exit 1
                fi
                URL=${FILESERVER}${files}
                echo -e "Download file: $URL\nDownloading ..."
                wget -q -c $URL -O ${DOWNLOAD_PATH}/${files}
            done

            # copy files to image folder
            cp ${DOWNLOAD_PATH}/* ${AUTO_IMAGE}/
            # copy adnl to image folder
            cp ${AUTO_BIN}/adnl ${AUTO_IMAGE}/

            IMGE_URL=$FILESERVER

        elif [[ $PROJECT_SERIES =~ "Kernel" ]]; then
            func_checkBuild;

            func_downloadTestImage "img" $FILESERVER;

        elif [[ $PROJECT_SERIES =~ "Bootloader" ]]; then
            func_checkBuild;
            URL=${FILESERVER}u-boot.bin
            IMGE_URL=$URL
            func_updateReportFile "Image URL" $URL;
            #echo -e "Download file: $URL\nDownloading ..."
            #wget -q -c $URL -O ${DOWNLOAD_PATH}/u-boot.bin
            echo -e "Download file: ${FILESERVER}u-boot.bin.usb.signed\nDownloading ..."
            wget -q -c ${FILESERVER}u-boot.bin.usb.signed -O ${DOWNLOAD_PATH}/u-boot.bin.usb.signed
            echo -e "Download file: ${FILESERVER}u-boot.bin.signed\nDownloading ..."
            wget -q -c ${FILESERVER}u-boot.bin.signed -O ${DOWNLOAD_PATH}/u-boot.bin.signed
            cp ${DOWNLOAD_PATH}/* ${AUTO_IMAGE}/

        else
            # Linux base product
            func_checkBuild;
            func_downloadTestImage "img" $FILESERVER;
        fi
    fi

fi

function func_stress() {
  if [[ $ADB_SN =~ "monkey" ]]; then
      sed -i  's/\("prj":\).*/"prj": "ott_hybrid_monkey_stress"/g' target.json
      python3 localtest_runner.py -m AATS_OTT_STRESS_MONKEY
  elif [[ $ADB_SN = "reboot" ]]; then
      sed -i  's/\("prj":\).*/"prj": "ott_hybrid_reboot_stress"/g' target.json
      python3 localtest_runner.py -m AATS_OTT_STRESS_REBOOT
  elif [[ $ADB_SN =~ "wifi" ]]; then
      sed -i  's/\("prj":\).*/"prj": "ott_hybrid_wifi_stress"/g' target.json
      python3 localtest_runner.py -m AATS_OTT_STRESS_WIFI
  elif [[ $ADB_SN =~ "suspend" ]]; then
      sed -i  's/\("prj":\).*/"prj": "ott_hybrid_suspend_stress"/g' target.json
      python3 localtest_runner.py -m AATS_OTT_STRESS_SUSPEND
  elif [[ $ADB_SN =~ "shutdown" ]]; then
      sed -i  's/\("prj":\).*/"prj": "ott_hybrid_shutdown_stress"/g' target.json
      python3 localtest_runner.py -m AATS_OTT_STRESS_SHUTDOWN
  elif [[ $ADB_SN =~ "av_play" ]]; then
      sed -i  's/\("prj":\).*/"prj": "ott_hybrid_av_play_stress"/g' target.json
      python3 localtest_runner.py -m AATS_OTT_STRESS_AV_PLAY
  elif [[ $ADB_SN =~ "factory_reset" ]]; then
      sed -i  's/\("prj":\).*/"prj": "ott_hybrid_factory_reset_stress"/g' target.json
      python3 localtest_runner.py -m AATS_OTT_STRESS_FACTORY_RESET
  elif [[ $ADB_SN = "uboot_reboot" ]]; then
      sed -i  's/\("prj":\).*/"prj": "ott_hybrid_uboot_reboot_stress"/g' target.json
      python3 localtest_runner.py -m AATS_OTT_STRESS_UBOOT_REBOOT
  elif [[ $ADB_SN =~ "switch_audioTrack" ]]; then
      sed -i  's/\("prj":\).*/"prj": "ott_hybrid_switch_audio_track_stress"/g' target.json
      python3 localtest_runner.py -m AATS_OTT_STRESS_SWITCH_AUDIO_TRACK
  elif [[ $ADB_SN =~ "switch_subtitleTrack" ]]; then
      sed -i  's/\("prj":\).*/"prj": "ott_hybrid_switch_subtitle_track_stress"/g' target.json
      python3 localtest_runner.py -m AATS_OTT_STRESS_SWITCH_SUBTITLE_TRACK
  elif [[ $ADB_SN =~ "youtube" ]]; then
      sed -i  's/\("prj":\).*/"prj": "ott_hybrid_youtube_stress"/g' target.json
      python3 localtest_runner.py -m AATS_OTT_STRESS_YOUTUBE
  else
      sed -i  's/\("prj":\).*/"prj": "ott_hybrid_power_stress"/g' target.json
      python3 localtest_runner.py -m AATS_OTT_STRESS_POWER
  fi
}

#upgrade firmware.
if [[ $PROJECT_SERIES =~ "Android" ]]; then
    func_checkAdbStatus;
    adbDevicesStatus=$?
    echo "Adb devices status code is: $adbDevicesStatus"
    if [ $adbDevicesStatus != 0 ]; then
        echo "=========>Rescure DUT by update tool"
        upgrademode="update"
    fi
fi
if [[ $PROJECT_SERIES =~ "RTOS" ]]; then
    # set DUT in upgrade mode
    echo "${AUTO_BIN}/setDutInUpdateMode ${DUT_Serial_Port} \
    ${DUT_SERIAL_PORT_BAUDRATE} \
    ${PowerRelay_Serial_Port} \
    ${WORKSPACE}/AutoTestRes \
    ${UPDATE_TOOL}"

    ${AUTO_BIN}/setDutInUpdateMode ${DUT_Serial_Port} \
    ${DUT_SERIAL_PORT_BAUDRATE} \
    ${PowerRelay_Serial_Port} \
    ${WORKSPACE}/AutoTestRes \
    ${UPDATE_TOOL}

    ${AUTO_BIN}/update/adnl devices
    ${AUTO_BIN}/update/adnl oem  "store erase.chip"

    func_rebootDutByRelayDelayTime 5;

    cd ${AUTO_IMAGE}
    bash ci_load.sh &
    sleep 60

    # Kill ci_load.sh after dut boot done.
    ps -ef | grep "ci_load" | grep -v grep | awk '{print $2}' | xargs kill -9

elif [[ $PROJECT_SERIES =~ "Bootloader" ]]; then
    echo "Bootloader testing do not need flash image in pre-test stage, pass."
!
#elif [[ ${TEST_BOARD_TYPE} =~ "iptv" || $PROJECT_SERIES =~ "Android_K"  || $PROJECT_SERIES =~ "Linux" || $PROJECT_SERIES =~ "Kernel" ]]; then

#if [[ ${TEST_BOARD_TYPE} =~ "iptv" || $PROJECT_SERIES =~ "Android_R"  || $PROJECT_SERIES =~ "Linux" || $PROJECT_SERIES =~ "Kernel" ]]; then
elif [[ $PROJECT_SERIES =~ "IPTV" || $PROJECT_SERIES =~ "Android_K" || $PROJECT_SERIES =~ "Linux" || $PROJECT_SERIES =~ "Kernel" || $upgrademode =~ "update" || $TEST_BOARD_TYPE == "p291_iptv" ]]; then

    echo " --- Start to upgrade firmware"
    # Upgrade DUT by update tool
    # kill reboot logging process as setDutInUpdateMode needs to occupy the serial port
    func_killRebootLoggingThread;
    sleep 1

    # Lock autoTestFlashImage.lock file
    if [ $is_skip_boot_partition = "yes" ]; then
        flock -x ~/.autoTestflashImage.lock \
        -c "bash ${WORKSPACE}/AutoTestRes/scripts/shell/upgrade_image.sh \
        $WORKSPACE \
        $DUT_Serial_Port \
        ${DUT_SERIAL_PORT_BAUDRATE} \
        $PowerRelay_Serial_Port \
        aml_upgrade_package.img \
        false \
        ${UPDATE_TOOL}"
    elif [ ${TEST_BOARD_TYPE} == "p291_iptv" ]; then
        flock -x ~/.autoTestflashImage.lock \
        -c "bash ${WORKSPACE}/AutoTestRes/scripts/shell/upgrade_image.sh \
        $WORKSPACE \
        $DUT_Serial_Port \
        ${DUT_SERIAL_PORT_BAUDRATE} \
        $PowerRelay_Serial_Port \
        aml_p291_prue_for_s905l_upgrade_package.img \
        true \
        ${UPDATE_TOOL}"
    else
        flock -x ~/.autoTestflashImage.lock \
        -c "bash ${WORKSPACE}/AutoTestRes/scripts/shell/upgrade_image.sh \
        $WORKSPACE \
        $DUT_Serial_Port \
        ${DUT_SERIAL_PORT_BAUDRATE} \
        $PowerRelay_Serial_Port \
        aml_upgrade_package.img \
        true \
        ${UPDATE_TOOL}"
    fi
    func_checkUpgradeDutStatus;
    updateStatus=$?
    if [ $updateStatus -ne 0 ]; then
        echo "@@@@@@ Upgrade image fail, exit test! @@@@@@"
        func_updateReportFile "FailReason" "Upgrade image by update tool failure";
        func_preTestFailSaveLogs;
        sleep 120
        exit 1
    fi
    if [[ $PROJECT_SERIES =~ "Android" ]]; then
        func_rebootDutByRelayDelayTime 180;
    elif [[ $PROJECT_SERIES =~ "Linux" ]]; then
        func_rebootDutByRelayDelayTime 120;
    fi


elif [[ $PROJECT_SERIES =~ "Android_R" || $PROJECT_SERIES =~ "Android_S" || $PROJECT_SERIES =~ "Android_T" || $PROJECT_SERIES =~ "Android_U"  || $PROJECT_SERIES =~ "Zapper" ]]; then
    echo " --- Start to upgrade firmware from $PROJECT_SERIES"
    cd ${AUTO_IMAGE}
    if [ ! -L flashImageTool ]; then
        echo "ln -s ${AUTO_BIN}/flashImageTool flashImageTool"
        ln -s ${AUTO_BIN}/flashImageTool flashImageTool
    fi

    if [ ! -L tc_flash-all.sh ]; then
        echo "ln -s ${AUTO_SCRIPT}/tc_flash-all.sh tc_flash-all.sh"
        ln -s ${AUTO_SCRIPT}/tc_flash-all.sh tc_flash-all.sh
    fi
    #Determine whether the burning method is fastboot or update
    if [[ $UPDATE_TOOL =~ "fastboot" ]];then
        echo " --- Start to upgrade with fastboot"
:<<eof
        if [[ $is_skip_boot_partition = "yes" ]]; then
            echo "adb -s $FASTBOOT_SN reboot bootloader"
            adb -s $FASTBOOT_SN reboot bootloader
            echo "sleep 60"
            sleep 60
            echo "check fastboot status"
            func_checkFastbootStatus;
            echo "./flashImageTool skipboot=yes flash-all.bat $FASTBOOT_SN ${AUTO_LOG} ${PROJECT_SERIES} 600"
            ./flashImageTool skipboot=yes flash-all.bat $FASTBOOT_SN ${AUTO_LOG} ${PROJECT_SERIES} 600
        else
            echo "adb reboot bootloader"
            adb reboot bootloader
            echo "sleep 60"
            sleep 60
            echo "check Fastboot Status"
            func_checkFastbootStatus;
            echo "./flashImageTool skipboot=no flash-all.bat $FASTBOOT_SN ${AUTO_LOG} ${PROJECT_SERIES} 600"
            ./flashImageTool skipboot=no flash-all.bat $FASTBOOT_SN ${AUTO_LOG} ${PROJECT_SERIES} 600
        fi
eof
        cp ../scripts/shell/flash-all.sh ./
        bash flash-all.sh ${DUT_ADB_SN}

    elif [[ $UPDATE_TOOL =~ "adnl" ]];then
        echo " --- Start to upgrade with adnl"
        if [[ $is_skip_boot_partition = "yes" ]]; then
            echo "upgrade_image.sh:(1)$WORKSPACE (2)$DUT_Serial_Port (3)${DUT_SERIAL_PORT_BAUDRATE} (4)$PowerRelay_Serial_Port (5)aml_upgrade_package.img (6)false (7)${UPDATE_TOOL} "
            flock -x ~/.autoTestflashImage.lock \
            -c "bash ${WORKSPACE}/AutoTestRes/scripts/shell/upgrade_image.sh \
            $WORKSPACE \
            $DUT_Serial_Port \
            ${DUT_SERIAL_PORT_BAUDRATE} \
            $PowerRelay_Serial_Port \
            aml_upgrade_package.img \
            false \
            ${UPDATE_TOOL}"
        else
            echo "upgrade_image.sh:(1)$WORKSPACE (2)$DUT_Serial_Port (3)${DUT_SERIAL_PORT_BAUDRATE} (4)$PowerRelay_Serial_Port (5)aml_upgrade_package.img (6)true (7)${UPDATE_TOOL} "
            flock -x ~/.autoTestflashImage.lock \
            -c "bash ${WORKSPACE}/AutoTestRes/scripts/shell/upgrade_image.sh \
            $WORKSPACE \
            $DUT_Serial_Port \
            ${DUT_SERIAL_PORT_BAUDRATE} \
            $PowerRelay_Serial_Port \
            aml_upgrade_package.img \
            true \
            ${UPDATE_TOOL}"
        fi

        func_checkUpgradeDutStatus;
        updateStatus=$?
        if [ $updateStatus -ne 0 ]; then
            echo "@@@@@@ Upgrade image fail, exit test! @@@@@@"
            func_updateReportFile "FailReason" "Upgrade image by update tool failure";
            func_preTestFailSaveLogs;
            sleep 120
            exit 1
        fi
    fi

    if [[ $PROJECT_SERIES =~ "Android" ]]; then
        func_rebootDutByRelayDelayTime 180;
    elif [[ $PROJECT_SERIES =~ "Linux" ]]; then
        func_rebootDutByRelayDelayTime 120;
    fi

else
    # flash Android product. android P/Q...
    # echo "Check if there is any devices is in fastboot mode"
    cd ${AUTO_IMAGE}

    echo "Done: fastboot $FASTBOOT_SN_OPTION devices, starting to flash image..."
    if [ ! -L flashImageTool ]; then
        ln -s ${AUTO_BIN}/flashImageTool flashImageTool
    fi

    if [ ! -L tc_flash-all.sh ]; then
        ln -s ${AUTO_SCRIPT}/tc_flash-all.sh tc_flash-all.sh
    fi


    func_killRebootLoggingThread;
    func_startRebootLoggingThread;

    echo " --- TEST_BOARD_TYPE = $TEST_BOARD_TYPE"
    #if [ "TEST_BOARD_TYPE" =~ "amazon_pat" ]; then
    if [[ ${TEST_BOARD_TYPE} =~ "amazon_pat" ]]; then
        echo " --- --- Amazon Test_Image_URL: $Test_Image_URL"
        BUILD_INFO=$(echo $Test_Image_URL |awk -F '/' '{print $11}'|awk -F '.'  '{print $1}')
        DATE_STR=$(echo $Test_Image_URL |awk -F '/' '{print $10}')

        echo " --- --- BUILD_INFO/DATE_STR/: $BUILD_INFO, $DATE_STR"
        chmod 777 -R $BUILD_INFO
        cd $BUILD_INFO
        pwd

        #Mindy
        func_setDutIntoFastbootMode

        echo "./flashimage.py"
        #Mindy
        ./flashimage.py

    elif [ $is_skip_boot_partition = "yes" ]; then
        echo "./flashImageTool skipboot=yes flash-all.bat $FASTBOOT_SN ${AUTO_LOG} ${PROJECT_SERIES} 600"
        ./flashImageTool skipboot=yes flash-all.bat $FASTBOOT_SN ${AUTO_LOG} ${PROJECT_SERIES} 600
    else
        echo "./flashImageTool skipboot=no flash-all.bat $FASTBOOT_SN ${AUTO_LOG} ${PROJECT_SERIES} 600"
        ./flashImageTool skipboot=no flash-all.bat $FASTBOOT_SN ${AUTO_LOG} ${PROJECT_SERIES} 600
    fi

    func_killRebootLoggingThread;

    echo "=================  FASTBOOT UPGRADE PACKAGE SERIAL LOG START  ================="

    #cat ${AUTO_LOG}/pretest.txt

#==========================================================================================

    echo "=================  FASTBOOT UPGRADE PACKAGE SERIAL LOG END    ================="

    update_image_log=$(cat ${AUTO_LOG}/fastbootUpgradeLog.txt)
    if [[ $update_image_log =~ "Connect DUT fail" || $update_image_log =~ "is timeout" ]]; then
        func_updateReportFile "FailReason" "Upgrade image by fastboot timeout, connect DUT fail";
        func_preTestFailSaveLogs;
        echo "===================FASTBOOT UPGRADE PACKAGE CONSOLE FAIL LOG START================="
        cat ${AUTO_LOG}/fastbootUpgradeLog.txt
        echo "===================FASTBOOT UPGRADE PACKAGE CONSOLE FAIL LOG END==================="
        func_checkDutAndRecovery;
        exit 1
    fi

    #Mindy
    func_rebootDutByRelayDelayTime 5;

    func_startRebootLoggingThread;

    echo "Fastboot upgrade package done, waiting 180 seconds to boot dut..."
    sleep 90

    func_killRebootLoggingThread;

    echo "=================  DUT FIRST BOOT AFTER UPGRADE PACKAGE SERIAL LOG START  ================="

    #cat ${AUTO_LOG}/pretest.txt

    func_checkBuildVersion

    echo "=================  DUT FIRST BOOT AFTER UPGRADE PACKAGE SERIAL LOG END    ================="
    sleep 10
fi

echo "The upgrade is successful, restart and wait for 180 seconds"
sleep 180

# Check DUT status after download image.
echo ' --- Check DUT status after download image:'
# If DUT adb status is "recovery/NA" will make this version test fail. and write to gerrit.
if [[ $PROJECT_SERIES =~ "Android" && $PROJECT_SERIES != "Android_K" && ! ${TEST_BOARD_TYPE} =~ "iptv" && $PROJECT_SERIES != "Android_T" ]]; then
    echo " ---  --- Check DUT adb port status after download image."
    echo "adb devices SN: $ADB_SN"
    func_checkDutAndRecovery;
    dutStatus=$?
    if [ $dutStatus -ne 0 ]; then
        func_updateReportFile "FailReason" "DUT boot up fail after upgrade test image";
        func_preTestFailSaveLogs;
        if [ $PATCHSET_IDS != "NULL" ]; then
            echo "[FAIL] After flash image, DUT can not boot up" > $AUTO_REVIEW_INFO
            bash ${AUTO_SCRIPT}/add_comment4patchset.sh ${AUTO_BIN} ${AUTO_REVIEW_INFO} "${PATCHSET_IDS}"
        fi

        func_killRebootLoggingThread;
        echo "====================  SERIAL PORT LOG START ========================"
#============== shield by Mindy 20210428 ===================================================
:<<!

        cat ${AUTO_LOG}/pretest.txt
        echo "====================  SERIAL PORT LOG END   ========================"
!
#==========================================================================================

        exit 1
    fi
    echo " ---  --- Check DUT adb port status after download image"
    adb $ADB_SN_OPTION root
    sleep 2
#============== shield by Mindy 20210428 ===================================================
:<<!
    #func_adbIfaceLostReboot;
!
#==========================================================================================

else
    if [[ ${TEST_BOARD_TYPE} =~ "iptv" || $PROJECT_SERIES =~ "Android_T" ]]; then
        echo "Nothing to check after download image."
    elif [ ${DUT_ADB_SN} != "NotUsed" ]; then
        func_checkLinuxBaseProAdb;
        dutStatus=$?
        if [ $dutStatus -ne 0 ]; then
            func_updateReportFile "FailReason" "DUT boot up fail after upgrade test image";
            func_preTestFailSaveLogs;
            if [ $PATCHSET_IDS != "NULL" ]; then
                echo "[FAIL] After flash image, DUT can not boot up" > $AUTO_REVIEW_INFO
                bash ${AUTO_SCRIPT}/add_comment4patchset.sh ${AUTO_BIN} ${AUTO_REVIEW_INFO} "${PATCHSET_IDS}"
            fi
#============== shield by Mindy 20210428 ===================================================
:<<!

    func_killRebootLoggingThread;

            echo "====================  SERIAL PORT LOG START ========================"
            cat ${AUTO_LOG}/pretest.txt
            echo "====================  SERIAL PORT LOG END   ========================"
!
#==========================================================================================

            exit 1
        fi
    else
        echo "Nothing to check after download image."
    fi
fi

# kill reboot logging process if not exit yet

#============== shield by Mindy 20210428 ===================================================
:<<!

func_killRebootLoggingThread;
!
#==========================================================================================

sleep 1

if [[ $PROJECT_SERIES =~ "Android" ]]; then
    LOGCAT_THREAD="-c script/test_case_logcat_log.sh"
    if [[ $PROJECT_SERIES =~ "Android_K" ]]; then
        OTHER_ARGS="-E 5 -B"
        TEST_TIMER=7200
        LOGCAT_THREAD=
    fi
    # FAE project T5FL disable LOGCAT_THREAD
    if [[ ${TEST_PLAN_NAME} =~ "T963_T5FL_AOSP_DailyBuild_CI_Multi" ]]; then
       LOGCAT_THREAD=
    fi
    # FAE project P291 disable DUT_Serial_Port
    if [[ ${TEST_PLAN_NAME} =~ "S905L3_P291_AOSP_DailyBuild_CI" ]]; then
       DUT_Serial_Port="NotUsed"
    fi
    # patch for DRM test which TV board as the receiver to connect with the test board
    if [[ ${TEST_PLAN_NAME} =~ "S905X2_U215_GTVS_DailyBuild_CI_Multi" ]]; then
        OTHER_ARGS="${OTHER_ARGS} -D AMLT962X3AB301BT165"
        FAIL_RETEST="-r 3 -R Now"
    fi
elif [[ $PROJECT_SERIES =~ "Linux" ]]; then
    FAIL_RETEST="-r 3 -R Now"
    if [[ ${TEST_PLAN_NAME} =~ "S905X2_U212_a6432bit_DailyBuild_YTB" ]]; then
        FAIL_RETEST=
    fi
fi

#============== shield by wxl 20210317 ===================================================
:<<!
#if [[ ${TEST_PLAN_NAME} =~ 'RDK' && ${RDK_TESTPLAN} != "NULL" ]]; then
if [[ ${TEST_PLAN_NAME} =~ 'S905X2_U212_a32bit_DailyBuild_RDK.yml' && ${RDK_TESTPLAN} != "NULL" ]]; then
    ${AUTO_BIN}/serial_batch -p ${DUT_Serial_Port} -b ${DUT_SERIAL_PORT_BAUDRATE} -f ${AUTO_SCRIPT}/rdk_static_ip.txt
    echo "------------------------------"
    echo "Starting to test RDK..."
    sleep 120
    : > ${AUTO_TMP}/rdklogs.txt
    echo "${AUTO_BIN}/tdkRestApi -s aats.amlogic.com:10000 -d ${RDK_DEVICE} -p ${RDK_TESTPLAN} > ${AUTO_TMP}/rdklogs.txt"
    ${AUTO_BIN}/tdkRestApi -s aats.amlogic.com:10000 -d ${RDK_DEVICE} -p ${RDK_TESTPLAN} > ${AUTO_TMP}/rdklogs.txt
    sleep 60
    echo "------------------------------"
fi
!
#==========================================================================================

if [[ ${TEST_JOB_URL} =~ "Android_U_Hybrid_Openlinux_Autotest_Basic_SZ" || ${TEST_JOB_URL} =~ "Android_U_Hybrid_Openlinux_Autotest_Format_Compatibility_SZ" ]]; then
    echo "start burning oem.img"
    cp "/home/amlogic/oem_ms12.img" "$(pwd)" && echo "oem.img copy to $(pwd) success" || echo "oem.img copy fail"
    bash $WORKSPACE/AutoTestRes/scripts/shell/gsi.sh $ADB_SN
fi

if [[ $PROJECT_SERIES != "Android_S_Google_Gretzky"  && $PROJECT_SERIES =~ "Android_S" || $PROJECT_SERIES =~ "Android_T" || $PROJECT_SERIES =~ "Android_U" ]]; then

    echo "start to Android S remount"
    func_adbRemount;
fi

echo "disable bluetooth"
adb -s $DUT_ADB_SN shell svc bluetooth disable


PYTHONSPACE=AutoTestRes/scripts/python
echo "start to test !!! WORKSPACE:$WORKSPACE"
START_TEST_TIME=`date '+%Y.%m.%d_%H.%M'`
func_getStartTime() {
    echo $START_TEST_TIME
    return $?
}
cd $WORKSPACE/$PYTHONSPACE
pwd

# Start to push device_check into DUT
echo " --- Start to push device_check into DUT"
func_pushDeviceCheck;

# Start to run test cases for projects
echo " --- Start to run test cases for projects"
PRJ_INFO=$(echo $Test_Image_URL |awk -F '/' '{print $7}')

#list wifi Dut adb sn
adb devices > adb_sn.txt
DUT_ADB_SN_TMP1=`awk '$0 ~ /288CB8F36360/' adb_sn.txt`
DUT_ADB_SN1=${DUT_ADB_SN_TMP1:0:32}
DUT_ADB_SN_TMP2=`awk '$0 ~ /F09CD75467CA/' adb_sn.txt`
DUT_ADB_SN2=${DUT_ADB_SN_TMP2:0:32}
echo "WIFI5621 DUT_ADB_SN is" $DUT_ADB_SN1
echo "WIFI8822CS DUT_ADB_SN is" $DUT_ADB_SN2

# if server has installed allure ,Pytest run with allure command
if command -v allure &> /dev/null; then
    echo "allure found. Pytest run with allure command"
    # 修改 tox.ini 文件
    sed -i '/^ *pytest -v -s/s@^ *pytest -v -s.*@    pytest -v -s --alluredir=./allure_data {posargs}@' "$WORKSPACE/AutoTestRes/scripts/python/tox.ini"
    if [ -d "$AUTO_ALLURE" ]; then
        rm -rf "$AUTO_ALLURE"
        echo "The history allure_data folder has been removed."
    else
        echo "The allure_data folder does not exist. No need to remove it."
    fi
else
    echo "allure not found, Pytest command does not use allure"
fi

if [[ ${PRJ_INFO} =~ "IPTV" || $PROJECT_SERIES =~ "Android_K"  || $PROJECT_SERIES =~ "Zapper" || $PROJECT_SERIES =~ "KT"  || $PROJECT_SERIES =~ "Kernel" || ${TEST_BOARD_TYPE} == "p291_iptv" || ${TEST_BOARD_TYPE} == "s928x_iptv" ]]; then
    if [[ ${TEST_JOB_URL} =~ 'WIFI' ]];then
        if [[ ${BUILD_INFO} =~ "telecom" ]]; then
            sed -i  's/\("prj":\).*/"prj": "wifi_ctcc"/g' target.json ]]
            sed -i "s/\(\"device_id\": \"\)[[:alnum:]]\+/\1$DUT_ADB_SN2/" ./config/config_wifi_ctcc.json
        else
            sed -i  's/\("prj":\).*/"prj": "wifi_cmcc"/g' target.json
            sed -i "s/\(\"device_id\": \"\)[[:alnum:]]\+/\1$DUT_ADB_SN1/" ./config/config_wifi_cmcc.json
        fi
    elif [[ ${TEST_BOARD_TYPE} == "p291_iptv" ]]; then
        sed -i  's/\("prj":\).*/"prj": "iptv_product_line_p_yuv"/g' target.json
    elif [[ ${TEST_JOB_URL} =~ "Zapper" ]]; then
        sed -i  's/\("prj":\).*/"prj": "zapper"/g' target.json
    elif [[ ${TEST_BOARD_TYPE} == "s928x_iptv" ]]; then
        sed -i  's/\("prj":\).*/"prj": "iptv_product_line_r_yuv"/g' target.json
    elif [[ ${BUILD_INFO} =~ "telecom" ]]; then
        sed -i  's/\("prj":\).*/"prj": "iptv_ctcc"/g' target.json
    elif [[ ${TEST_JOB_URL} =~ "KT" ]]; then
        sed -i  's/\("prj":\).*/"prj": "kt_sanity"/g' target.json
    else
        if [[ ${BUILD_ROOT_PATH} =~ "S905L3A" ]]; then
            sed -i  's/\("prj":\).*/"prj": "iptv_cmcc_l3a"/g' target.json
        else
            sed -i  's/\("prj":\).*/"prj": "iptv_cmcc"/g' target.json
        fi
    fi
    python3 localtest_runner.py -l
    python3 localtest_runner.py --all --retest 2

elif [[ ${PRJ_INFO} =~ "TV" || ${TEST_BOARD_TYPE} =~ "amazon_pat" ]]; then

    #sed -i 's/iptv/tv/' target.json
    #xiaojun.huang
    #PRJ_INFO convert to lowercase，
    PRJ_NAME=$(echo ${PRJ_INFO} | sed 's/[A-Z]/\l&/g')
    #PRJ_NAME write into target.json
    sed -i 's/\("prj":\).*/"prj": "'"$PRJ_NAME"'"/g' target.json
    python3 localtest_runner.py -l
    #python3 localtest_runner.py -m AATS_MTS_SYSTEM_ANTUTU
    #python3 localtest_runner.py -m AATS_MTS_SYSTEM_RESOLTION_SWITCH
    #python3 localtest_runner.py -m AATS_AMAZON_PLATFORM_UPGRADE_FASTBOOT --noflash
    python3 localtest_runner.py --all

elif [[ ${PRJ_INFO} =~ "Android-S_Google_Partner" || $PROJECT_SERIES =~ "Android_S" || $PROJECT_SERIES =~ "Android_T" || $PROJECT_SERIES =~ "Android_U" ]]; then
    if [[ ${TEST_JOB_URL} =~ "DVB_C" ]]; then
        if [[ ${TEST_JOB_URL} =~ "Stress" ]]; then
            if [[ ${ADB_SN} =~ "scan" ]]; then
                sed -i  's/\("prj":\).*/"prj": "dvb_stress_scan"/g' target.json
            elif [[ ${ADB_SN} =~ "channelswitch" ]]; then
                sed -i  's/\("prj":\).*/"prj": "dvb_stress_channel_switch"/g' target.json
            elif [[ ${ADB_SN} =~ "playback" ]]; then
                sed -i  's/\("prj":\).*/"prj": "dvb_stress_playback"/g' target.json
            elif [[ ${ADB_SN} =~ "pvr" ]]; then
                sed -i  's/\("prj":\).*/"prj": "dvb_stress_pvr"/g' target.json
            elif [[ ${ADB_SN} =~ "timeshift" ]]; then
                sed -i  's/\("prj":\).*/"prj": "dvb_stress_timeshift"/g' target.json
            fi
            python3 localtest_runner.py -l
            python3 localtest_runner.py --all
        else
            sed -i  's/\("prj":\).*/"prj": "dvb_trunk"/g' target.json
            python3 localtest_runner.py -l
            python3 localtest_runner.py --all --retest 2
        fi
    elif [[ ${TEST_JOB_URL} =~ "DVB_S" ]]; then
        sed -i  's/\("prj":\).*/"prj": "dvb_s"/g' target.json
        python3 localtest_runner.py -l
        python3 localtest_runner.py --all --retest 2
    elif [[ ${TEST_JOB_URL} =~ "DVB_T" ]]; then
        sed -i  's/\("prj":\).*/"prj": "dvb_t"/g' target.json
        python3 localtest_runner.py -l
        python3 localtest_runner.py --all --retest 2
    elif [[ ${TEST_JOB_URL} =~ "Android_U_Hybrid_Openlinux_Autotest_Sanity" || ${TEST_JOB_URL} =~ "Android_S_Hybrid_Openlinux_Autotest_Sanity" ]]; then
        sed -i  's/\("prj":\).*/"prj": "ott_sanity"/g' target.json
        python3 localtest_runner.py -l --project=ref
        python3 localtest_runner.py --all --project=ref --retest 2
    elif [[ ${TEST_JOB_URL} =~ "Android_U_Google_Boreal_Autotest_Sanity" ]]; then
        sed -i  's/\("prj":\).*/"prj": "ott_sanity"/g' target.json
        python3 localtest_runner.py -l --project=boreal
        python3 localtest_runner.py --all --project=boreal --retest 2
    elif [[ ${PROJECT_SERIES} =~ "Nagratkl" ]]; then
        sed -i  's/\("prj":\).*/"prj": "ott_hybrid_s_nagratkl"/g' target.json
        python3 localtest_runner.py -l
        python3 localtest_runner.py --all --retest 2
    elif [[ ${PROJECT_SERIES} =~ "Nagranocs" ]]; then
        sed -i  's/\("prj":\).*/"prj": "ott_hybrid_s_nagranocs"/g' target.json
        python3 localtest_runner.py -l
        python3 localtest_runner.py --all --retest 2
    elif [[ ${PROJECT_SERIES} =~ "KPI" ]]; then
        if [[ $ADB_SN =~ "skpi" ]]; then
          sed -i  's/\("prj":\).*/"prj": "ott_hybrid_s_kpi"/g' target.json
          python3 localtest_runner.py -l
          python3 localtest_runner.py --all
        else
          sed -i  's/\("prj":\).*/"prj": "ott_hybrid_t_kpi"/g' target.json
          python3 localtest_runner.py -l
          python3 localtest_runner.py --all
        fi
    elif [[ ${TEST_JOB_URL} =~ "Android_S_Hybrid_Openlinux_Autotest_YuvCheck" ]]; then
        sed -i  's/\("prj":\).*/"prj": "ott_hybrid_s_yuv"/g' target.json
        python3 localtest_runner.py -l
        python3 localtest_runner.py --all --retest 2
    elif [[ ${TEST_JOB_URL} =~ "Android_U_Hybrid_Openlinux_Autotest_YuvCheck" ]]; then
        sed -i  's/\("prj":\).*/"prj": "ott_hybrid_s_yuv"/g' target.json
        python3 localtest_runner.py -l
        python3 localtest_runner.py --all --retest 2
    elif [[ ${TEST_JOB_URL} =~ "Android_T_Hybrid_Autotest_Compatibility" ]]; then
        sed -i  's/\("prj":\).*/"prj": "ott_hybrid_t_compatibility"/g' target.json
        python3 localtest_runner.py -l
        python3 localtest_runner.py --all --retest 2
    elif [[ ${TEST_JOB_URL} =~ "Android_S_Hybrid_Openlinux_Autotest_Compatibility" ]]; then
        sed -i  's/\("prj":\).*/"prj": "ott_hybrid_compatibility"/g' target.json
        python3 localtest_runner.py -l
        python3 localtest_runner.py --all --retest 2
    elif [[ ${TEST_JOB_URL} =~ "Android_T_Hybrid_Autotest" ]]; then
        sed -i  's/\("prj":\).*/"prj": "ott_hybrid_t"/g' target.json
        python3 localtest_runner.py -l
        python3 localtest_runner.py --all --retest 2
    elif [[ ${PROJECT_SERIES} =~ "Google_Gretzky" ]]; then
        sed -i  's/\("prj":\).*/"prj": "google_gretzky"/g' target.json
        python3 localtest_runner.py -l
        python3 localtest_runner.py --all
    elif [[ ${TEST_JOB_URL} =~ "Android_S_Hybrid_Openlinux_Autotest_Multi_Stress" ]]; then
        func_stress;
    elif [[ ${TEST_JOB_URL} =~ "Android_S_Hybrid_Openlinux_Autotest_Widevine_CAS" ]]; then
        sed -i  's/\("prj":\).*/"prj": "ott_hybrid_widevine_cas"/g' target.json
        python3 localtest_runner.py -l
        python3 localtest_runner.py --all --retest 2
    elif [[ ${TEST_JOB_URL} =~ "Android_S_Hybrid_Openlinux_Autotest_CAS_Vmx_Iptv" ]]; then
        sed -i  's/\("prj":\).*/"prj": "ott_hybrid_vmx_iptv"/g' target.json
        python3 localtest_runner.py -l
        python3 localtest_runner.py --all --retest 2
    elif [[ ${TEST_JOB_URL} =~ "Android_S_Hybrid_Openlinux_Autotest_Irdeto_DVB" ]]; then
        sed -i  's/\("prj":\).*/"prj": "dvb_s_irdeto"/g' target.json
        python3 localtest_runner.py -l
        python3 localtest_runner.py --all --retest 2
    elif [[ ${TEST_JOB_URL} =~ "Android_T_Google_AOSP_Autotest" ]]; then
        sed -i  's/\("prj":\).*/"prj": "ddr"/g' target.json
        python3 localtest_runner.py -l
        python3 localtest_runner.py --all
    elif [[ ${TEST_JOB_URL} =~ "Android_U_Hybrid_Openlinux_Autotest_Format_Compatibility" ]]; then
        sed -i  's/\("prj":\).*/"prj": "ott_hybrid_playback_strategy"/g' target.json
        python3 localtest_runner.py -l
        python3 localtest_runner.py --all
    else
        sed -i  's/\("prj":\).*/"prj": "ott_hybrid"/g' target.json
        python3 localtest_runner.py -l
        python3 localtest_runner.py --all --retest 2
    fi
else
    sed -i  's/\("prj":\).*/"prj": "ott"/g' target.json
    #sed -i 's/iptv/ott/' target.json
    python3 localtest_runner.py -l
    python3 localtest_runner.py --all
fi

func_saveResult;
func_saveAllureReport;
exit 0

#============== shield by wxl 20210317 ===================================================
:<<!
# Run test
cd ${WORKSPACE}/AutoFramework

echo "Debug Test plan is: $TEST_PLAN_NAME"

echo "Start test at:" `date +%Y/%m/%d-%H:%M:%S`

echo "timeout 10h ./aats_linux_cmd -p $TEST_PLAN_NAME \
    -b -i ${BUILD_INFO} \
    -d ${ADB_SN} \
    -s ${DUT_Serial_Port} \
    -S ${PowerRelay_Serial_Port} \
    -T ${TEST_TIMER} \
    -U ${DUT_SERIAL_PORT_BAUDRATE} \
    -I ${IMGE_URL} ${FAIL_RETEST} ${LOGCAT_THREAD} ${OTHER_ARGS}"
timeout 10h ./aats_linux_cmd -p $TEST_PLAN_NAME \
    -b -i ${BUILD_INFO} \
    -d ${ADB_SN} \
    -s ${DUT_Serial_Port} \
    -S ${PowerRelay_Serial_Port} \
    -T ${TEST_TIMER} \
    -U ${DUT_SERIAL_PORT_BAUDRATE} \
    -I ${IMGE_URL} ${FAIL_RETEST} ${LOGCAT_THREAD} ${OTHER_ARGS}

if [ $? -ne 0 ]; then
   echo "Test not excute pass, exit!"
   exit 1
else
    #get latest folder name for android
    report_folder_name=`ls -lt ${AUTO_OUTPUT}/${PRJ_FOLDER_NAME} | grep drw | head -n 1 |awk '{print $9}'`
    output_folder_path=${PRJ_FOLDER_NAME}/${report_folder_name}
    rm ${AUTO_TMP}/report_template_upgradefail.html
    cp ${AUTO_TMP}/* ${AUTO_OUTPUT}/${output_folder_path}/
    tt=$(sed -n "1p" ${AUTO_TMP}/test_job_info.txt)
    timestamp_path=$(echo "${tt:0:4}/${tt:4:2}/${tt:6:2}/${tt:9}")
    result_url=http://aats.amlogic.com/files/jenkins/html/archive_data/${timestamp_path}
    mv ${AUTO_TMP}/test_job_info.txt ${AUTO_OUTPUT}/${output_folder_path}/test_job_info.txt

    ##################################################################################
    #if it is hourly build, download project xml/changeid.txt file
    ##################################################################################
    if [ $TASK_TYPE = "HourlyBuild" ]; then
        wget -c ${FILESERVER}project.xml -O ${AUTO_OUTPUT}/${output_folder_path}/project.xml
        wget -c ${FILESERVER}changeid.txt -O ${AUTO_OUTPUT}/${output_folder_path}/changeid.txt
        wget -c ${FILESERVER}repo_ajax.txt -O ${AUTO_OUTPUT}/${output_folder_path}/repo_ajax.txt
        wget -c ${FILESERVER}cl_detail.html -O ${AUTO_OUTPUT}/${output_folder_path}/cl_detail.html
        wget -c ${FILESERVER}unmergeable.txt -O ${AUTO_OUTPUT}/${output_folder_path}/unmergeable.txt
        wget -c ${FILESERVER}multiMergeable.txt -O ${AUTO_OUTPUT}/${output_folder_path}/multiMergeable.txt
        wget -c ${FILESERVER}make_64bit_abi_feature.log -O ${AUTO_OUTPUT}/${output_folder_path}/make_64bit_abi_feature.log
        wget -c ${FILESERVER}make_x86_64_abi_feature.log -O ${AUTO_OUTPUT}/${output_folder_path}/make_x86_64_abi_feature.log
        HOURLY_CHANGE_IDS="$(cat ${AUTO_OUTPUT}/${output_folder_path}/changeid.txt)"
    fi

    # check patchset test result
    if [ "$PATCHSET_IDS" != "NULL" ]; then
        echo "Exe command: python ${AUTO_SCRIPT}/Test_passrate.py ${AUTO_REPORT}/report.html $PATCHSET_IDS $BUILD_NUMBER"
        auto_run_result=`python ${AUTO_SCRIPT}/Test_passrate.py ${AUTO_REPORT}/report.html "$PATCHSET_IDS" "$BUILD_NUMBER"`
        echo "auto_run_result: $auto_run_result"
        if [ $auto_run_result !=  "" ]; then
            #auto_run_result1=`echo $str | cut -d ':' -f 2`
            auto_run_result1=`echo $auto_run_result | cut -d ':' -f 2 | sed s/%$//`
            echo "Pass rate is: $auto_run_result1"

            if [ $(echo "$auto_run_result1 < 90.00" | bc) -eq 1 ]; then
                echo "[FAIL] Auto test Pass Ratio: ${auto_run_result1}%. Test board: ${TEST_BOARD_TYPE}. Test report:${result_url}/report.html, Test logs:${result_url}/jenkins.txt" > $AUTO_REVIEW_INFO
                bash ${AUTO_SCRIPT}/add_comment4patchset.sh ${AUTO_BIN} ${AUTO_REVIEW_INFO} "${PATCHSET_IDS}"
            else
                echo "[PASS] Auto test Pass Ratio: ${auto_run_result1}%. Test board: ${TEST_BOARD_TYPE}. Test report:${result_url}/report.html, Test logs:${result_url}/jenkins.txt" > $AUTO_REVIEW_INFO
                bash ${AUTO_SCRIPT}/add_comment4patchset.sh ${AUTO_BIN} "${AUTO_REVIEW_INFO}" "${PATCHSET_IDS}"
            fi
        else
            echo "[FAIL] Auto test fail, test report not exist. Test board: ${TEST_BOARD_TYPE}" > $AUTO_REVIEW_INFO
            bash ${AUTO_SCRIPT}/add_comment4patchset.sh ${AUTO_BIN} ${AUTO_REVIEW_INFO} "${PATCHSET_IDS}"
        fi
    elif [ ! -z "${HOURLY_CHANGE_IDS}" ]; then
        # hourly change id is not null
        echo "Exe command: python ${AUTO_SCRIPT}/Test_passrate.py ${AUTO_REPORT}/report.html ${HOURLY_CHANGE_IDS} ${BUILD_NUMBER}"
        python ${AUTO_SCRIPT}/Test_passrate.py ${AUTO_REPORT}/report.html "${HOURLY_CHANGE_IDS}" ${BUILD_NUMBER}
    else
        # Not patch set build test. it's daily/ci test. this will record test build number to log.
        echo "Exe command: python ${AUTO_SCRIPT}/Test_passrate.py ${AUTO_REPORT}/report.html NA $BUILD_NUMBER"
        python ${AUTO_SCRIPT}/Test_passrate.py ${AUTO_REPORT}/report.html NA "$BUILD_NUMBER"
    fi
fi
!
#==============================================================================================

