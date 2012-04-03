#!/bin/bash

PWD=`pwd`
export PYTHONPATH=$PWD/eggs:$PWD/stager/trunk/lib
export PATH=$PATH:$PWD/eggs
export STAGER_TEST=$HOME/destroy
export STAGER_CONF=$HOME/stager_test/stager/trunk/conf
export SSH_KEY_FILE=$HOME/.ssh/identity
export REMOTE_USERNAME=$USER
export LOG_DIR=$HOME/stager_test/stager/trunk/log

