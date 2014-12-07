#!/usr/bin/python

import os
import getopt, sys
import re

DEBUG = 1
TESTHOSTS = "../testhosts"

def runCommand(command, error):
	if DEBUG:
		print command
	ret = os.system(command)
	if ret != 0:
		assert False, error

def runJmeter():
	# See if JMeter is properly deployed everywhere.
	testJmeter = 'pdsh -S -w ^' + TESTHOSTS + ' "test -e /tmp/phoenix-performance/apache-jmeter*/lib/phoenix*.jar"'
	runCommand(testJmeter, "JMeter is not properly deployed on all nodes")

	# Clean up prior runs.
	cleanupJmeter = 'pdsh -S -w ^' + TESTHOSTS + ' "rm -f jmeter.log output.xml root.log"'
	runCommand(cleanupJmeter, "Cleanup failed")

	# Deploy the temp JMX on all nodes.
	distJmx = "pdcp -w ^" + TESTHOSTS + " temp.jmx /tmp/temp.jmx"
	runCommand(distJmx, "Failed to deploy JMeter spec")

	# Run JMeter on all nodes.
	runJmeter = 'pdsh -S -w ^' + TESTHOSTS + ' "/tmp/phoenix-performance/apache-jmeter*/bin/jmeter -n -t /tmp/temp.jmx"'
	runCommand(runJmeter, "JMeter execution failed")

def analyzeOutput():
	# Bring the various output files local.
	bringFiles = 'rpdcp -w ^' + TESTHOSTS + ' output.xml .'
	runCommand(bringFiles, "Failed to retrieve JMeter results")

	# Run the analysis.
	analyze = "python analyze.py"
	runCommand(analyze, "Analyze command failed")

def main():
	try:
		opts, args = getopt.getopt(sys.argv[1:], "i:t:v:", ["help", "output="])
	except getopt.GetoptError as err:
		print str(err)
		sys.exit(2)
	input = None
	output = "output.xml"
	variables = []
	for o, a in opts:
		if o == "-i":
			input = a
		elif o == "-t":
			TESTHOSTS = a
		elif o == "-v":
			variables.append(a.split("="))
		else:
			assert False, "unhandled option"

	if input == None:
		assert False, "Need an input file"

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
	runJmeter()

	# Analyze the output.
	analyzeOutput()

if __name__ == "__main__":
	main()
