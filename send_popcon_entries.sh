if [ "$#" -ne  2 ]; then
    echo "Usage $0 [actual_submissions_folder] [destiny_submissions_folder]"
    exit 1
fi
if ! [ -e "$1" ]; then
    echo "$1 not found"
    echo ""
    echo "Usage $0 [actual_submissions_folder] [destiny_submissions_folder]"
    exit 1
fi
if ! [ -d "$1" ]; then
    echo "$1 not a directory"
    echo ""
    echo "Usage $0 [actual_submissions_folder] [destiny_submissions_folder]"
    exit 1
fi
if ! [ -e "$2" ]; then
    echo "$2 not found"
    echo ""
    echo "Usage $0 [actual_submissions_folder] [destiny_submissions_folder]"
    exit 1
fi
if ! [ -d "$2" ]; then
    echo "$2 not a directory"
    echo ""
    echo "Usage $0 [actual_submissions_folder] [destiny_submissions_folder]"
    exit 1
fi

ACTUAL_SUBMISSIONS_FOLDER=$1
DESTINY_SUBMISSIONS_FOLDER=$2

for popcon_file in "$ACTUAL_SUBMISSIONS_FOLDER"/*popcon
do
  dir_name=$(basename "$popcon_file")
  dir_name=${dir_name:0:2}
  dir_name=$DESTINY_SUBMISSIONS_FOLDER$dir_name

  if [ ! -d "$dir_name" ]; then
    mkdir $dir_name
  fi

  cp $popcon_file $dir_name
done
