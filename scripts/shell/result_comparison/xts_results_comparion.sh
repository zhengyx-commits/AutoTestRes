#!/bin/bash

base_file=$1 #initial test file :Check if there are files with new error items

target_file=$2  # Test result file for comparison

base_version_xml=$3

target_version_xml=$4

base_file_test_category=` sed -n "2"p < $base_file  | cut -d '"' -f 12 `
target_file_test_category=` sed -n "2"p < $target_file  | cut -d '"' -f 12 `

func_result_comparison(){

        initial_document=$1
        target_document=$2
        comparison_file=$3
        count__base_line=` wc -l < $initial_document `

        second_fiter_file=second_fiter.txt

        for (( i=1 ; i <= $count__base_line ; i=i+1 ))
        do
          data=` sed -n "$i"p < $initial_document `
          #echo "data : $data"
          let n=$i+1
          next_line_data=` sed -n "$n"p < $initial_document `
          if [[ $data =~ "Module name" ]];then
            if [[ $next_line_data =~ "Module name" ]];then
              continue
            fi
            pass_number=` echo $data | cut -d '"' -f 10 `
            total_tests_number=` echo $data | cut -d '"' -f 12 `
            if [[ $total_tests_number != $pass_number ]];then
              echo $data >> $second_fiter_file
            fi
          elif [[ $data =~ "TestCase name" ]];then
            echo "  $data" >> $second_fiter_file
          elif [[ $data =~ "Test result" ]];then
            testcase_name=` echo $data | cut -d '"' -f 4 `
            fiter_data=` grep -F -c "$testcase_name" $target_document `
            #echo "fiter data : $fiter_data"
            if [[ $fiter_data -ne '0' ]];then
              continue
            else
              echo "      $data" >> $second_fiter_file
            fi

          fi
        done

        #new_test_error_item=$comparison_file
        count__base_line=` wc -l < $second_fiter_file `
        for (( i=1 ; i <= $count__base_line ; i=i+1 ))
        do
          data=` sed -n "$i"p < $second_fiter_file `
          #echo "data : $data"
          let n=$i+1
          next_line_data=` sed -n "$n"p < $second_fiter_file `
          if [[ $data =~ "Module name" ]];then
            if [[ $next_line_data =~ "Module name" ]];then
              continue
            elif [[ $i == $count__base_line ]];then
              continue
            else
              echo $data >> $comparison_file
            fi
          elif [[ $data =~ "TestCase name" ]];then
            echo "  $data" >> $comparison_file
          elif [[ $data =~ "Test result" ]];then
            echo "      $data" >> $comparison_file
          fi

        done

        rm $second_fiter_file

}


func_check_if_incomplete(){

  base_result=$1
  target_result=$2

  grep -E 'done="false"' $base_result > base_result_incompete_module.txt
  grep -E 'done="false"' $target_result > target_result_incompete_module.txt

  count_base_result=` wc -l < base_result_incompete_module.txt `
  for (( i=1 ; i <= $count_base_result ; i=i+1 ))
  do
    data=` sed -n "$i"p < base_result_incompete_module.txt `
    moudle_name=` echo $data | cut -d '"' -f 2  `
    #echo "data : $data"
    fiter_data=` grep -F -c "$moudle_name" target_result_incompete_module.txt `
    #echo "fiter data : $fiter_data"
    if [[ $fiter_data -ne '0' ]];then
        continue
    else
        echo "      $data" >> incompete_module.txt
    fi
  done
  rm base_result_incompete_module.txt target_result_incompete_module.txt
}


if [[ $base_file_test_category -ne $target_file_test_category  ]];then

        echo "base file test category is $base_file_test_category , target file test category is $target_file_test_category"
        echo "The test category of test results is inconsistent, please check again"
        exit 1

fi

base_first_fiter_file=first_fiter.txt
cat $base_file | grep -E '"fail"|Module name' > $base_first_fiter_file

target_fiter_file=target_first_fiter.txt
cat $target_file | grep -E '"fail"|Module name' > $target_fiter_file

new_error_items=new_error_items.txt
func_result_comparison $base_first_fiter_file $target_fiter_file $new_error_items

#resolved_fail_items=resolved_fail_items.txt
#func_result_comparison $target_fiter_file $base_first_fiter_file $resolved_fail_items

rm $base_first_fiter_file $target_fiter_file

func_check_if_incomplete $base_file $target_file

if [[ $base_version_xml != "" && $target_version_xml != "" ]];then

  source filter_commit.sh $base_version_xml $target_version_xml

  # echo " source generate_html_file.sh $new_error_items $resolved_fail_items $base_file $target_file $base_version_xml $target_version_xml  "
  source generate_html_file.sh $new_error_items $base_file $target_file $base_version_xml $target_version_xml

else

  source generate_html_file.sh $new_error_items $base_file $target_file

fi

sleep 5

remove_list=('new_error_items.txt' 'deleted_directory.xml' 'filter.xml' 'new_directory.xml' 'incompete_module.txt')

for remove_file in ${remove_list[@]}
do

    if [[ -e $remove_file  ]];then

        rm $remove_file

    fi

done

