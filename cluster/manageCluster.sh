#!/bin/bash

usage() {
    cat <<EOF
Usage: $0 [options]

Arguments:
  -c up | stop | rm | ps , --command up | stop | rm | ps
  (Required) Command to be run against the cluster.
EOF
}

# handy logging and error handling functions
log() { printf '%s\n' "$*"; }
error() { log "ERROR: $*" >&2; }
fatal() { error "$*"; exit 1; }
usage_fatal() { error "$*"; usage >&2; exit 1; }

#Default values
CLUSTER_NAME="myCluster"
# FORCE_REMOVE=false

while [ "$#" -gt 0 ]; do
    arg=$1
    case $1 in
        # convert "--opt=the value" to --opt "the value".
        # the quotes around the equals sign is to work around a
        # bug in emacs' syntax parsing
        --*'='*) shift; set -- "${arg%%=*}" "${arg#*=}" "$@"; continue;;
        -c|--command) shift; ACTION=$1;;
        -h|--help) usage; exit 0;;
        -v|--verbose) VERBOSE='-v';;
        -*) usage_fatal "unknown option: '$1'";;
        *) break;; # reached the list of file names
    esac
    shift || usage_fatal "option '${arg}' requires a value"
done
# Check if a required option was not set
if [[ -z $ACTION ]] ; then
  usage_fatal "Values for the following options are required: --action"
fi

logIfVerbose() {
  if [ ! -z $VERBOSE ]; then
    log $1
  fi
}
function checkrc {
        if [[ $1 -ne 0 ]]; then
                fatal "Last command exited with rc $1, exiting."
        fi
}

CLUSTER_ENV_NAME=mycluster.env
set -a
source $CLUSTER_ENV_NAME

if [[ $ACTION = "up" ]]; then
  logIfVerbose "docker-compose up -d  --scale workers=$SCALE_WORKERS"
  docker-compose up -d --scale workers=$SCALE_WORKERS
  checkrc $?
fi

if [[ $ACTION = "stop" ]]; then
  logIfVerbose "docker-compose stop "
  docker-compose stop
  checkrc $?
fi

if [[ $ACTION = "rm" ]]; then
  logIfVerbose "docker-compose rm"
  docker-compose rm
  checkrc $?
fi

if [[ $ACTION = "ps" ]]; then
  logIfVerbose "docker-compose ps"
  docker-compose ps
  checkrc $?
fi