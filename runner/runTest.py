#!/usr/bin/python

import getopt
import os
import re
import signal
import subprocess
import sys
import time

DEBUG = 1
TESTHOSTS    = "../clienthosts"
CLUSTERHOSTS = "../clusterhosts"

def fullShutdown(rsp, cp):
	for p in [rsp, cp]:
		try:
			p.terminate()
			sleep(0.25)
			p.kill()
		except:
			pass

def runCommand(command, error, background=False):
	if DEBUG:
		print command
	if background:
		ret = subprocess.Popen(command, shell=True)
		return ret
	else:
		ret = os.system(command)
		if ret != 0:
			assert False, error
		return ret

def runJmeter():
	# See if JMeter is properly deployed everywhere.
	testJmeter = 'pdsh -S -w ^' + TESTHOSTS + ' "test -e /tmp/phoenix-performance/apache-jmeter*/lib/phoenix*.jar"'
	runCommand(testJmeter, "JMeter is not properly deployed on all nodes")

	# Clean up prior runs.
	cleanupJmeter = 'pdsh -S -w ^' + TESTHOSTS + ' "rm -f jmeter.log output.csv output.xml root.log"'
	runCommand(cleanupJmeter, "Cleanup failed")
	cleanupLocal = 'rm -f output.csv.* output.xml.*'
	runCommand(cleanupLocal, "Cleanup failed")

	# Deploy the temp JMX on all nodes.
	distJmx = "pdcp -w ^" + TESTHOSTS + " temp.jmx /tmp/temp.jmx"
	runCommand(distJmx, "Failed to deploy JMeter spec")

	# Run JMeter on all nodes.
	runJmeter = 'pdsh -S -w ^' + TESTHOSTS + ' "/tmp/phoenix-performance/apache-jmeter*/bin/jmeter -n -t /tmp/temp.jmx"'
	p = runCommand(runJmeter, "JMeter execution failed", background=True)
	return p

def gatherClientStats():
	# Clean up the last run.
	cleanupLocal = 'rm -f sar.txt'
	runCommand(cleanupLocal, "Cleanup failed")

	# Start close to a 5s boundary.
	sometime = (int(time.time() / 5) * 5) + 5 - time.time()
	time.sleep(sometime)

	# Launch the command.
	sarCommand = "sar -d -n DEV -u -q -r -S 5 > sar.txt"
	sarCommand = 'pdsh -w ^' + CLUSTERHOSTS + ' ' + sarCommand
	p = runCommand(sarCommand, "Failed to run sar", background=True)
	return p

def gatherRegionServerStats(hmaster):
	# Clean up the last run.
	cleanupLocal = 'rm -f RegionServerStats.csv'
	runCommand(cleanupLocal, "Cleanup failed")

	gatherScript = 'python hbaseStats.py -m %s > RegionServerStats.csv' % hmaster
	p = runCommand(gatherScript, "Failed to execute hbase stat gatherer", background=True)
	return p

def analyzeOutput(carbon):
	# Bring the various output files local.
	bringFiles = 'rpdcp -w ^' + TESTHOSTS + ' output.* .'
	runCommand(bringFiles, "Failed to retrieve JMeter results")

	# Run the analysis.
	analyze = "python analyze.py"
	if carbon:
		analyze = "%s -c %s" % (analyze, carbon)
	runCommand(analyze, "Analyze command failed")

def main():
	try:
		opts, args = getopt.getopt(sys.argv[1:], "c:i:m:t:v:", ["help", "output="])
	except getopt.GetoptError as err:
		print str(err)
		sys.exit(2)
	input = None
	output = "output.csv"
	hmaster = None
	carbon = None
	variables = []
	for o, a in opts:
		if o == "-i":
			input = a
		elif o == "-c":
			carbon = a
		elif o == "-m":
			hmaster = a
		elif o == "-t":
			TESTHOSTS = a
		elif o == "-v":
			variables.append(a.split("="))
		else:
			assert False, "unhandled option"

	if input == None:
		assert False, "Need an input file (-i)"
	if hmaster == None:
		assert False, "Need an hmaster endpoint (-m)"

	# Replace the parameters in the JMX file.
	fd = open(input)
	jmx = fd.read()
	for vars in variables:
		var = vars[0]
		if jmx.find(var) == -1:
			assert False, "Undefined varible " + var
		jmx = jmx.replace(var, vars[1])

	# Error out if we have any VARs that were not replaced.
	m = re.search('(VAR_[A-Z_]+)', jmx)
	if m:
		varname = m.group(0)
		assert False, "Variable " + varname + " was not substituted (use -v) in " + input
	output = open("temp.jmx", "w")
	output.write(jmx)
	output.close()

	# Run the JMeter test.
	jp = runJmeter()

	# Gather stats while the test runs.
	rsp = gatherRegionServerStats(hmaster)
	cp = gatherClientStats()

	# Gather client and server stats while we wait for the JMeter test to finish.
	while jp.poll() == None:
		time.sleep(5)

	# Shut down collectors.
	fullShutdown(rsp, cp)

	# Retrieve and analyze the output.
	analyzeOutput(carbon)

if __name__ == "__main__":
	main()
