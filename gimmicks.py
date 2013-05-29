#!/usr/bin/env python
import codecs
from fractions import Fraction
import logging
import os
import pprint
import sys
from decimal import *

from simfile import *
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

import synctools

__all__ = ['gimmicks']




def gimmicks(simfile):
    log = logging.getLogger('synctools')
    cfg = synctools.get_config()
    synctools.backup(simfile)
    gpath = os.path.join(os.path.split(simfile.filename)[0], 'gimmicks.txt')
    
    # Parse gimmicks.txt.
    with open(gpath, 'r') as gfile:
        g = yaml.load(gfile, Loader=Loader)
    
    # Ensure the BPM is a float, not an integer
    g['bpm'] = float(g['bpm'])
    
    # Convert each gimmick line into a set of BPMs and stops.
    t = {
        'bpms': {0: g['bpm']},
        'stops': {},
    }
    gimmicks = sorted(((str(a), str(b)) for a, b in g['gimmicks'].iteritems()),
                      key=(lambda t: str(t[0]).split('-')[0]))
    for i, (beats, gimmick) in enumerate(gimmicks):
        # Split the gimmick into its segments
        length, mul, name = gimmick.split()
        length = float(Fraction(length)) * 4
        mul = float(Fraction(mul.rstrip('x')))
        if '-' in beats:
            # beats defined as "start-stop"
            start, stop = beats.split('-')
            start = float(start)
            if not stop:
                # beats defined as "start-"; stop when the next gimmick starts
                if i + 1 == len(gimmicks):
                    raise ValueError("can't end with an indefinite gimmick")
                stop = gimmicks[i + 1][0].split('-')[0]
            stop = float(stop)
        else:
            # beats defined as "start"; stop after one iteration
            start = float(beats)
            stop = start + length
        full_length = stop - start
        
        if 'definitions' in g and name in g['definitions']:
            definition = g['definitions'][name]
        elif name in builtin_gimmicks:
            definition = builtin_gimmicks[name]
        
        for timing in ('bpms', 'stops'):
            if timing in definition:
                for loc, eq in definition[timing].iteritems():
                    loc = float(loc)
                    pos = start + length * loc
                    val = eval(eq, {
                        '__builtins__': None,
                        'mul': mul,
                        'len': length,
                        'bpm': g['bpm'],
                    })
                    while decimal_from_192nd(pos) < decimal_from_192nd(stop):
                        t[timing][pos] = val
                        pos += length
                
                if timing == 'bpms':
                    t['bpms'][stop] = g['bpm']
    
    # Sort BPMs and stops
    last_bpm = None
    for timing in ('bpms', 'stops'):
        tlist = []
        while t[timing]:
            k = min(t[timing].keys())
            v = t[timing].pop(k)
            if timing == 'bpms' and v == last_bpm:
                continue
            tlist.append('%s=%s' % (decimal_from_192nd(k),
                                    decimal_from_192nd(v)))
            if timing == 'bpms':
                last_bpm = v
        simfile.get(timing)[1] = Timing(','.join(tlist))
    
    simfile.save()


builtin_gimmicks = yaml.load("""
stutter:
    bpms:
        0: bpm * mul
    stops:
        0: 60 / (bpm * mul) * ((mul - 1) * len)

midstutter:
    bpms:
        0: bpm * mul
    stops:
        0.5: 60 / (bpm * mul) * ((mul - 1) * len)

halfbrake:
    bpms:
        0: bpm * mul
        0.5: bpm / ((mul - .5) * (2 / mul))

quarterbrake:
    bpms:
        0: bpm * mul
        0.75: bpm / ((mul - .75) * (4 / mul))

halfboost:
    bpms:
        0: bpm / ((mul - .5) * (2 / mul))
        0.5: bpm * mul

quarterboost:
    bpms:
        0: bpm / ((mul - .75) * (4 / mul))
        0.25: bpm * mul
""", Loader=Loader)

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))
    synctools.main_iterator(gimmicks, sys.argv[1:])