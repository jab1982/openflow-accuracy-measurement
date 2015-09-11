# OpenFlow Accuracy Measurement Tool Suite

This collection of tools can be used to assess certain statistics obtainable from OpenFlow devices.
All tools are based on input/output compatible with the Open vSwitch tools, and *ovs-ofctl* in particular.



## Trace generator

Produces a pcap file, a .flows file (to be fed to `ovs-ofctl add-flows` using stdin) and a .truth file.
The latter is used as input for the Validator script (see below)

usage: tracegen.py [-h] [-t] [-4 | --v6flowlabels] [-i] [-m M] -n N
                   [--table TABLE] [--actions ACTIONS]
                   [--idle-timeout IDLE_TIMEOUT] [--hard-timeout HARD_TIMEOUT]
                   [--vlan VLAN] -o OUTFILE

optional arguments:
  -h, --help            show this help message and exit
  -t, --tcp             Create TCP as L4, default is UDP
  -4, --ipv4            Create IPv4 as L3, default is IPv6
  --v6flowlabels        Create flows based on IPv6 Flow Labels
  -i, --icmp            Create ICMPv6 or ICMPv4
  -m M                  Max number of packets per flow, default 1000
  -n N                  Number of flows to create
  --table TABLE         OpenFlow switch table for the flow entries TODO
                        implement this
  --actions ACTIONS     Define 'actions' attribute for OpenFlow flows. Default
                        'output:2'
  --idle-timeout IDLE_TIMEOUT
                        Set IDLE_TIMEOUT, default 0. Will set send_flow_rem.
  --hard-timeout HARD_TIMEOUT
                        Set HARD_TIMEOUT, default 0. Will set send_flow_rem.
  --vlan VLAN           Set dl_vlan
  -o OUTFILE, --outfile OUTFILE
                        PCAP output file


## Validator

usage: validate.py [-h] -t TRUTHFILE -m MEASUREDFILE [-b BYTE_DELTA] [-v]

optional arguments:
  -h, --help            show this help message and exit
  -t TRUTHFILE, --truthfile TRUTHFILE
                        Ground truth in ovs-ofctl flow format (output of
                        packetgen.py)
  -m MEASUREDFILE, --measuredfile MEASUREDFILE
                        Measurements in ovs-ofctl dump-flows format
  -b BYTE_DELTA, --byte-delta BYTE_DELTA
                        Possible byte delta per packet, used if switches add
                        bytes consistently for some reason
  -v, --verbose         Be verbose


## Duration variance

Lastly, there is a script taking `ovs-ofctl dump-flows` as its input format. It groups flow entries based on their cookie values, and calculates statistical info on the duration of these flow entries. 
More information is in the script itself.
