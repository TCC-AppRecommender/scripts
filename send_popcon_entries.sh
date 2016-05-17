FOLDER=$1
SELF_FOLDER=`pwd`


for popcon_file in "$SELF_FOLDER"/*popcon
do
  dir_name=$(basename "$popcon_file")
  dir_name=${dir_name:0:2}
  dir_name=$FOLDER$dir_name

  rm -rf $dir_name
  mkdir $dir_name
  cp $popcon_file $dir_name
done
