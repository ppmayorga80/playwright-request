#!/usr/bin/env bash

echo "             _            _   "
echo " _ __  _   _| |_ ___  ___| |_ "
echo "| '_ \| | | | __/ _ \/ __| __|"
echo "| |_) | |_| | ||  __/\__ \ |_ "
echo "| .__/ \__, |\__\___||___/\__|"
echo "|_|    |___/                  "

export PYTHONPATH="$PWD/src"

#1. set the test coverage value and other shell variables
COVERAGE_THRESHOLD="100"
PROJECT_DIR="src"
TEST_DIR="tests"

COV_DIR="${PROJECT_DIR}/$*"
PROCESS_TEST_DIR_OR_FILE="${TEST_DIR}/$*"

if [[ -f "${PROCESS_TEST_DIR_OR_FILE}" ]]; then
  COV_DIR=${PROJECT_DIR}/$(dirname "$@")
fi

pytest \
  --disable-warnings \
  --cov-report term-missing:skip-covered \
  --cov-fail-under=${COVERAGE_THRESHOLD} \
  --cov=${COV_DIR} \
  "${PROCESS_TEST_DIR_OR_FILE}/"