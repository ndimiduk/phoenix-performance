#!/bin/sh

# Check for all the stuff I need to function.
for f in pdsh pdcp; do
	which $f > /dev/null 2>&1
	if [ $? -ne 0 ]; then
		echo "Required program $f is missing. Please install or fix your path and try again."
		exit 1
	fi
done

echo "Setting up JMeter"
LOCATION=https://archive.apache.org/dist/jmeter/binaries
VERSION=2.11
FILE=apache-jmeter-$VERSION.tgz

SKIP=0
if [ -e $FILE ]; then
	SIZE=`du -b $FILE | cut -f 1`
	if [ $SIZE -eq 29489945 ]; then
		SKIP=1
	fi
fi
if [ $SKIP -ne 1 ]; then
	echo "Downloading JMeter"
	curl -O $LOCATION/$FILE 2> /dev/null
	if [ $? -ne 0 ]; then
		echo "Failed to download JMeter, check Internet connectivity and try again."
		exit 1
	fi
fi

# Copy to our test machines.
echo "Deploying JMeter to all hosts specified in testshosts"
pdcp -w ^testhosts $FILE /tmp
pdsh -w ^testhosts "cd /tmp; tar -xzf $FILE"
pdcp -w ^testhosts phoenix*client.jar /tmp/apache-jmeter-*/lib
