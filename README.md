Sample invocation for a Sandbox environment:

./build_driver.sh && \
	./generate_data.sh 2 && \
	./load_data.sh 2 sandbox.hortonworks.com:2181:/hbase-unsecure
