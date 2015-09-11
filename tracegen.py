#!/usr/bin/env python2

import sys
from scapy.all import *
import logging
import random
import argparse
logging.getLogger("scapy").setLevel(1)

parser = argparse.ArgumentParser()
l4group = parser.add_mutually_exclusive_group()
v6flgroup = parser.add_mutually_exclusive_group()
l4group.add_argument("-t", "--tcp", help="Create TCP as L4, default is UDP", action="store_true")
v6flgroup.add_argument("-4", "--ipv4", help="Create IPv4 as L3, default is IPv6", action="store_true")
v6flgroup.add_argument("--v6flowlabels", help="Create flows based on IPv6 Flow Labels", action="store_true")
l4group.add_argument("-i", "--icmp", help="Create ICMPv6 or ICMPv4", action="store_true")
parser.add_argument("-m", type=int, help="Max number of packets per flow, default 1000", default=1000)
parser.add_argument("-n", required=True, type=int, help="Number of flows to create")

parser.add_argument("--table", type=int, default=0, help="OpenFlow switch table for the flow entries TODO implement this")
parser.add_argument("--actions", default="output:2", help="Define 'actions' attribute for OpenFlow flows. Default 'output:2'")
parser.add_argument("--idle-timeout", type=int, default=0, help="Set IDLE_TIMEOUT, default 0. Will set send_flow_rem.")
parser.add_argument("--hard-timeout", type=int, default=0, help="Set HARD_TIMEOUT, default 0. Will set send_flow_rem.")
parser.add_argument("--vlan", type=int, help="Set dl_vlan")

parser.add_argument("-o", "--outfile", required=True, help="PCAP output file")

args = parser.parse_args()
SEND_FLOW_REM   = 'send_flow_rem' if (args.idle_timeout > 0 or args.hard_timeout > 0) else ''
DL_VLAN         = 'dl_vlan=%d' % (args.vlan) if args.vlan else ''


f_truth = open(args.outfile + ".truth", 'w')
f_flows = open(args.outfile + ".flows", 'w')

# set PROTO to (tcp|udp|icmp)(6), to be used on ovs-ofctl add-flow as shortcut
PROTO   = 'tcp' if args.tcp else 'udp'
PROTO   = 'icmp' if args.icmp else PROTO
PROTO   = PROTO + "6" if not args.ipv4 else PROTO

MAX_PPF     = args.m
NUM_FLOWS   = args.n
ACTIONS     = args.actions
TABLE       = "table=%d" % (args.table)
MAX_PAYLOAD = 1438 # based on ether/v6/udp

progress10percent = NUM_FLOWS/10.0

TEMPLATES = {}
TEMPLATES['truth']  = "cookie=0x%x,n_bytes=%d,n_packets=%d\n"
TEMPLATES['udp']    = "cookie=0x%x,%s,%s,nw_src=%s,nw_dst=%s,tp_src=%d,tp_dst=%d,%s,%s,idle_timeout=%d,hard_timeout=%d,actions=%s\n"#,n_bytes=%d,n_packets=%d"
TEMPLATES['tcp']    = TEMPLATES['udp']
TEMPLATES['udp6']   = "cookie=0x%x,%s,%s,ipv6_src=%s,ipv6_dst=%s,tp_src=%d,tp_dst=%d,%s,%s,idle_timeout=%d,hard_timeout=%d,actions=%s\n"#,n_bytes=%d,n_packets=%d"
TEMPLATES['tcp6']   = TEMPLATES['udp6']
TEMPLATES['icmp']   = "cookie=0x%x,%s,%s,nw_src=%s,nw_dst=%s,tp_src=%d,tp_dst=%d,%s,%s,idle_timeout=%d,hard_timeout=%d,actions=%s\n"#,n_bytes=%d,n_packets=%d"
TEMPLATES['icmp6']  = "cookie=0x%x,%s,%s,ipv6_src=%s,ipv6_dst=%s,icmp_type=%d,icmp_code=%d,%s,%s,idle_timeout=%d,hard_timeout=%d,actions=%s\n"#,n_bytes=%d,n_packets=%d"
TEMPLATES['v6fl']   = "cookie=0x%x,%s,%s,ipv6_src=%s,ipv6_dst=%s,ipv6_label=0x%x,%s,%s,idle_timeout=%d,hard_timeout=%d,actions=%s\n"

all_packets = []
cookie_id = 0
for i in xrange(0,NUM_FLOWS):
    cookie_id += 1
    # don't use RandMAC() for src, as some switches want to see 'valid' MACs. Use MAC of the machine this script is run on instead
    # use broadcast as dst MAC, again some switches will drop frames otherwise
    l2=Ether(dst="FF:FF:FF:FF:FF:FF")
    if args.ipv4:
        # source address should not be multicast, so outside of 224.0.0.0 - 239.255.255.255
        # dst address can also be dropped due to restrictions in certain devices, we use the same range
        l3=IP(src=RandIP('160.0.0.0/2')._fix(),dst=RandIP('160.0.0.0/2')._fix())
    elif args.v6flowlabels:
        l3=IPv6(src=RandIP6("2001:db8:*:*:*:*:*:*")._fix(),dst=RandIP6("2001:db8:*:*:*:*:*:*")._fix(), fl=RandNum(1,1048575))
    else:
        l3=IPv6(src=RandIP6("2001:db8:*:*:*:*:*:*")._fix(),dst=RandIP6("2001:db8:*:*:*:*:*:*")._fix())

    if args.tcp: 
        l4=TCP(sport=RandNum(1024,65535)._fix(), dport=RandNum(1,1023)._fix())
    elif args.icmp:
        if args.ipv4:
            l4=ICMP(type=RandNum(0,255)._fix(), code=RandNum(0,255)._fix())
        else:
            l4=ICMPv6Unknown(type=RandNum(0,255)._fix(), code=RandNum(0,255)._fix())
    else:
        l4=UDP(sport=RandNum(1024,65535)._fix(), dport=RandNum(1,1023)._fix())
    
    # Number of packets for this flow
    ppf=random.randint(1,MAX_PPF)

    # we need frames of >=64 bytes, else padding will occur and measurements will be off
    # Ergo payload is 22 minimum to get v4 to at least 64bytes
    payloads=Raw(load=[RandString(size=RandNum(22,MAX_PAYLOAD))._fix() for x in xrange(0,ppf)]) 
    packets = l2/l3/l4/payloads

    # Number of bytes for this flow
    bpf     = sum([len(p) for p in packets])

    if args.icmp:
        f_flows.write(TEMPLATES[PROTO] % (cookie_id, TABLE, PROTO, l3.src, l3.dst, l4.type, l4.code, DL_VLAN, SEND_FLOW_REM, args.idle_timeout, args.hard_timeout, ACTIONS))
    elif args.v6flowlabels:
        f_flows.write(TEMPLATES['v6fl'] % (cookie_id, TABLE, PROTO, l3.src, l3.dst, l3.fl, DL_VLAN, SEND_FLOW_REM, args.idle_timeout, args.hard_timeout, ACTIONS))
    else:
        f_flows.write(TEMPLATES[PROTO] % (cookie_id, TABLE, PROTO, l3.src, l3.dst, l4.sport, l4.dport, DL_VLAN, SEND_FLOW_REM, args.idle_timeout, args.hard_timeout, ACTIONS))

    f_truth.write(TEMPLATES['truth'] % (cookie_id, bpf, ppf))
    all_packets += packets 
    if cookie_id % progress10percent == 0:
        progress = cookie_id/progress10percent * 10
        print '%d%% ..' % (progress),
        sys.stdout.flush()
    

f_truth.close()
f_flows.close()

# now shuffle and write all the packets
print 'shuffling ..',
shuffled = sorted(all_packets, key=lambda p: random.randint(0,MAX_PPF))
print 'writing pcap ..',
wrpcap(args.outfile, shuffled)
print 'done'
