if [ "$#" -ne  1 ]; then
    echo "Usage $0 [folder_with_targz]"
    exit 1
fi
if ! [ -e "$1" ]; then
    echo "$1 not found"
    echo ""
    echo "Usage $0 [folder_with_targz]"
    exit 1
fi
if ! [ -d "$1" ]; then
    echo "$1 not a directory"
    echo ""
    echo "Usage $0 [folder_with_targz]"
    exit 1
fi

FOLDER=$1

cd $FOLDER

for tar_file in "$FOLDER"/*
do
  tar xvf $tar_file
  rm $tar_file
done
