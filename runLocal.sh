#!/usr/bin/env bash

set -x;
set -e;

DRIVER=$1
DURATION=$2
MACHINES=$3
PROCS=$4
THREADS=$5

function usage {
	echo "Usage: $0 phx|hs2 duration numMachines numProcs numThreads"
	exit 1
}

if [ X"$DURATION" = "X" ]; then
	usage
fi
if [ X"$MACHINES" = "X" ]; then
	usage
fi
if [ X"$PROCS" = "X" ]; then
    usage
fi
if [ X"$THREADS" = "X" ]; then
    usage
fi

if [ "$MACHINES" -ne "1" ] ; then
    echo "only 1 machine supported."
    exit 1
fi

JVM_ARGS="-XX:+UnlockCommercialFeatures -XX:+FlightRecorder -XX:StartFlightRecording=defaultrecording=true,dumponexit=true,compress=true"

HIVE_HOME=/Users/ndimiduk/phx_perf/apache-hive-1.2.0-SNAPSHOT-bin

PHX_TEST=../jmeter_tests/Point_NoJoin_NoGroup_Pri1_phx.jmx
HS2_TEST=../jmeter_tests/Point_NoJoin_NoGroup_Pri1_hive.jmx

PHX_CP=../phoenix-4.2.2-client.jar
HS2_CP=/usr/local/Cellar/hadoop/2.6.0/libexec/share/hadoop/common/hadoop-common-2.6.0.jar:${HIVE_HOME}/lib/hive-jdbc-1.2.0-SNAPSHOT-standalone.jar

TEST="X"
CP="X"

if [ "$DRIVER" = "phx" ] ; then
    TEST=$PHX_TEST
    CP=$PHX_CP
elif [ "$DRIVER" = "hs2" ] ; then
    TEST=$HS2_TEST
    CP=$HS2_CP
else
    echo "unrecognized driver $DRIVER"
    usage
fi

seq ${PROCS} | parallel -j${PROCS} -n0 ./jmeter.sh {#} ${CP} ${TEST} ${DURATION} ${THREADS}
~/phx_perf/pyenv/bin/python runner/analyze.py > "analysis_${DRIVER}_D${DURATION}xM${MACHINES}xP${PROCS}xT${THREADS}.log"
seq ${PROCS} | parallel -n0 rm -r {#}
