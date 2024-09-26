#!/bin/sh

new_xml=$1
old_xml=$2

count_line=` wc -l < $new_xml `

for (( i=3 ; i < $count_line ; i=i+1 ))
do

    New_data=` sed -n "$i"p < $new_xml `
    if [[ *"$New_data"* =~ "revision" ]] && [[ *"$New_data"* =~ "name" ]];then
        if [[ *"$New_data"* =~ "path" ]];then
            New_path=$( echo $New_data | sed 's/^.*path=\"//g' | sed 's/\".*$//g' )
			grep_path="path=\"$New_path"\"
        else
            New_path=$( echo $New_data | sed 's/^.*name=\"//g' | sed 's/\".*$//g' )
			grep_path="name=\"$New_path"\"
        fi
	
	New_revision=$( echo $New_data | sed 's/^.*revision=\"//g' | sed 's/\".*$//g' )
	#	echo " New_path : $New_path --> $New_revision "
	
	Old_revision=` grep $grep_path $old_xml | sed 's/^.*revision=\"//g' | sed 's/\".*$//g' `
	#	echo " Old_path : $grep_path --> $Old_revision "
	# Filter out new directories
	if [[ $Old_revision == "" ]];then
		#echo " New_path : $New_revision "
		echo "$New_path $New_revision" >> new_directory.xml
		# Filter out commit records (Commit ID)
	elif [[ $Old_revision != $New_revision ]];then
		#echo " $New_path : $Old_revision --> $New_revision "
		echo "$New_path $Old_revision $New_revision " >> filter.xml
	fi
	fi

done

# Filter out deleted directories
count_line=` wc -l < $old_xml `
for (( i=3 ; i < $count_line ; i=i+1 ))
do

    data=` sed -n "$i"p < $old_xml `
    if [[ *"$data"* =~ "revision" ]] && [[ *"$data"* =~ "name" ]];then
        if [[ *"$data"* =~ "path" ]];then
		path=$( echo $data | sed 's/^.*path=\"//g' | sed 's/\".*$//g' )
		grep_path="path=\"$path"\"
        else
		path=$( echo $data | sed 's/^.*name=\"//g' | sed 's/\".*$//g' )
		grep_path="name=\"$path"\"
		fi
    
	#echo " path : $path "
		
	if_path_in_new_xml=` grep $grep_path $new_xml `
		# Filter out new directories
	if [[ $if_path_in_new_xml == "" ]];then
	#	echo " deleted_directory : $path "
		echo "$path" >> deleted_directory.xml
    fi
	fi
done


