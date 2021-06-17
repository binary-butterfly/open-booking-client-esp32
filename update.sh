#!/bin/bash

# ensure /app folder
PORT=${1:-"/dev/ttyUSB0"}
if ! ampy -p $PORT ls | grep -q '/app'; then
  echo "would create folder"
fi

# copy all files
#ampy -p $PORT put boot.py boot.py
for file in app/*.py; do
  if [ "$file" == "app/config_dist.py" ]; then
    continue
  fi
  ampy -p $PORT put $file $file
done
