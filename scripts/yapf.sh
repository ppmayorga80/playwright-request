#!/bin/bash

echo "                    __  "
echo " _   _  __ _ _ __  / _| "
echo "| | | |/ _' | '_ \| |_  "
echo "| |_| | (_| | |_) |  _| "
echo " \__, |\__,_| .__/|_|   "
echo " |___/      |_|         "
echo "                        "

if [[ "$*" == *"--apply"* ]]; then
  echo "#Apply yapf recursively"
  yapf -ir src tests
else
  echo "#Test yapf recursively"
  yapf -r --diff src tests
  if [[ $? == 0 ]]; then
    echo "yapf: code formatting is OK!"
  fi
fi