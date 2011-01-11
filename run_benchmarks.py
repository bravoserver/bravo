#!/usr/bin/env python

from __future__ import division

import datetime
import glob
import imp
import math
import os.path
import urllib
import urllib2
import subprocess

description = subprocess.Popen(["git", "describe"],
    stdout=subprocess.PIPE).communicate()
description = description[0].strip()

URL = "http://athena.osuosl.org/"

data = {
    'commitid': description,
    'project': 'Bravo',
    'executable': 'CPython 2.6.6',
    'environment': "Athena",
    'result_date': datetime.datetime.today(),
}

def add(data):
    params = urllib.urlencode(data)
    response = None
    print "Executable %s, revision %s, benchmark %s" % (data['executable'], data['commitid'], data['benchmark'])
    f = urllib2.urlopen('%sresult/add/' % URL, params)
    response = f.read()
    f.close()
    print "Server (%s) response: %s" % (URL, response)

def average(l):
    return sum(l) / len(l)

def stddev(l):
    return math.sqrt(sum((i - average(l))**2 for i in l))

def main():
    for bench in glob.glob("benchmarks/*.py"):
        name = os.path.splitext(os.path.basename(bench))[0]
        module = imp.load_source("bench", bench)
        benchmarks = module.benchmarks
        print "Running benchmarks in %s..." % name
        for benchmark in benchmarks:
            name, l = benchmark()
            print "%s: Average %f, min %f, max %f, stddev %f" % (
                name, average(l), min(l), max(l), stddev(l))
            d = {
                "benchmark": name,
                "result_value": average(l),
                "std_dev": stddev(l),
                "max": max(l),
                "min": min(l),
            }
            d.update(data)

if __name__ == "__main__":
    main()
