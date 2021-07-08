#!/bin/bash

# ensure /app folder
PORT=${1:-"/dev/ttyUSB0"}
if ! ampy -p $PORT ls | grep -q '/app'; then
  echo "create folder"
  ampy -p $PORT mkdir /app
fi

# copy all files
echo "put file boot.py"
ampy -p $PORT put boot.py boot.py
for file in app/*.py; do
  if [ "$file" == "app/config_dist.py" ]; then
    continue
  fi
  echo "put file $file"
  ampy -p $PORT put $file $file
done
