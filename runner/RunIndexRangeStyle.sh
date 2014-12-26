#!/bin/sh

mydir="$(dirname "$0")"
source $mydir/ClusterProfile.sh

# Sanity checking.
if [ X"$1" = "X" ]; then
	echo "Usage: $0 [JMX Path]"
	exit 1
fi
if [ ! -f $1 ]; then
	echo "$1 does not exist"
	exit 1
fi

CARBONARG=""
if [ X"$CARBON" != "X" ]; then
	CARBONARG="-c $CARBON"
fi

# Semi point lookups.
python runTest.py $CARBONARG \
	-i $1 \
	-v VAR_REQUESTS_PER_THREAD=500 \
	-v VAR_NUM_THREADS=4 \
	-v VAR_RAMP_TIME=1 \
	-v VAR_POOL_MAX=4 \
	-v VAR_ZOOKEEPER_QUORUM=${ZOOKEEPER_ENDPOINT}
