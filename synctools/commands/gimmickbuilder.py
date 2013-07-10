#!/usr/bin/env python
from fractions import Fraction
import os

from simfile import decimal_from_192nd, Timing
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from synctools import command

__all__ = ['GimmickBuilder']

class GimmickBuilder(command.SynctoolsCommand):
    
    title = 'Gimmick builder'
    description='convert a gimmicks.txt file into BPM changes and stops'
    fields = []
    
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
    
    def parse_beats(self, beats, nextbeats, length):
        if '-' in beats:
            # beats defined as "start-[stop]"
            start, stop = beats.split('-', 1)
            start = float(start)
            if stop:
                # "start-stop"
                stop = float(stop)
            else:
                # "start-"
                if not nextbeats:
                    raise ValueError("can't end with an indefinite gimmick")
                stop = self.parse_beats(nextbeats, '0', 0)[0]
        else:
            # beats defined as just "start"; stop after one iteration
            if length is None:
                raise ValueError("can't have a one-time copy gimmick")
            start = float(beats)
            stop = start + length
        return (start, stop)

    def add_offset(self, gimmick, offset):
        gimmick = list(gimmick)
        if '-' in gimmick[0]:
            start, stop = gimmick[0].split('-', 1)
            start = str(float(start) + offset)
            if stop: stop = str(float(stop) + offset)
            gimmick[0] = '-'.join((start, stop))
        else:
            gimmick[0] = str(float(gimmick[0]) + offset)
        return gimmick

    def parse_gimmick(self, g, t, gimmicks, gimmick, nextgimmick):
        beats = gimmick[0]
        gimmick = gimmick[1].split()
        
        # Copy gimmicks
        if gimmick[0] == 'copy':
            start, stop = self.parse_beats(beats,
                nextgimmick[0] if nextgimmick else None, None)
            copy_start = float(gimmick[1])
            copy_stop = copy_start + stop - start
            offset = start - copy_start
            for j, copy_gimmick in enumerate(gimmicks):
                if (copy_start <=
                        self.parse_beats(copy_gimmick[0], '0', 0)[0] <
                        copy_stop):
                    self.log.debug('%s-%s (%s): copying %s' %
                        (start, stop, offset, copy_gimmick))
                    self.parse_gimmick(g, t, gimmicks,
                                  self.add_offset(copy_gimmick, offset),
                                  self.add_offset(gimmicks[j + 1], offset)
                                  if j + 1 < len(gimmicks) else None)
            return
        
        # Split the gimmick into its segments
        try:
            length, mul, name = gimmick
        except ValueError:
            raise ValueError("%s is not of the form 'length mul name'")
        length = float(Fraction(length)) * 4
        mul = float(Fraction(mul.rstrip('x')))
        start, stop = self.parse_beats(beats,
                                       nextgimmick[0] if nextgimmick else None,
                                       length)
        full_length = stop - start
        
        if 'definitions' in g and name in g['definitions']:
            definition = g['definitions'][name]
        elif name in self.builtin_gimmicks:
            definition = self.builtin_gimmicks[name]
        
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

    def run(self, simfile):
        super(GimmickBuilder, self).run(simfile)
        
        gpath = os.path.join(os.path.dirname(simfile.filename), 'gimmicks.txt')
        
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
        for i, gimmick in enumerate(gimmicks):
            self.parse_gimmick(g, t, gimmicks, gimmick,
                          gimmicks[i + 1] if i + 1 < len(gimmicks) else None)
        
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
            simfile[timing.upper()] = Timing(','.join(tlist))
        
        simfile.save()