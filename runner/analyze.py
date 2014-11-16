import csv
import numpy
import glob

timeStamp = []
elapsed = []
bytes=[]
latency=[]

def outputMeasure(name, values):
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
	output = [ str(x) for x in output ]
	print ",".join(output)

outputs = glob.glob("output.csv.*")
for file in outputs:
	with open(file) as csvfile:
		reader = csv.reader(csvfile)
		next(reader)
		for row in reader:
			timeStamp.append(int(row[0]))
			elapsed.append(int(row[1]))
			bytes.append(int(row[5]))
			latency.append(int(row[6]))

print "Measure,Min,Max,Median,90,95,99,99.9"
outputMeasure("elapsed", elapsed)
outputMeasure("bytes", bytes)
outputMeasure("latency", latency)
