from xml.dom.minidom import parse, parseString
import numpy
import glob
import re

timeStamp = []
elapsed = []
bytes=[]
latency=[]

def outputMeasure(name, values, totalReq, failRatio):
	output = []
	nv = numpy.array(values)
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

# For stripping things that will cause the XML parser to choke.
control_chars = ''.join(map(unichr, [38] + range(127,256)))
control_char_re = re.compile('[%s]' % re.escape(control_chars))

outputs = glob.glob("output.xml.*")
rowCount = 0
failCount = 0
for file in outputs:
	with open(file) as fd:
		text = fd.read()
		stripped = control_char_re.sub('X', text)
		dom = parseString(stripped)

		# Find all samples.
		samples = dom.getElementsByTagName("sample")
		for sample in samples:
			attributeMap = {}
			for a in sample.attributes.items():
				attributeMap[a[0]] = a[1]

			# Skip BeanShell samples.
			if attributeMap["by"] == "0":
				continue

			rowCount = rowCount + 1
			timeStamp.append(int(attributeMap["ts"]))
			elapsed.append(int(attributeMap["t"]))
			bytes.append(int(attributeMap["by"]))
			latency.append(int(attributeMap["lt"]))
			if attributeMap["s"] == "false":
				failCount = failCount + 1

failRatio = "%0.2f" % (100.0 * failCount / rowCount)
print "Measure,Min,Max,Median,90,95,99,99.9,TotalReq,FailRatio"
outputMeasure("elapsed", elapsed, rowCount, failRatio)
outputMeasure("bytes", bytes, rowCount, failRatio)
outputMeasure("latency", latency, rowCount, failRatio)
