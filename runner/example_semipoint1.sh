#!/bin/sh

# Semi point lookups.
python runTest.py \
	-i ../jmeter_tests/Phoenix_StoreSales_Semipoint1.jmx \
	-v VAR_REQUESTS_PER_THREAD=1500 \
	-v VAR_NUM_THREADS=4 \
	-v VAR_RAMP_TIME=1 \
	-v VAR_POOL_MAX=4 \
	-v VAR_ZOOKEEPER_QUORUM=cluster1:2181:/hbase-unsecure
