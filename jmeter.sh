#!/usr/bin/env bash

set -x;
set -e;

N=$1
CP=$2
TEST=$3
DURATION=$4
THREADS=$5

function usage {
	echo "Usage: $0 n CP test duration threads"
	exit 1
}

if [ "${N}" -eq 100 ] ; then
    JVM_ARGS="-XX:+UnlockCommercialFeatures -XX:+FlightRecorder -XX:FlightRecorderOptions=defaultrecording=true,dumponexit=true"
fi

mkdir -p ${N}
cd ${N}
rm -f *
JVM_ARGS="${JVM_ARGS}" jmeter -Duser.classpath=${CP} -n -t ${TEST} -Jduration=${DURATION} -Jthreads=${THREADS}
