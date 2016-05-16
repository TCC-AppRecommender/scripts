FOLDER=$1

cd $FOLDER

for tar_file in "$FOLDER"/*
do
  tar xvf $tar_file
  rm $tar_file
done
