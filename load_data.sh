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

# Create the tables in Phoenix.
echo "Creating tables in Phoenix"
psql.py ${ZOOKEEPER} ddl/CreateTables.sql

# Bulk load the tables.

# Variables we need.
HADOOP_COMPAT=$(ls hbase-hadoop-compat*.jar)
HADOOP2_COMPAT=$(ls hbase-hadoop-compat*.jar)
export LIBJARS=$HADOOP_COMPAT,$HADOOP2_COMPAT

# XXX: This needs to get fixed!
export HADOOP_CLASSPATH=/etc/hbase/conf:/usr/hdp/2.2.0.0-854/hbase/lib/hbase-protocol.jar

TABLES="store_sales"
for t in $TABLES; do
	echo "Loading $t"
	hdfs dfs -ls ${DIR}/${SCALE}/${t} > /dev/null
	if [ $? -ne 0 ]; then
		echo "$t data is not generated"
		exit 1
	fi
	UCT=`echo $t | tr '[:lower:]' '[:upper:]'`
	INPUT=${DIR}/${SCALE}/${t}/${t}
	hadoop jar phoenix-4.2.0-client.jar \
		org.apache.phoenix.mapreduce.CsvBulkLoadTool \
		-libjars ${LIBJARS} \
		--table ${UCT} \
		--input ${INPUT} \
		--zookeeper=${ZOOKEEPER} \
		-g \
		-d '|'
done

# Load date dimension. Needed a special hack to work around date requiring time.
hadoop fs -copyFromLocal data/date_dim.txt /tmp
hadoop jar phoenix-4.2.0-client.jar \
	org.apache.phoenix.mapreduce.CsvBulkLoadTool \
	-libjars ${LIBJARS} \
	--table DATE_DIM \
	--input /tmp/date_dim.txt \
	--zookeeper=${ZOOKEEPER} \
	-g \
	-d '|'
