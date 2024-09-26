#!/bin/bash

XTS=$1
TARGET_PATH=$2

if [ ! -d "last_report" ]; then
    mkdir last_report
fi

latest_folder=$(ls -td "$TARGET_PATH"/* | grep -v '\.zip$' | head -1)

if [ -f "$latest_folder/test_result_failures_suite.html" ]; then
    cp "$latest_folder/test_result_failures_suite.html" last_report/index.html
    cp_exit_code=$?
    if [[ $cp_exit_code -eq 0 ]]; then
    	# sed -i "s/<th colspan=\"2\">Summary<\/th>/<th colspan=\"2\">${XTS} Summary<\/th>/" last_report/index.html
    	sed -i "s/<title>.*<\/title>/<title>${XTS} Test Report<\/title>/" last_report/index.html
    	echo "Last report has copied to /last_report/"
	failed_tests=$(grep -oP '(?<=<td class="rowtitle">Tests Failed</td><td>)\d+' last_report/index.html)
	if [[ -z "$failed_tests" ]]; then
	    echo "No 'Tests Failed' number found in the report"
	else
	    echo "Number of failed tests: $failed_tests"
            export FAILED_TESTS=$failed_tests
	fi
    else
	echo "Copy file failed"
    fi
else
    echo "Last report not found"
fi

