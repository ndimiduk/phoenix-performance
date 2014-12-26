import xml.parsers.expat
import csv
import numpy
import getopt
import glob
import re
import socket
import sys
import datetime

reportGranularity = 5
rowCount = 0
failCount = 0
timestamp = []
elapsed = []
bytes=[]
latency=[]
minTimestamp = sys.maxint
maxTimestamp = 0

def netcat(hostname, port, content):
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((hostname, port))
	s.sendall(content)
	s.shutdown(socket.SHUT_WR)
	s.close()

def outputMeasure(name, values, totalReq, failRatio):
	nv = numpy.array(values)
	output = []
	output.append(name)
	output.append(numpy.min(nv))
	output.append(numpy.max(nv))
	output.append(numpy.median(nv))
	output.append(numpy.percentile(nv, 90))
	output.append(numpy.percentile(nv, 95))
	output.append(numpy.percentile(nv, 99))
	output.append(numpy.percentile(nv, 99.9))
	output.append(totalReq)
	output.append(failRatio)
	output = [ str(x) for x in output ]
	print ",".join(output)

def start_element(name, attributeMap):
	global rowCount, failCount
	global timestamp, elapsed, bytes, latency
	global minTimestamp, maxTimestamp

	if name != "sample":
		return

	# Skip BeanShell samples.
	if attributeMap["by"] == "0":
		return

	rowCount = rowCount + 1
	elapsed.append(int(attributeMap["t"]))
	bytes.append(int(attributeMap["by"]))
	latency.append(int(attributeMap["lt"]))
	if attributeMap["s"] == "false":
		failCount = failCount + 1

	ts = int(attributeMap["ts"])
	timestamp.append(ts)
	if ts < minTimestamp:
		minTimestamp = ts
	if ts > maxTimestamp:
		maxTimestamp = ts

def process():
	global rowCount, failCount
	global timestamp, elapsed, bytes, latency
	global minTimestamp, maxTimestamp
	results = []

	# For stripping things that will cause the XML parser to choke.
	control_chars = ''.join(map(unichr, [38] + range(127,256)))
	control_char_re = re.compile('[%s]' % re.escape(control_chars))

	csvs = glob.glob("output.csv.*")
	xmls = glob.glob("output.xml.*")

	for xml in xmls:
		with open(xml) as fd:
			text = fd.read()
			fd.close()
			stripped = control_char_re.sub('X', text)
			p = xml.parsers.expat.ParserCreate()
			p.StartElementHandler = start_element
			p.Parse(stripped)

	for csvf in csvs:
		with open(csvf) as fd:
			r = csv.reader(fd)
			next(r, None) 
			for row in r:
				rowCount = rowCount + 1
				elapsed.append(int(row[1]))
				bytes.append(int(row[5]))
				latency.append(int(row[6]))
				if row[4] == "false":
					failCount = failCount + 1
				ts = int(row[0])
				timestamp.append(ts)
				if ts < minTimestamp:
					minTimestamp = ts
				if ts > maxTimestamp:
					maxTimestamp = ts

	failRatio = "%0.2f" % (100.0 * failCount / rowCount)
	print "Measure,Min,Max,Median,90,95,99,99.9,TotalReq,FailRatio"
	outputMeasure("elapsed", elapsed, rowCount, failRatio)
	outputMeasure("bytes", bytes, rowCount, failRatio)
	outputMeasure("latency", latency, rowCount, failRatio)
	print

	# Calculate the requests per second on 10 second boundaries.
	boundary = 10
	timestamp.sort()
	timestamp = [ x/1000 for x in timestamp ]
	minTime = timestamp[0]
	maxTime = timestamp[-1]
	blockMin = ((minTime / boundary) * boundary)
	blockMax = blockMin + boundary
	ts = numpy.asarray(timestamp)
	while blockMin < maxTime:
		maxt = datetime.datetime.fromtimestamp(blockMax).strftime("%s")
		rps = ((ts <= blockMax).sum() - (ts < blockMin).sum()) * 1.0 / boundary
		value = "phoenix.opspersec.cluster %f %s" % (rps, maxt)
		#print value
		results.append(value)
		blockMin = blockMax
		blockMax = blockMax + boundary

	totalTime = (maxTimestamp - minTimestamp) / 1000.0
	#print "Total requests per second = %02f" % ((rowCount * 1.0) / (totalTime))
	return results

def main():
	try:
		opts, args = getopt.getopt(sys.argv[1:], "c:", ["help", "output="])
	except getopt.GetoptError as err:
		print str(err)
		print "Arguments: -c carbon"
		print "Ex: analyze.py -c 192.168.129.147:2003"
		sys.exit(2)

	carbonHost = None
	carbonPort = None
	for o, a in opts:
		if o == "-c":
			(carbonHost, carbonPort) = a.split(":")
			carbonPort = int(carbonPort)
		else:
			assert False, "unhandled option"

	results = process()
	rtext = "\n".join(results)
	print rtext
	if carbonHost:
		netcat(carbonHost, carbonPort, rtext)

main()
