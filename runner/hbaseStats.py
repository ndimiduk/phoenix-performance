#!/usr/bin/python

import datetime
import getopt
import json
import operator
import re
import requests
import socket
import sys
import time
import urllib

def netcat(hostname, port, content):
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((hostname, port))
	s.sendall(content)
	s.shutdown(socket.SHUT_WR)
	s.close()

def findBean(beans, name):
	for bean in beans:
		if bean["name"] == name:
			return bean

def gatherProperties(map, attributes, props):
	for a in attributes:
		props[a] = map[a]
	return props

def customSorter(x):
	if x == "Host":
		return "AAA"
	if x == "Timestamp":
		return "AAB"
	return x

def printProperties(props):
	try:
		printProperties.header = printProperties.header
	except AttributeError:
		printProperties.header = 0

	keys = props.keys()
	keys = sorted(keys, key=lambda x: customSorter(x))
	if printProperties.header == 0:
		printProperties.header = 1
		print ",".join(keys)
	ary = []
	for k in keys:
		ary.append(str(props[k]))
	print ",".join(ary)

def newPoll(hmaster):
	# Load info from the HMaster.
	hmasterJmx = "http://" + hmaster + "/jmx"
	targetMasterBeanName = "Hadoop:service=HBase,name=Master,sub=Server"
	r = requests.get(hmasterJmx)
	rawJson = r.text
	decoded = json.loads(rawJson)
	targetBean = findBean(decoded["beans"], targetMasterBeanName)

	regionBean = 'Hadoop:service=HBase,name=RegionServer,sub=Regions'
	excludeBean = [
		'JMImplementation:type=MBeanServerDelegate',
		'java.lang',
		'java.util.logging',
		'com.sun.management',
		# regionBean,
	]
	excludeTable = [
		'kylin',
	]

	# Iterate through all live RegionServers.
	results = []
	liveRegionServers = targetBean["tag.liveRegionServers"]
	regionServers = liveRegionServers.split(";")
	regionRe = "[Nn]amespace_([^_]+)_table_(.+?)_region_[0-9a-f]+_metric_(.+)"
	tableStats = {}
	for r in regionServers:
		components = r.split(",")
		host = components[0]
		endpoint = "http://" + host + ":60030/jmx"
		rsStats = requests.get(endpoint)
		rsJson = rsStats.text
		statJson = json.loads(rsJson)

		now = int(time.time())
		beans = statJson["beans"]
		for bean in beans:
			beanName = bean["name"]
			if len(filter(lambda x: beanName.find(x) > -1, excludeBean)) > 0:
				continue
			#beanName = urllib.quote_plus(beanName)
			if beanName == regionBean:
				for property in bean.keys():
					val = bean[property]
					m = re.match(regionRe, property)
					if m:
						(namespace, table, stat) = (m.group(1), m.group(2), m.group(3))
						if len(filter(lambda x: table.find(x) > -1, excludeTable)) > 0:
							continue
						fqTable = "%s.%s" % (namespace, table)
						if tableStats.has_key(fqTable):
							tableStats[fqTable].append([stat, val])
						else:
							tableStats[fqTable] = [[stat, val]]
					else:
						pass
				pass
			else:
				for property in bean.keys():
					if property == "name":
						continue
					val = bean[property]
					if isinstance(val, int) or isinstance(val, float):
						stat = "hbase.%s.%s %s %d" % (host, property, val, now)
						results.append(stat)

	rollupTableStats(results, tableStats)
	return results

def meanOfMeans(means, numbers):
	total = sum(numbers)
	if total == 0:
		return 0
	return sum(map(operator.mul, means, numbers)) * 1.0 / total

# Note: This is just an estimate.
def medianOfMedians(list):
	list.sort()
	return list[len(list)/2]

def variance(list):
	average = sum(list) / len(list)
	variance = sum((average - value) ** 2 for value in list) / len(list)
	return variance

def rollupTableStats(results, tableStats):
	stats = {}
	regionMetrics = {}

	operations = {
		"appendCount"			: sum,
		"compactionsCompletedCount"	: sum,
		"deleteCount"			: sum,
		"get_75th_percentile"		: max,
		"get_95th_percentile"		: max,
		"get_99th_percentile"		: max,
		"get_max"			: max,
		"get_mean"			: "special",
		"get_median"			: medianOfMedians,
		"get_min"			: min,
		"get_num_ops"			: sum,
		"incrementCount"		: sum,
		"memStoreSize"			: sum,
		"mutateCount"			: sum,
		"numBytesCompactedCount"	: sum,
		"numFilesCompactedCount"	: sum,
		"scanNext_75th_percentile"	: max,
		"scanNext_95th_percentile"	: max,
		"scanNext_99th_percentile"	: max,
		"scanNext_max"			: max,
		"scanNext_mean"			: "special",
		"scanNext_median"		: medianOfMedians,
		"scanNext_min"			: min,
		"scanNext_num_ops"		: sum,
		"storeCount"			: sum,
		"storeFileCount"		: sum,
		"storeFileSize"			: sum,
		"get_num_var"			: "special",
		"scanNext_num_var"		: "special",
	}

	for table in tableStats.keys():
		stats[table] = {}
		regionMetrics[table] = []
		regionStats = tableStats[table]

		for o in operations:
			function = operations[o]
			if function == "special":
				continue
			hits = filter(lambda x: x[0] == o, regionStats)
			values = [ x[1] for x in hits ]
			stats[table][o] = function(values)

		# Special values.
		numOps = filter(lambda x: x[0] == "get_num_ops", regionStats)
		numOps = [ x[1] for x in numOps ]
		stats[table]["get_num_var"] = variance(numOps)
		gmeans = filter(lambda x: x[0] == "get_mean", regionStats)
		gmeans = [ x[1] for x in gmeans ]
		stats[table]["get_mean"] = meanOfMeans(gmeans, numOps)
		numOps = filter(lambda x: x[0] == "scanNext_num_ops", regionStats)
		numOps = [ x[1] for x in numOps ]
		stats[table]["scanNext_num_var"] = variance(numOps)
		smeans = filter(lambda x: x[0] == "scanNext_mean", regionStats)
		smeans = [ x[1] for x in smeans ]
		stats[table]["scanNext_mean"] = meanOfMeans(smeans, numOps)

	# Add the stats in.
	now = int(time.time())
	for table in tableStats.keys():
		for met in operations.keys():
			metric = "%s.%s" % (table, met)
			val = stats[table][met]
			stat = "hbase.table.%s %s %d" % (metric, val, now)
			results.append(stat)

def poll(hmaster):
	hmasterJmx = "http://" + hmaster + "/jmx"
	targetMasterBeanName = "Hadoop:service=HBase,name=Master,sub=Server"
	regionServerServerBeanName = "Hadoop:service=HBase,name=RegionServer,sub=Server"
	regionServerRegionsBeanName = "Hadoop:service=HBase,name=RegionServer,sub=Regions"
	regionServerMetricsBeanName = "Hadoop:service=HBase,name=MetricsSystem,sub=Stats"
	regionServerIPCBeanName = "Hadoop:service=HBase,name=IPC,sub=IPC"
	regionServerOSBeanName = "java.lang:type=OperatingSystem"

	r = requests.get(hmasterJmx)
	rawJson = r.text
	decoded = json.loads(rawJson)
	targetBean = findBean(decoded["beans"], targetMasterBeanName)

	liveRegionServers = targetBean["tag.liveRegionServers"]
	regionServers = liveRegionServers.split(";")
	now = datetime.datetime.utcnow()
	for r in regionServers:
		components = r.split(",")
		host = components[0]
		endpoint = "http://" + host + ":60030/jmx"
		rsStats = requests.get(endpoint)
		rsJson = rsStats.text
		statJson = json.loads(rsJson)
		#print rsJson

		props = { "Host" : host, "Timestamp" : now }

		serverBean = findBean(statJson["beans"], regionServerServerBeanName)
		attributes = [
			"regionCount",
			"storeFileSize",
			"percentFilesLocal",
			"Get_median",
			"Get_99th_percentile",
			"totalRequestCount",
			"readRequestCount",
			"blockCacheHitCount",
			"blockCacheMissCount",
			"blockCacheEvictionCount",
			"blockCountHitPercent",
		]
		props = gatherProperties(serverBean, attributes, props)

		IPCBean = findBean(statJson["beans"], regionServerIPCBeanName)
		attributes = [
			"numCallsInGeneralQueue",
			"QueueCallTime_num_ops",
			"ProcessCallTime_num_ops",
			"ProcessCallTime_mean",
		]
		props = gatherProperties(IPCBean, attributes, props)

		OSBean = findBean(statJson["beans"], regionServerOSBeanName)
		attributes = [
			"ProcessCpuLoad",
			"SystemCpuLoad",
			"SystemLoadAverage",
			"AvailableProcessors",
		]
		props = gatherProperties(OSBean, attributes, props)

		printProperties(props)

def main():
	try:
		opts, args = getopt.getopt(sys.argv[1:], "b:c:m:", ["help", "output="])
	except getopt.GetoptError as err:
		print str(err)
		print "Arguments: -m hmaster -b boundary -c carbon"
		print "Ex: hbaseStats.py -m 192.168.129.137:60010 -c 192.168.129.147:2003"
		sys.exit(2)

	hmaster = None
	boundary = 10
	carbonHost = None
	carbonPort = None
	for o, a in opts:
		if o == "-m":
			hmaster = a
		elif o == "-b":
			boundary = int(a)
		elif o == "-c":
			(carbonHost, carbonPort) = a.split(":")
			carbonPort = int(carbonPort)
		else:
			assert False, "unhandled option"

	if hmaster == None:
		assert False, "Need HMaster (ex: -m 192.168.129.137:60010)"

	while True:
		# Wait for the boundary time.
		sometime = (int(time.time() / boundary) * boundary) + boundary - time.time()
                print "sleeping for %s" % sometime
		time.sleep(sometime)

		# Poll all regionservers (serially)
		results = newPoll(hmaster)
		rtext = "\n".join(results)
		if carbonHost:
			print "Sending stats to carbon"
			print rtext
			netcat(carbonHost, carbonPort, rtext)
		else:
			print rtext

main()
