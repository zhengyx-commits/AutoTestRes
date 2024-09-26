latest=""
latest_time=0
for file in ` ls $1 `
  do
     if [ ! -d $1"/"$file ];then
         a=`stat -c %Y $1"/"$file`
         if [  $latest_time -lt  $a  ];then
         	latest=$file
		latest_time=$a
	 fi
     fi
  done
echo $latest
