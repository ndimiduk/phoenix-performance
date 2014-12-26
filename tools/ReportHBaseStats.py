#!/usr/bin/python

import re
import subprocess

def main():
	# Get the status using the hbase shell.
	#cmd = ['hbase', 'shell']
	#p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
	#	stderr=subprocess.PIPE, stdin=subprocess.PIPE)
	#out, err = p.communicate("status 'detailed'")
	fd = open("sample.txt")
	out = fd.read()

	# States.
	LOOK_FOR_SERVER_OR_REGION = 1
	GET_SERVER_STATS = 2
	GET_REGION_STATS = 3

	# Regular expressions.
	serverRe = "^    ([^ :]+)"
	regionRe = '^        "([^"]+)'

	# Walk through the status line by line.
	state = LOOK_FOR_SERVER_OR_REGION
	for line in out.split("\n"):
		if state == LOOK_FOR_SERVER_OR_REGION:
			m = re.match(serverRe, line)
			if m:
				print m.group(1)
				state = GET_SERVER_STATS
			m = re.match(regionRe, line)
			if m:
				regionInfo = m.group(1)
				info = regionInfo.split(",")
				print info[0], " ", info[1]
				state = GET_REGION_STATS
		elif state == GET_SERVER_STATS:
			state = LOOK_FOR_SERVER_OR_REGION
			info = [ x.strip() for x in line.split(",") ]
			print info
		elif state == GET_REGION_STATS:
			state = LOOK_FOR_SERVER_OR_REGION
			info = [ x.strip() for x in line.split(",") ]

main()








