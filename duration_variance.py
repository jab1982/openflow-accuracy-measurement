#!/usr/bin/env python2
import sys
import numpy as np

# All based on stdin. Make sure input is in the normal 'flow format'.
# Usage: do something like `cat my_measurements.*` | ./duration_variance.py

# Essential here the identification of flows based on their cookie
#   so in all the files cat'd into the script, ensure the same flows have indeed the same cookie

durations = {}
for line in sys.stdin:
    line = line.strip()
    all = [e.strip() for e in line.split(',')]
    (_,cookie) = all[0].split("=")
    stats = dict(e.split("=") for e in all[1:]) # first entry is the cookie, skip it
    duration = float(stats['duration'].strip('s'))
    if cookie not in durations:
        durations[cookie] = []
    durations[cookie].append(duration)


stds = []
for cookie in durations:
    std = np.std(durations[cookie])
    stds.append(std)
print "Overall mean/median std for flow durations: %f %f" % (np.mean(stds), np.median(stds))
