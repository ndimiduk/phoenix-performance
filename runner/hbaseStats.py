#!/usr/bin/python

import datetime
import getopt
import json
import requests
import sys
import time

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
		opts, args = getopt.getopt(sys.argv[1:], "m:s:", ["help", "output="])
	except getopt.GetoptError as err:
		print str(err)
		sys.exit(2)

	hmaster = None
	sleepTime = 5
	for o, a in opts:
		if o == "-m":
			hmaster = a
		elif o == "-s":
			sleepTime = int(a)
		else:
			assert False, "unhandled option"

	if hmaster == None:
		assert False, "Need HMaster (-m)"

	while True:
		# Wait for an appropriate start time (5s boundary).
		sometime = (int(time.time() / 5) * 5) + 5 - time.time()
		time.sleep(sometime)

		# Poll all regionservers (serially)
		poll(hmaster)

main()
