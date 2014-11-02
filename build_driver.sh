# Build the Phoenix client driver, including applying patches
# to make it compatible with JMeter.

BRANCH=4.2

# Check for all the stuff I need to function.
for f in javac; do
	which $f > /dev/null 2>&1
	if [ $? -ne 0 ]; then
		echo "Required program $f is missing. Please install or fix your path and try again."
		exit 1
	fi
done

# Grab Maven if we don't have it.
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

# Download Phoenix source and switch to a known branch.
echo "Downloading Phoenix source code"
rm -rf phoenix
git clone https://github.com/apache/phoenix 2> /dev/null
( cd phoenix && git checkout -b $BRANCH remotes/origin/$BRANCH > /dev/null )

# Apply patches.
FILE=jmeter-patch-$BRANCH
if [ -f patches/$FILE ]; then
	echo "Applying JMeter compatibility patches"
	(cd phoenix && patch -p0 < ../patches/$FILE)
fi

# Build.
echo "Building Phoenix Client"
(cd phoenix && mvn package -DskipTests -Dhadoop.profile=2 > /dev/null)

# Bring the client JAR into the top level directory.
cp phoenix/phoenix-assembly/target/phoenix*client.jar .
echo "Driver built and copied to base directory."
