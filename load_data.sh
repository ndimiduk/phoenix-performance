#!/bin/sh

# Use the Phoenix bulk loader to load data.
# Data needs to have been generated using generate_data.sh prior to this step.

PSQL=/usr/hdp/current/phoenix-client/bin/psql.py

CLIENT=/usr/hdp/current/phoenix-client/phoenix-client.jar

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
${PSQL} ${ZOOKEEPER} ddl/CreateTables.sql

# Pre-split STORE_SALES 128 ways.
echo "Pre-splitting STORE_SALES"

# Ensure the table does not keep deleted records.
cat ddl/disableKeepDeleted | hbase shell

# Load some data so we can split the table.
${PSQL} -t STORE_SALES ${ZOOKEEPER} ddl/50kRecords.csv

# Run the split and balancer
cat ddl/presplit | hbase shell

# Delete the data we added
${PSQL} -t STORE_SALES ${ZOOKEEPER} ddl/DeleteFromStoreSales.sql

# Run a major compaction
cat ddl/majorCompactStoreSales | hbase shell

# Bulk load the tables.
HADOOP_COMPAT=/usr/hdp/current/hbase-client/lib/hbase-hadoop-compat.jar
HADOOP2_COMPAT=/usr/hdp/current/hbase-client/lib/hbase-hadoop2-compat.jar
export LIBJARS=$HADOOP_COMPAT,$HADOOP2_COMPAT
export HADOOP_CLASSPATH=/etc/hbase/conf:/usr/hdp/current/hbase-client/lib/hbase-protocol.jar

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
	hadoop jar ${CLIENT} \
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
hadoop jar ${CLIENT} \
	org.apache.phoenix.mapreduce.CsvBulkLoadTool \
	-libjars ${LIBJARS} \
	--table DATE_DIM \
	--input /tmp/date_dim.txt \
	--zookeeper=${ZOOKEEPER} \
	-g \
	-d '|'
