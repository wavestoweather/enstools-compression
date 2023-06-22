#!/bin/bash
set -e

function usage {
  echo "arguments:"
  echo "-w    warnings are errors"
  exit 1
}

# parse the command line
excluded_files=""
extra_arguments=""
while getopts "w" opt; do
  case $opt in
  w)
    echo "WARNING: warnings are treated like errors for debugging."
    extra_arguments="-W error"
    ;;
  *)
    usage
    ;;
  esac
done
if [[ ! -z $excluded_files ]]; then
  ignore_option="--ignore=$excluded_files"
fi

# create a virtual environment and install all dependencies
if [[ ! -d venv ]]; then
  python3 -m venv --prompt enstools-compression venv
  source venv/bin/activate
  pip install -U pip
  pip install -e .[test]
fi

source venv/bin/activate
pytest ${extra_arguments} ${ignore_option}
