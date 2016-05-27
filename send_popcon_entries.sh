FOLDER=$1
SELF_FOLDER=`pwd`

mkdir -p $FOLDER
for popcon_file in "$SELF_FOLDER"/*popcon
do
  cp $popcon_file $FOLDER
done
