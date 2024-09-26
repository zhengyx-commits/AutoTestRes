#!/bin/bash
echo "begin to watch the update of $2 while $1 exists"
while [ -e $1 ]
do
    timestamp=`date +%s`
    filetimestamp=`stat -c %Y $2`
    timecha=$[$timestamp - $filetimestamp]
    time_now=`date +%Y-%m-%d,%H:%M:%S` 
    #echo $time_now >> wifi.txt
    #echo =============AMLS905Y4AP222248 >> wifi.txt
    #adb -s AMLS905Y4AP222248 shell cmd wifi status >> wifi.txt
    #echo =============ohm0000000036 >> wifi.txt
    #adb -s ohm0000000036 shell cmd wifi status >> wifi.txt
    #echo =============ohm0000000032 >> wifi.txt
    #adb -s ohm0000000032 shell cmd wifi status >> wifi.txt
    #echo =============ohm0000000033 >> wifi.txt
    #adb -s ohm0000000033 shell cmd wifi status >> wifi.txt
    #echo =============ohm0000000034 >> wifi.txt
    #adb -s ohm0000000034 shell cmd wifi status >> wifi.txt
    #echo =============ap2228019621984101029 >> wifi.txt
    #adb -s ap2228019621984101029 shell cmd wifi status >> wifi.txt
    if [[ $timecha -gt 5100 ]];then
        echo "reboot didn't make log begin to update, please check the log to analyze the problem"
    elif [[ $timecha -gt 3600 ]];then
        echo "timecha:${timecha}"
        echo "the log has stopped updating for more than 1800s, begin to reboot"    
        $WORKSPACE/AutoTestRes/bin/powerRelay /dev/powerRelay1 all off
        $WORKSPACE/AutoTestRes/bin/powerRelay /dev/powerRelay2 all off
        $WORKSPACE/AutoTestRes/bin/powerRelay /dev/powerRelay3 all off
        sleep 15
        $WORKSPACE/AutoTestRes/bin/powerRelay /dev/powerRelay1 all on
        $WORKSPACE/AutoTestRes/bin/powerRelay /dev/powerRelay2 all on
        $WORKSPACE/AutoTestRes/bin/powerRelay /dev/powerRelay3 all on
    fi
    sleep 300
done
echo "watch finished!"
