#!/bin/bash
WORKSPACE=$1
DUT_Serial_Port=$2
DUT_Serial_Port_Daudrate=$3
PowerRelay_Serial_Port=$4
Image_File_Name=$5
Skip_Boot_Partition=$6
UPDATE_TYPE=$7

if [[ ${UPDATE_TYPE} =~ 'update' ]]; then
    UPDATE_TOOL='update'
else
    UPDATE_TOOL='adnl'
fi

function func_checkUpgradeDutStatus() {
    # Get update error info:
    update_image_log=$(cat ${WORKSPACE}/AutoTestRes/bin/update/upgradeDutStatuslLog.txt)
    echo "========== Check upgrade status log start =========="
    echo ${update_image_log}
    echo "========== Check upgrade status log en ============="

    if [[ ! ${update_image_log} =~ "Upgrade image successful" ]]; then
        echo "Upgrade image fail, try again."
        ps -ef | grep reboot_logging | grep ${DUT_Serial_Port} | grep -v grep | awk '{print $2}' | xargs kill -9
        ps -ef | grep reboot_logging | grep -v grep
        echo "=================PRE-TEST SERIAL LOG START================="
        cat $WORKSPACE/AutoTestRes/log/pretest.txt
        echo "=================PRE-TEST SERIAL LOG END================="
        : > ${WORKSPACE}/AutoTestRes/log/pretest.txt # clear log  file
        : > ${WORKSPACE}/AutoTestRes/bin/update/upgradeDutStatuslLog.txt

        start_time=`date +%Y/%m/%d-%H:%M:%S`
        echo "Log started at: ${start_time}"
        echo "Log started at: ${start_time}" >> ${WORKSPACE}/AutoTestRes/bin/update/upgradeDutStatuslLog.txt

        ${WORKSPACE}/AutoTestRes/bin/reboot_logging -s ${DUT_Serial_Port} -b ${DUT_Serial_Port_Daudrate} -t 900 &

        ${WORKSPACE}/AutoTestRes/bin/setDutInUpdateMode ${DUT_Serial_Port} \
        ${DUT_Serial_Port_Daudrate} \
        ${PowerRelay_Serial_Port} \
        ${WORKSPACE}/AutoTestRes \
        ${UPDATE_TOOL}

        return 1
    else
        ps -ef | grep reboot_logging | grep ${DUT_Serial_Port} | grep -v grep | awk '{print $2}' | xargs kill -9
        ps -ef | grep reboot_logging | grep -v grep
        return 0
    fi
}

# restore reboot logging, and save the file to $WORKSPACE/AutoTestRes/log/pretest.txt
${WORKSPACE}/AutoTestRes/bin/reboot_logging -s ${DUT_Serial_Port} -b ${DUT_Serial_Port_Daudrate} -t 900 &

: > ${WORKSPACE}/AutoTestRes/bin/update/upgradeDutStatuslLog.txt
start_time=`date +%Y/%m/%d-%H:%M:%S`
echo "Log started at: ${start_time}"
echo "Log started at: ${start_time}" >> ${WORKSPACE}/AutoTestRes/bin/update/upgradeDutStatuslLog.txt

echo "${WORKSPACE}/AutoTestRes/bin/setDutInUpdateMode ${DUT_Serial_Port} \
${DUT_Serial_Port_Daudrate} \
${PowerRelay_Serial_Port} \
${WORKSPACE}/AutoTestRes \
${UPDATE_TOOL}"

${WORKSPACE}/AutoTestRes/bin/setDutInUpdateMode ${DUT_Serial_Port} \
${DUT_Serial_Port_Daudrate} \
${PowerRelay_Serial_Port} \
${WORKSPACE}/AutoTestRes \
${UPDATE_TOOL}

if [[ ${UPDATE_TOOL} =~ 'adnl' ]]; then
    echo Linux2017|sudo -S ${WORKSPACE}/AutoTestRes/bin/update/adnl devices
else
    echo Linux2017|sudo -S sudo ${WORKSPACE}/AutoTestRes/bin/update/update scan
    sleep 3
    echo Linux2017|sudo -S sudo ${WORKSPACE}/AutoTestRes/bin/update/update identify
    sleep 3
    echo Linux2017|sudo -S sudo ${WORKSPACE}/AutoTestRes/bin/update/update scan
fi

case "$WORKSPACE" in
    *_CTS*|*_GTS*|*_TVTS*|*_VTS*|*_STS*|*_NTS*)
    if [ ! -f ${Image_File_Name} ]; then
        echo "Test image file not found @ ${Image_File_Name}" >> ${WORKSPACE}/AutoTestRes/bin/update/upgradeDutStatuslLog.txt
        exit 0
    fi
    ;;
    *)
    if [ ! -f ${WORKSPACE}/AutoTestRes/image/${Image_File_Name} ]; then
        echo "Test image file not found @ ${WORKSPACE}/AutoTestRes/image/${Image_File_Name}" >> ${WORKSPACE}/AutoTestRes/bin/update/upgradeDutStatuslLog.txt
        exit 0
    fi
    ;;
esac

i=1
while [ $i -lt 4 ]
do
    echo "================>>>START: The $i times upgrade image"

    if [[ ${UPDATE_TOOL} =~ 'adnl' ]]; then
        if [[ ! -z $(lsusb | grep 1b8e:c004) ]]; then
            if [[ $WORKSPACE =~ (_CTS|_VTS|_GTS|_TVTS|_NTS|_STS) ]]; then
                echo "${WORKSPACE}/AutoTestRes/bin/update/adnl_burn_pkg -p ${Image_File_Name}"
                echo Linux2017|sudo -S ${WORKSPACE}/AutoTestRes/bin/update/adnl_burn_pkg -p ${Image_File_Name} -r 1 | tee -a ${WORKSPACE}/AutoTestRes/bin/update/tmpUpgradeLog.txt
            else
                echo "${WORKSPACE}/AutoTestRes/bin/update/adnl_burn_pkg -p ${WORKSPACE}/AutoTestRes/image/${Image_File_Name}"
                if [[ ${WORKSPACE} =~ "Nagratnocs" ]]; then
                    echo Linux2017|sudo -S ${WORKSPACE}/AutoTestRes/bin/update/adnl_burn_pkg -b 0 -p ${WORKSPACE}/AutoTestRes/image/${Image_File_Name} -r 1 | tee -a ${WORKSPACE}/AutoTestRes/bin/update/tmpUpgradeLog.txt
                else
                    echo Linux2017|sudo -S ${WORKSPACE}/AutoTestRes/bin/update/adnl_burn_pkg -p ${WORKSPACE}/AutoTestRes/image/${Image_File_Name} -r 1 | tee -a ${WORKSPACE}/AutoTestRes/bin/update/tmpUpgradeLog.txt
                fi
            fi
            adnl_burnning_log=$(cat ${WORKSPACE}/AutoTestRes/bin/update/tmpUpgradeLog.txt)
            if [[ ${adnl_burnning_log} =~ 'burn successful^_^' ]]; then
                echo "Upgrade image successful" >> ${WORKSPACE}/AutoTestRes/bin/update/upgradeDutStatuslLog.txt
                rm ${WORKSPACE}/AutoTestRes/bin/update/tmpUpgradeLog.txt
                break
            fi
        else
            echo "INFO: Debug is not avaliable!"
        fi
        rm ${WORKSPACE}/AutoTestRes/bin/update/tmpUpgradeLog.txt
    else
        if [[ ${UPDATE_TYPE} =~ 'android_k' || ${UPDATE_TYPE} =~ 'iptv' ]]; then
            echo "bash ${WORKSPACE}/AutoTestRes/bin/update/aml_update_whole_package_android_k.bash ${WORKSPACE}/AutoTestRes/image/${Image_File_Name} ${Skip_Boot_Partition} dev00 auto"
            echo Linux2017|sudo -S bash ${WORKSPACE}/AutoTestRes/bin/update/aml_update_whole_package_android_k.bash ${WORKSPACE}/AutoTestRes/image/${Image_File_Name} ${Skip_Boot_Partition} dev00 auto | tee -a ${WORKSPACE}/AutoTestRes/bin/update/tmpUpgradeLog.txt
        else
            echo "bash ${WORKSPACE}/AutoTestRes/bin/update/aml_update_whole_package.bash ${WORKSPACE}/AutoTestRes/image/${Image_File_Name} ${Skip_Boot_Partition} dev00 auto"
            echo Linux2017|sudo -S bash ${WORKSPACE}/AutoTestRes/bin/update/aml_update_whole_package.bash ${WORKSPACE}/AutoTestRes/image/${Image_File_Name} ${Skip_Boot_Partition} dev00 auto | tee -a ${WORKSPACE}/AutoTestRes/bin/update/tmpUpgradeLog.txt
        fi

        update_burnning_log=$(cat ${WORKSPACE}/AutoTestRes/bin/update/tmpUpgradeLog.txt)
        if [[ ${update_burnning_log} =~ 'programming successful^_^' ]]; then
            echo "Upgrade image successful" >> ${WORKSPACE}/AutoTestRes/bin/update/upgradeDutStatuslLog.txt
            rm ${WORKSPACE}/AutoTestRes/bin/update/tmpUpgradeLog.txt
            break
        fi
        rm ${WORKSPACE}/AutoTestRes/bin/update/tmpUpgradeLog.txt
        echo "================>>>END: The $i times burnnig image"
    fi

    func_checkUpgradeDutStatus;
    try_again=$?
    if [ ${try_again} -ne 1 ]; then
        break
    fi
    i=$[$i+1]

done
