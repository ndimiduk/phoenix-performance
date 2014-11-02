#!/bin/sh

# Use the TPC-DS data generator to generate delimited data. We don't use the full schema, just a few tables.

function usage {
	echo "Usage: generate_data.sh scale_factor [temp_directory]"
	exit 1
}

function runcommand {
	if [ "X$DEBUG_SCRIPT" != "X" ]; then
		$1
	else
		$1 2>/dev/null
	fi
}

SCALE=$1
DIR=$2
if [ X"$SCALE" = "X" ]; then
	usage
fi
if [ X"$DIR" = "X" ]; then
	DIR=/tmp/phoenix-generate
fi

# Check for all the stuff I need to function.
for f in gcc javac; do
	which $f > /dev/null 2>&1
	if [ $? -ne 0 ]; then
		echo "Required program $f is missing. Please install or fix your path and try again."
		exit 1
	fi
done

# Check if Maven is installed and install it if not.
which mvn > /dev/null 2>&1
if [ $? -ne 0 ]; then
	SKIP=0
	if [ -e "apache-maven-3.0.5-bin.tar.gz" ]; then
		SIZE=`du -b apache-maven-3.0.5-bin.tar.gz | cut -f 1`
		if [ $SIZE -eq 5144659 ]; then
			SKIP=1
		fi
	fi
	if [ $SKIP -ne 1 ]; then
		echo "Maven not found, automatically installing it."
		curl -O http://www.us.apache.org/dist/maven/maven-3/3.0.5/binaries/apache-maven-3.0.5-bin.tar.gz 2> /dev/null
		if [ $? -ne 0 ]; then
			echo "Failed to download Maven, check Internet connectivity and try again."
			exit 1
		fi
	fi
	tar -zxf apache-maven-3.0.5-bin.tar.gz > /dev/null
	CWD=$(pwd)
	export MAVEN_HOME="$CWD/apache-maven-3.0.5"
	export PATH=$PATH:$MAVEN_HOME/bin
fi

echo "Building TPC-DS Data Generator"
(cd tpcds-gen; make)
echo "TPC-DS Data Generator built, generating data"

hdfs dfs -mkdir -p ${DIR}
hdfs dfs -ls ${DIR}/${SCALE}/store_sales > /dev/null
if [ $? -ne 0 ]; then
	echo "Generating store sales data at scale factor $SCALE."
	(cd tpcds-gen; hadoop jar target/*.jar -d ${DIR}/${SCALE}/store_sales -s ${SCALE} -t store_sales)
fi
hdfs dfs -ls ${DIR}/${SCALE}/date_dim > /dev/null
if [ $? -ne 0 ]; then
	echo "Generating date dim data."
	(cd tpcds-gen; hadoop jar target/*.jar -d ${DIR}/${SCALE}/date_dim -s ${SCALE} -t date_dim)
fi
hdfs dfs -ls ${DIR}/${SCALE}/store_sales > /dev/null
if [ $? -ne 0 ]; then
	echo "Data generation failed, exiting."
	exit 1
fi
echo "Data generation complete."
