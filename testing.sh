#!/bin/bash

TRUTH="sink_output.pcap.truth"
DUMPS="sink_output.pcap.dump-flows-of13"
REPS=40
NUMBER_OF_FLOWS=100
OF_BRIDGE="tcp:67.17.206.196:9933"
OF_VERSION="OpenFlow13"
OF_INTF="eth2"
OVERHEAD=4

mkdir tmp

accuracy () {
	TOTAL=$1
	MAX=`echo "$REPS * $NUMBER_OF_FLOWS" | bc -l`
	ACCU=`echo "($MAX - $TOTAL) * 100/ $MAX" | bc -l`
	RESULT=`printf "Accuracy: %0.2f" $ACCU`
	echo "$RESULT %"
}

for SLEEP in `seq 1 25`; do
	TOTAL=0
	echo -n "Delay set to $SLEEP seconds - Values: "
	for I in `seq 1 $REPS`; do
		# echo "Test Sequence $I" | tee results
		sleep 1
		#echo "Deleting OpenFlow entries"
		ovs-ofctl -O $OF_VERSION del-flows $OF_BRIDGE 2>&1 >> results
		sleep 1
		#echo "Adding OpenFlow entries"
		ovs-ofctl -O $OF_VERSION add-flows $OF_BRIDGE sink_output.pcap.flows 2>&1 >> results
		sleep 1
		#echo "Replaying TCP Flows"
		tcpreplay -i $OF_INTF -p 1000 sink_output.pcap 2>> /dev/null >> results
		sleep $SLEEP
		#echo "Dumping OpenFlow entries to sink_output.pcap.dump-flows-of13"
		ovs-ofctl -O $OF_VERSION dump-flows $OF_BRIDGE > sink_output.pcap.dump-flows-of13
		#echo "Validating OpenFlow entries' counters..."
		touch tmp/sink_output.$SLEEP.$I
		VALUE=`python validate.py -t $TRUTH -m $DUMPS -b $OVERHEAD -j tmp/sink_output.$SLEEP.$I | grep "Flow with incorrect n_bytes" | cut -d":" -f2 | sed 's/ //g'`
		echo -n "$VALUE "
		TOTAL=`echo "$VALUE + $TOTAL"| bc -l`
		cp sink_output.pcap.dump-flows-of13 tmp/sink_output.pcap.dump-flows-of13.$SLEEP.$I
	done
	accuracy $TOTAL
done