#!/bin/bash

usage() {
    cat <<EOF
Usage: $0 [options]

Arguments:
  -cn <val>, --clusterName <val>, -cn<val>
    (Optional) Cluster Name. Default is myCluster

  -s, --scaleWorkers
    (Optional) Number of workers to be instantiated in the cluster. Default is 3
EOF
}

# handy logging and error handling functions
log() { printf '%s\n' "$*"; }
error() { log "ERROR: $*" >&2; }
fatal() { error "$*"; exit 1; }
usage_fatal() { error "$*"; usage >&2; exit 1; }

#Default values
CLUSTER_NAME="myCluster"
SCALE_WORKERS=3

while [ "$#" -gt 0 ]; do
    arg=$1
    case $1 in
        # convert "--opt=the value" to --opt "the value".
        # the quotes around the equals sign is to work around a
        # bug in emacs' syntax parsing
        --*'='*) shift; set -- "${arg%%=*}" "${arg#*=}" "$@"; continue;;
        -s|--scaleWorkers) shift; SCALE_WORKERS=$1;;
        -cn|--clusterName) shift; CLUSTER_NAME=$1;;
        -h|--help) usage; exit 0;;
        -v|--verbose) VERBOSE='-v';;
        -*) usage_fatal "unknown option: '$1'";;
        *) break;; # reached the list of file names
    esac
    shift || usage_fatal "option '${arg}' requires a value"
done

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

logIfVerbose "Saving environment variables to $CLUSTER_ENV_NAME "
echo "#" > $CLUSTER_ENV_NAME
echo "# DO NOT MODIFY THIS FILE DIRECTLY" >> $CLUSTER_ENV_NAME
echo "#" >> $CLUSTER_ENV_NAME
echo "COMPOSE_PROJECT_NAME=$CLUSTER_NAME" >> $CLUSTER_ENV_NAME
checkrc $?
echo "SCALE_WORKERS=$SCALE_WORKERS"  >> $CLUSTER_ENV_NAME
checkrc $?

set -a
source $CLUSTER_ENV_NAME
logIfVerbose "docker-compose up --scale worker=$SCALE_WORKERS -d"
docker-compose up --scale worker=$SCALE_WORKERS -d
checkrc $?
