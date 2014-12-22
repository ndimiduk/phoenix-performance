#!/usr/bin/python

import getopt
import os
import re
import subprocess
import sys
import time

DEBUG = 1
CLUSTERHOSTS = "../clusterhosts"

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

def runGather():
	# Launch the command.
	sarCommand = "sar -d -n DEV -u -q -r -S 5"
	sarCommand = 'pdsh -w ^' + CLUSTERHOSTS + ' ' + sarCommand
	runCommand(sarCommand, "Failed to run sar")

def analyzeOutput():
	pass

def main():
	try:
		opts, args = getopt.getopt(sys.argv[1:], "i:", ["help", "output="])
	except getopt.GetoptError as err:
		print str(err)
		sys.exit(2)

	# Start close to a 5s boundary.
	sometime = (int(time.time() / 5) * 5) + 5 - time.time()
	time.sleep(sometime)

	# Gather the stats.
	runGather()

if __name__ == "__main__":
	main()
