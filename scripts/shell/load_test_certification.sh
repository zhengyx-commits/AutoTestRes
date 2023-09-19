#!/bin/bash
function usage() {
    echo "Usage: $0 -b [Current Build number] \
    -d [ADB_SN] \
    -f [Project_series] \
    -i [BUILD_INFO] \
    -j [Upgrade_IMG_tool] \
    -m [Manual_Test_Image_URL] \
    -n [Build_Number] \
    -o [DUT_Baudrate] \
    -p [Project] \
    -q [Test_job_url] \
    -r [PowerRelay_Serial_Port] \
    -s [DUT_Serial_Port] \
    -u [TestPlanName] \
    -v [userdebug|engine] \
    -y [work_powerRelay_dir] \
    -w [Jenkins_Workspace] \
    [-h help]"
    exit 1
}
while getopts ":b:d:f:i:j:m:n:o:p:q:r:s:u:v:y:w:h" opt
do
    case $opt in
        b)
    echo "argument: $opt $OPTARG"
    BUILD_NUMBER=$OPTARG
    ;;
        d)
    echo "argument: $opt $OPTARG"
    DUT_ADB_SN=$OPTARG
    ;;
        f)
    echo "argument: $opt $OPTARG"
    PROJECT_SERIES=$OPTARG
    ;;
        i)
    echo "argument: $opt $OPTARG"
    BUILD_INFO=$OPTARG
    ;;
        j)
    echo "argument: $opt $OPTARG"
    UPDATE_TOOL=$OPTARG
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
        y)
    echo "argument: $opt $OPTARG"
    work_powerRelay_dir=$OPTARG
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
echo "TEST_BOARD_TYPE:$TEST_BOARD_TYPE"
echo "TEST_VARIANT_TYPE:$TEST_VARIANT_TYPE"
echo "TEST_BUILD_NUMBER:$Test_BUILD_NUMBER"
cd $work_powerRelay_dir
if [ ! -e ~/.autoTestflashImage.lock ]; then
    touch ~/.autoTestflashImage.lock
fi
echo "Manual_Test_Image_URL:$Test_Image_URL"
BUILD_JOB_URL=${TEST_JOB_URL}${BUILD_NUMBER}
echo "Current Test Job URL: ${BUILD_JOB_URL}"
# Defined DUT ADB SN INFO
ADB_SN=$DUT_ADB_SN
ADB_SN_OPTION="-s $DUT_ADB_SN"
FASTBOOT_SN=$DUT_ADB_SN
FASTBOOT_SN_OPTION="-s $DUT_ADB_SN"
AUTO_SCRIPT=${WORKSPACE}/AutoTestRes/scripts/shell/
AUTO_REPORT=${WORKSPACE}/AutoTestRes/report
AUTO_BIN=${WORKSPACE}/AutoTestRes/bin
AUTO_LOG=${WORKSPACE}/AutoTestRes/log
AUTO_TMP=${WORKSPACE}/AutoTestRes/tmp
AUTO_IMAGE=${work_powerRelay_dir}/auto_image
AUTO_OUTPUT=${WORKSPACE}/AutoTestRes/output
AUTO_DEVICECHK=${WORKSPACE}/AutoTestRes/scripts/python/tools/device_check

DOWNLOAD_PATH=${work_powerRelay_dir}/Temp_Image
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

TODAY_MDATE=`date "+%Y-%m-%d"`
TODAY_MDATE1=`date "+%Y%m%d"`

YESTERDAY_MDATE=`date "+%Y-%m-%d" -d "-22hour"`
YESTERDAY_MDATE1=`date "+%Y%m%d" -d "-22hour"`
is_skip_boot_partition=no
function func_rebootDutByRelayDelayTime() {
    ${AUTO_BIN}/powerRelay $PowerRelay_Serial_Port all off
    sleep 3
    ${AUTO_BIN}/powerRelay $PowerRelay_Serial_Port all on
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
    else
        echo -e " --- Download file: $URL\nDownloading ..."
        wget -q -c $URL -O ${DOWNLOAD_PATH}/aml_upgrade_package.img
    fi
    if [[ $URL =~ "signed_image" ]]; then
        cp ${DOWNLOAD_PATH}/aml_upgrade_package_signed.img ${AUTO_IMAGE}/aml_upgrade_package.img
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
function func_killRebootLoggingThread() {
    ps -ef | grep reboot_logging | grep ${DUT_Serial_Port} | grep -v grep | awk '{print $2}' | xargs kill -9
    #echo "Check reboot_logging after kill thread start"
    ps -ef | grep reboot_logging | grep -v grep # check reboot_logging thread kill or not
    #echo "Check reboot_logging after kill thread end"
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
function func_checkManualBuild() {
    func_checkUrlStatus $1;
    if [ $? -ne 0 ]; then
        echo " --- Manual Test image is not available, Error code: HTTP 404"
        return 1
    else
        return 0
    fi
}
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
            BUILD_INFO=$(echo $FILESERVER | awk -F '/' '{ i=1; while(i<=NF) {if( $i ~ /[A-Za-z].+-.+-.+-.+-.+-/) print $i; i++} }')
            echo " Zip Build information: $BUILD_INFO"
            IMGE_URL=$FILESERVER
            func_downloadFastbootFile $FILESERVER;
            echo " --- --- func_downloadFastbootFile: done"
        elif [[ $FILESERVER =~ '.tgz' ]]; then
            BUILD_INFO=$(echo $FILESERVER | awk -F '/' '{ i=1; while(i<=NF) {if( $i ~ /[A-Za-z].+-.+-.+-.+-.+-/) print $i; i++} }')
            echo " tgz Build information: $BUILD_INFO"
            IMGE_URL=$FILESERVER
            func_downloadFastboottgzFile $FILESERVER;
            echo " --- --- func_downloadFastboot tgz File: done"
        else
            if [[ $PROJECT_SERIES =~ "Android_U" || $PROJECT_SERIES =~ "Android_S" ]]; then
                echo " --- --- Android_S / Android_U Build information:"
                BUILD_INFO=$(echo $FILESERVER | awk -F '/' '{ i=1; while(i<=NF) {if( $i ~ /[A-Za-z].+-.+-.+-.+-.+-/) print $i; i++} }')
                DATE_STR=$(echo $FILESERVER | awk -F '/' '{ i=1; while(i<=NF) {if( $i ~ /^[0-9]+-/) print $i; i++} }')
                AUTO_BUILD_NUMBER=$(echo $FILESERVER | awk -F'-' '{split($NF,a,"/"); print a[1]}')
                MDATE1=$(echo $DATE_STR | tr -cd "[0-9]")
                if [[ $PROJECT_SERIES =~ "Android_U" ]]; then
                    URL=${FILESERVER}aml_upgrade_signed_img-${MDATE1}-${AUTO_BUILD_NUMBER}.tar.bz2
                else
                    URL=${FILESERVER}aml_upgrade_img-${MDATE1}-${AUTO_BUILD_NUMBER}.tar.bz2
                fi
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
    fi
fi
if [[ $PROJECT_SERIES =~ "Android_S" || $PROJECT_SERIES =~ "Android_U" ]]; then
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
    if [[ $UPDATE_TOOL =~ "fastboot" ]];then
        echo " --- Start to upgrade with fastboot"
        cp ../scripts/shell/flash-all.sh ./
        bash flash-all.sh ${DUT_ADB_SN}
    elif [[ $UPDATE_TOOL =~ "adnl" ]];then
        echo " --- Start to upgrade with adnl"
        if [[ $is_skip_boot_partition = "yes" ]]; then
            echo "upgrade_image.sh:(1)$WORKSPACE (2)$DUT_Serial_Port (3)${DUT_SERIAL_PORT_BAUDRATE} (4)$PowerRelay_Serial_Port (5)${AUTO_IMAGE}/aml_upgrade_package.img (6)false (7)${UPDATE_TOOL} "
            flock -x ~/.autoTestflashImage.lock \
            -c "bash ${WORKSPACE}/AutoTestRes/scripts/shell/upgrade_image.sh \
            $WORKSPACE \
            $DUT_Serial_Port \
            ${DUT_SERIAL_PORT_BAUDRATE} \
            $PowerRelay_Serial_Port \
            ${AUTO_IMAGE}/aml_upgrade_package.img \
            false \
            ${UPDATE_TOOL}"
        else
            echo "upgrade_image.sh:(1)$WORKSPACE (2)$DUT_Serial_Port (3)${DUT_SERIAL_PORT_BAUDRATE} (4)$PowerRelay_Serial_Port (5)${AUTO_IMAGE}/aml_upgrade_package.img (6)true (7)${UPDATE_TOOL}"
            flock -x ~/.autoTestflashImage.lock \
            -c "bash ${WORKSPACE}/AutoTestRes/scripts/shell/upgrade_image.sh \
            $WORKSPACE \
            $DUT_Serial_Port \
            ${DUT_SERIAL_PORT_BAUDRATE} \
            $PowerRelay_Serial_Port \
            ${AUTO_IMAGE}/aml_upgrade_package.img \
            true \
            ${UPDATE_TOOL}"
        fi
    else
        echo "Burning mode not currently supported,exit test!"
        exit 1
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
    if [[ $PROJECT_SERIES =~ "Boreal" ]]; then
        sleep 180
    else
        func_rebootDutByRelayDelayTime 180;
    fi
fi
echo "The upgrade is successful, restart and wait for 10 seconds"
sleep 10
echo " ---  --- Check DUT adb port status after download image."
echo "adb devices SN: $ADB_SN"
func_checkAdbStatus;
dutStatus=$?
if [ $dutStatus -ne 0 ]; then
    func_updateReportFile "FailReason" "DUT boot up fail after upgrade test image";
    func_preTestFailSaveLogs;
    func_killRebootLoggingThread;
    echo "====================  SERIAL PORT LOG START ========================"
    exit 1
fi
echo " ---  --- Check DUT adb port status after download image"
if [[ $TEST_PLAN_NAME =~ "STS" ]]; then
    adb $ADB_SN_OPTION root
    sleep 2
fi
cd ${WORKSPACE}
exit 0
