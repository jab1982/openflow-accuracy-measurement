#!/usr/bin/env python2

import argparse
import numpy as np
import hashlib

parser = argparse.ArgumentParser()
parser.add_argument("-t", "--truthfile", required=True, help="Ground truth in ovs-ofctl flow format (output of packetgen.py)")
parser.add_argument("-m", "--measuredfile", required=True, help="Measurements in ovs-ofctl dump-flows format")
parser.add_argument("-b", "--byte-delta", type=int, default=0, help="Possible byte delta per packet, used if switches add bytes consistently for some reason")
parser.add_argument("-v", "--verbose", action='store_true', help="Be verbose")
args = parser.parse_args()

TRUTH_IN =  args.truthfile 
MEASURED_IN = args.measuredfile 

truth = {}
with open(TRUTH_IN, 'r') as f:
    for line in f:
        line = line.strip()
        all = line.split(',')
        (_,cookie) = all[0].split("=")
        stats = dict(e.split("=") for e in all[1:]) # first entry is the cookie, skip it using [1:]
        for k in stats:
            stats[k] = int(stats[k])
        stats['n_bytes'] += args.byte_delta * stats['n_packets']
        truth[cookie] = stats
        

measured = {}
with open(MEASURED_IN, 'r') as f:
    for line in f:
        if line.startswith("OFPST_FLOW reply"):
            continue
        exprs = [i.strip() for i in line.split(",")]
        m = dict(e.split("=") for e in exprs[0:5]) # we only need the first five things from the ovs-ofctl dump-flows output
        m['n_bytes']    = int(m['n_bytes'])
        m['n_packets']  = int(m['n_packets'])
        measured[m['cookie']] = m

not_in_truth            = 0
bytes_incorrect         = 0
packets_incorrect       = 0
zeroed_flows            = 0
byte_deltas             = []
packet_deltas           = []
error_log               = []
incorrect_cookies       = []

for m in measured:
    if m in truth:
        if measured[m]['n_packets'] == 0 and measured[m]['n_bytes'] == 0:
            zeroed_flows += 1
        if measured[m]['n_packets'] != truth[m]['n_packets']:
            packets_incorrect += 1
            packet_deltas.append(measured[m]['n_packets'] - truth[m]['n_packets'])
            # Adding verbose info
            error_log.append("%s n_packets %d" % (m, measured[m]['n_packets'] - truth[m]['n_packets']))
            incorrect_cookies.append(m)
        if measured[m]['n_bytes'] != truth[m]['n_bytes']:
            bytes_incorrect += 1
            byte_deltas.append(measured[m]['n_bytes'] - truth[m]['n_bytes'])
            # Adding verbose info
            error_log.append("%s n_bytes measured %d should be %d, factor %f" % #, per packet inaccuracy is %f" %
                (m, measured[m]['n_bytes'] , truth[m]['n_bytes'], measured[m]['n_bytes']/truth[m]['n_bytes']))
                #(m, measured[m]['n_bytes'] , truth[m]['n_bytes'], (measured[m]['n_bytes'] - truth[m]['n_bytes'])/float(measured[m]['n_packets'])))
            incorrect_cookies.append(m)
        del truth[m] # remove, in the end truth should be empty
    else:
       not_in_truth += 1 

print "Summary %s vs %s:" % (MEASURED_IN, TRUTH_IN)
print "Flow with incorrect n_bytes: ", bytes_incorrect
if bytes_incorrect > 0:
    print "Byte delta abs_sum/avg/std min/max: %d/%.2f/%.2f %d/%d" % (np.sum(abs(d) for d in byte_deltas), np.mean(byte_deltas), np.std(byte_deltas), np.min(byte_deltas), np.max(byte_deltas))
print "Flow with incorrect n_packets: ", packets_incorrect
if packets_incorrect > 0:
    print "Packet delta abs_sum/avg/std min/max: %d/%.2f/%.2f %d/%d" % (np.sum(abs(d) for d in packet_deltas), np.mean(packet_deltas), np.std(packet_deltas), np.min(packet_deltas), np.max(packet_deltas))
print "Zeroed flows:", zeroed_flows
print "Missing flows:", len(truth)
print "Unexpected flows:", not_in_truth
print "Incorrect cookies hash:", hashlib.md5("".join(incorrect_cookies)).hexdigest()
if args.verbose:
    print "\n".join(error_log)
