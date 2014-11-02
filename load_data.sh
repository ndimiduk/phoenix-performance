#!/bin/sh

# Use the Phoenix bulk loader to load data.
# Data needs to have been generated using generate_data.sh prior to this step.

function usage {
	echo "Usage: load_data.sh scale_factor zk [temp_directory]"
	echo "Ex: load_data.sh 10 sandbox.hortonworks.com:2181:/hbase-unsecure"
	exit 1
}

SCALE=$1
ZOOKEEPER=$2
DIR=$3
if [ X"$SCALE" = "X" ]; then
	usage
fi
if [ X"$ZOOKEEPER" = "X" ]; then
	usage
fi
if [ X"$DIR" = "X" ]; then
	DIR=/tmp/phoenix-generate
fi

# Check for the data I need.
hdfs dfs -ls ${DIR}/${SCALE}/store_sales > /dev/null
if [ $? -ne 0 ]; then
	echo "Store Sales data is not generated"
	exit 1
fi
hdfs dfs -ls ${DIR}/${SCALE}/date_dim > /dev/null
if [ $? -ne 0 ]; then
	echo "Date data is not generated"
	exit 1
fi

# Run the bulk load for Store Sales.
set -x
echo "Loading STORE_SALES"
INPUT=${DIR}/${SCALE}/store_sales/store_sales/data-m-00001

#hadoop jar phoenix*client.jar \
#	org.apache.phoenix.mapreduce.CsvBulkLoadTool \
#	-libjars ${LIBJARS} \
#	--table STORE_SALES \
#	--input ${INPUT} \
#	-d '|' \
#	--zookeeper=${ZOOKEEPER}

export LIBJARS=hbase-hadoop-compat*.jar,hbase-hadoop2-compat*.jar
hadoop jar phoenix*client.jar \
	org.apache.phoenix.mapreduce.CsvBulkLoadTool \
	--table STORE_SALES \
	--input ${INPUT} \
	-d '|' \
	--zookeeper=${ZOOKEEPER}


