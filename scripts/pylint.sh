#!/bin/bash

echo "             _ _       _     "
echo " _ __  _   _| (_)_ __ | |_   "
echo "| '_ \| | | | | | '_ \| __|  "
echo "| |_) | |_| | | | | | | |_   "
echo "| .__/ \__, |_|_|_| |_|\__|  "
echo "|_|    |___/                 "

export PYTHONPATH="$PWD/src"

THRESHOLD="10.0"
PROJECT_DIR="src/"
TEST_DIR="tests/"

pylint \
  --fail-under=${THRESHOLD} \
  --recursive=y \
  --docstring-min-length 10 \
  ${PROJECT_DIR} ${TEST_DIR}

ERROR_CODE=$?
if [[ ${ERROR_CODE} != 0 ]]; then
  echo "pylint doesn't pass, ERROR_CODE=${ERROR_CODE}" >&2
  exit ${ERROR_CODE}
fi
