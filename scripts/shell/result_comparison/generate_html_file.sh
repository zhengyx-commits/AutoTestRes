#!/bin/bash

new_fail_test_xml=$1

base_result=$2

target_result=$3

base_version_xml=$4

target_version_xml=$5


if [[ -e $new_fail_test_xml ]];then

        new_fail_module_number=` grep -c "Module name"  $new_fail_test_xml `

        new_fail_number=` grep -c '"fail"'  $new_fail_test_xml `

        new_assumption_number=` grep -c "ASSUMPTION_FAILURE"  $new_fail_test_xml `

        let new_case_number=$new_fail_number+$new_assumption_number

else

        new_fail_module_number=0

        new_case_number=0

fi

#if [[ -e $resolved_fail_items ]];then
#
#        fix_module_number=` grep -c "Module name"  $resolved_fail_items `
#
#        fix_fail_number=` grep -c '"fail"'  $resolved_fail_items `
#
#        fix_assumption_number=` grep -c "ASSUMPTION_FAILURE"  $resolved_fail_items `
#
#        let fix_case_number=$fix_fail_number+$fix_assumption_number
#
#else
#
#        fix_module_number=0
#
#        fix_case_number=0
#
#fi

if [[ -e incompete_module.txt ]];then

    incompete_module_number=` wc -l < incompete_module.txt `
else

    incompete_module_number=0

fi

Base_result_file_date_month_day=` sed -n "2"p < $base_result | cut -d '"' -f 6 | cut -d ' ' -f 2-3  `
Base_result_file_date_year=` sed -n "2"p < $base_result | cut -d '"' -f 6 | cut -d ' ' -f 6 `
target_result_file_date_month_day=` sed -n "2"p < $target_result | cut -d '"' -f 6 | cut -d ' ' -f 2-3  `
target_result_file_date_year=` sed -n "2"p < $target_result | cut -d '"' -f 6 | cut -d ' ' -f 6  `
base_file_test_category=` sed -n "2"p < $base_result  | cut -d '"' -f 12 `
target_file_test_category=` sed -n "2"p < $target_result  | cut -d '"' -f 12 `

if [[ $base_file_test_category -ne $target_file_test_category  ]];then

        echo "base file test category is $base_file_test_category , target file test category is $target_file_test_category"
        echo "The test category of test results is inconsistent, please check again"
        exit 1

fi


base_result_name=${base_result##*/}
target_result_name=${target_result##*/}

test_date=` date +%Y.%m.%d-%H.%M.%S `

test_html=Test_Result_Comparison_$test_date.html
export LAST_COMPARISON=$test_html

echo "
<html>
  <body>
  <div>
  <table align='center' style='background-color:#F5DEB3' cellpadding = "5" cellspacing = "10" width="60%">
    <tr style='background-color:#F5DEB3' ><td colspan = 3 align='center'>Test Report Comparison Summary</td></tr>
    <tr style='background-color:#F5DEB3'><td colspan = "3">Base result file : $Base_result_file_date_year $Base_result_file_date_month_day $base_file_test_category $base_result_name</td></tr>
    <tr style='background-color:#F5DEB3'><td colspan = "3">Target result file : $target_result_file_date_year $target_result_file_date_month_day $target_file_test_category $target_result_name</td></tr>
    <tr style='background-color:#F0FFF0'><td>New Tests Failed Modules</td><td align='center'>$new_fail_module_number</td></tr>
    <tr style='background-color:#F0FFF0'><td>New Tests Failed Cases</td><td align='center'>$new_case_number</td></tr>
    <tr style='background-color:#F0FFF0'><td>New Incompete Module</td><td align='center'>$incompete_module_number</td></tr>
  </table>
  </div>
  <br>">> $test_html

if [[ -e incompete_module.txt ]];then
  echo "
  <div>
  <table border='1' align='center' width="95%">
    <tr style='background-color:#F0E68C' ><td colspan = 3 align='center'>New Incompete Module</td></tr>" >> $test_html
  count_for_incompete_module=` wc -l < incompete_module.txt `

  for (( i=1 ; i <= $count_for_incompete_module ; i=i+1 ))
  do
    module_name=` sed -n "$i"p < incompete_module.txt | cut -d '"' -f 2 `
    echo "
    <tr style='background-color:#EEE8AA' ><td align='center'>$module_name</td></tr>" >> $test_html

  done
  echo "
  </table>
  </div>
  <br>" >> $test_html

fi

#echo "resolved_fail_items : $resolved_fail_items"

#if [[ -e $resolved_fail_items ]];then

#        func_html $resolved_fail_items $base_result 'flase' 'fix' $test_html

#fi

func_html(){

        test_xml=$1
        base_result=$2
        is_fail_data=$3
        html_summary=$4
        test_html=$5
        if [[ $html_summary =~ "fix" ]];then
                module_color='#F0E68C'
                case_color='#EEE8AA'
                echo "
  <div>
  <table border='1' align='center' width="95%">
    <tr style='background-color:$module_color' ><td colspan = 3 align='center'>Fixed Cases Details</td></tr>" >> $test_html
        elif [[ $html_summary =~ "fail" ]];then
                module_color='#CD853F'
                case_color='#D2B48C'
                echo "
  <div>
  <table border='1' align='center' width="95%">
    <tr style='background-color:$module_color' ><td colspan = 3 align='center'>New Tests Failed Cases Details</td></tr>" >> $test_html

        fi

        txt_line=` wc -l < $test_xml `


        for (( i=1 ; i <= $txt_line ; i=i+1 ))
        do
          data=` sed -n "$i"p < $test_xml `
          if [[ $data =~ "Module name" ]];then
            module_name=` echo $data | cut -d '"' -f 2 `
            module_abi=` echo $data | cut -d '"' -f 4 `
            echo "
    <tr style='background-color:$module_color'><td colspan = '3' id='$module_name'>Tests Module name: $module_abi $module_name</td></tr>
    <tr style='background-color:$module_color'><td>Testcases Name </td><td align='center'>Result</td><td>Details</td></tr>" >> $test_html
          elif [[ $data =~ "Test result" ]];then
            test_result=` echo $data | cut -d '"' -f 2 `
            test_name=` echo $data | cut -d '"' -f 4 `
            #echo "test_name : $test_name"
            if [[ $is_fail_data =~ "true" ]];then
              test_name_str="\"$test_name"\"
              data_result_line=` grep -n -F "$test_name_str" $base_result | grep "$test_result" | head -n 1 | cut -d ':' -f 1 `
              #echo "data_result_line : $data_result_line"
              next_result_line=$[ data_result_line +2 ]
              next_result_data=` sed -n "$next_result_line"p < $base_result `
              details=` echo $next_result_data | cut -d '>' -f 2 `
              echo "
    <tr style='background-color:$case_color'><td>$test_name</td><td align='center'>$test_result</td><td>$details</td></tr>" >> $test_html
            else
              echo "
    <tr style='background-color:$case_color'><td>$test_name</td><td align='center'>pass</td><td>    </td></tr>" >> $test_html
            fi
          fi
        done
        echo "
  </table>
  </div>
  <br>
  </body>" >> $test_html
}


if [[ -e $new_fail_test_xml ]];then
        grep -E 'Module name'  $new_fail_test_xml > module.txt
        module_line=` wc -l < module.txt `

        echo "
  <div>
  <table border='1' align='center' width=95%>
    <tr style='background-color:#F0E68C' ><td colspan = 3 align='center'>New Tests Failed Modules lists</td></tr>
    <tr style='background-color:#F0E68C' ><td>Modules Name </td></tr>" >> $test_html
   for (( i=1 ; i <= $module_line ; i=i+1 ))
   do
     data=` sed -n "$i"p < module.txt `
     module_name=` echo $data | cut -d '"' -f 2 `
     module_abi=` echo $data | cut -d '"' -f 4 `
     echo "
    <tr style='background-color:#F0E68C'><td><a href='#$module_name'>$module_abi $module_name</td></tr>" >> $test_html
   done
   echo "
  </table>
  </div>
  <br>" >> $test_html
  func_html $new_fail_test_xml $base_result 'true' 'fail' $test_html
  rm module.txt

fi


if [[ $base_version_xml != "" && $target_version_xml != "" ]];then

   if [[ -e new_directory.xml ]];then

     new_directory_number=` wc -l < new_directory.xml `

   else

     new_directory_number=0

   fi

    if [[ -e deleted_directory.xml ]];then

      deleted_directory_number=` wc -l < deleted_directory.xml `

    else

      deleted_directory_number=0

    fi

    if [[ -e filter.xml ]];then

      modified_directories_number=` wc -l < filter.xml `

    else

      modified_directories_number=0

    fi
  base_version_build_vendor_fingerprint=` grep 'invocation-id' $base_result | sed 's/ /\n/g' | grep 'build_vendor_fingerprint' | cut -d '"' -f 2  `
  target_version_build_vendor_fingerprint=` grep 'invocation-id' $target_result | sed 's/ /\n/g' | grep 'build_vendor_fingerprint' | cut -d '"' -f 2  `

echo "

  <body>
  <div>
  <table align='center' style='background-color:#F5DEB3' cellpadding = "5" cellspacing = "10" width="60%">
    <tr style='background-color:#F5DEB3' ><td colspan = 3 align='center'>Beta Version Comparison Summary</td></tr>
    <tr style='background-color:#F5DEB3'><td colspan = "3">Base version xml : $base_version_build_vendor_fingerprint build-manifest.xml </td></tr>
    <tr style='background-color:#F5DEB3'><td colspan = "3">Target version xml : $target_version_build_vendor_fingerprint build-manifest.xml </td></tr>
    <tr style='background-color:#F5F5DC'><td>New Directory Number</td><td align='center'>$new_directory_number</td></tr>
    <tr style='background-color:#F5F5DC'><td>Deleted Directory Number</td><td align='center'>$deleted_directory_number</td></tr>
    <tr style='background-color:#F0FFF0'><td>Modified Directories Number</td><td align='center'>$modified_directories_number</td></tr>
  </table>
  </div>
  <br>
  </body>" >> $test_html

   if [[ -e new_directory.xml ]];then

      xml_line=` wc -l < new_directory.xml `
     echo "
  <div>
  <table border='1' align='center' width="95%">
    <tr style='background-color:$module_color' ><td colspan = 3 align='center'>New Directories Details</td></tr>
    <tr style='background-color:#D2B48C'><td>New Directories Path</td><td>$base_version_xml</td></tr>" >> $test_html
     for (( i=1 ; i <= $xml_line ; i=i+1 ))
     do
       path=` sed -n "$i"p < new_directory.xml | awk '{print $1}' `
       commit_id=` sed -n "$i"p < new_directory.xml | awk '{print $2}' `
       echo "
   <tr style='background-color:$case_color'><td>$path</td><td>$commit_id</td></tr>" >> $test_html
      done
     echo "
 </div>
   <br>" >> $test_html
   fi

   if [[ -e deleted_directory.xml ]];then

     xml_line=` wc -l < deleted_directory.xml  `
     echo "
  <div>
  <table border='1' align='center' width="95%">
    <tr style='background-color:$module_color' ><td colspan = 3 align='center'>Deleted Directories Details</td></tr>
    <tr style='background-color:#D2B48C'><td>Deleted Directories Path</td></tr>" >> $test_html
    for (( i=1 ; i <= $xml_line ; i=i+1 ))
    do
      path=` sed -n "$i"p < deleted_directory.xml | awk '{print $1}' `
      echo "
    <tr style='background-color:$case_color'><td>$path</td></tr>" >> $test_html
    done
    echo "
  </div>
  <br>" >> $test_html
  fi

  if [[ -e filter.xml ]];then

    xml_line=` wc -l < filter.xml  `
    echo "
  <div>
  <table border='1' align='center' width="95%">
    <tr style='background-color:$module_color' ><td colspan = 3 align='center'>Modified Directories Details</td></tr>
    <tr style='background-color:#D2B48C'><td>Modified Directories Path</td><td>Commit for $target_version_xml</td><td>Commit for $base_version_xml</td></tr>" >> $test_html
    for (( i=1 ; i <= $xml_line ; i=i+1 ))
    do
      path=` sed -n "$i"p < filter.xml | awk '{print $1}' `
      target_commit_id=` sed -n "$i"p < filter.xml | awk '{print $2}' `
      base_commit_id=` sed -n "$i"p < filter.xml | awk '{print $3}' `
      echo "
    <tr style='background-color:$case_color'><td>$path</td><td>$target_commit_id</td><td>$base_commit_id</td></tr>" >> $test_html
    done
    echo "
  </div>
  <br>" >> $test_html
  fi
fi


echo "
</html>">> $test_html
