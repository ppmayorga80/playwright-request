#!/usr/bin/env bash

CWD=$(dirname "$0")
INPUT=$(realpath "$CWD/../.bumpversion.cfg")
grep "current_version" "$INPUT" | awk -F'=' '{print $2}' | xargs
