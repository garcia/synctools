#!/usr/bin/env python
from fractions import Fraction
import re
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from simfile import decimal_from_192nd, decimal_to_192nd, Timing
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

version = '0.2.0'
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


def parse_gimmick_position(pos):
    """
    Parses the portion of a gimmick line before the colon.
    
    Valid gimmick positions:
    
        * 32
        * 48-48.5
        * 69.5-70.75
    
    Invalid gimmick positions:
    
        * -13
        * 49x
        * 66-66
        * 42-
        * 12.5-12.25
        * 1-2-3
    """
    start, dash, end = pos.partition('-')
    
    # There should always be a starting beat
    try:
        start = float(start)
    except ValueError:
        raise ValueError('%r: invalid starting beat' % pos)
    
    # If there's a dash, it should be followed by a number
    if end:
        try:
            end = float(end)
        except ValueError:
            raise ValueError('%r: invalid ending beat' % pos)
        # It should also be greater than the starting position
        assert end > start, '%r: end > start' % pos
    return {
        'start': start,
        'end': end or None,
    }


def parse_gimmick_value(_val, defs):
    """
    Parses the portion of a gimmick line after the colon.
    
    Valid gimmick values:
    
        * bpm 174
        * bpm 140.425
        * stop 2
        * stop 1/3
        * stop .5
        * copy 36
        * 1/8 2x stutter
        * 2 .5x halfboost
        * 3/4 1.333x quarterbrake
    
    Invalid gimmick values:
    
        * bpm 120-140
        * bpm 140/2
        * stop 2-5
        * copy 12-16
        * copy 96/3
        * 1/8 2 stutter
        * 0.25 4x halfbrake
        * 10e2/200 1.5x midstutter
        * 1/2 4x undefined
        * 3/4 -1x quarterboost
        * -2 5x halfboost
    """
    val = _val.split()
    
    # BPM changes are of the form "bpm {new_bpm}"
    if val[0] == 'bpm':
        assert len(val) == 2, '%r: expecting exactly 2 components' % _val
        try:
            bpm = float(val[1])
        except ValueError:
            raise ValueError('%r: invalid BPM value' % _val)
        return {
            'type': 'bpm',
            'bpm': bpm,
        }
    
    # Constant stops are of the form "stop {beats}"
    if val[0] == 'stop':
        assert len(val) == 2, '%r: expecting exactly 2 components' % _val
        try:
            stop = float(Fraction(val[1]) * 4)
        except ValueError:
            raise ValueError('%r: stop length should be a fraction' % _val)
        assert stop > 0, '%r: stop length should be positive' % _val
        return {
            'type': 'stop',
            'len': stop,
        }
    
    # Copy gimmicks are of the form "copy {source}"
    if val[0] == 'copy':
        assert len(val) == 2, '%r: expecting exactly 2 components' % _val
        try:
            source = float(val[1])
        except ValueError:
            raise ValueError('%r: invalid copy source beat' % _val)
        return {
            'type': 'copy',
            'source': source,
        }
    
    # Normal gimmicks are of the form "{len} {mul} {def}"
    assert len(val) == 3, '%r: expecting exactly 3 components' % _val
    # Check len
    assert '.' not in val[0], '%r: len cannot be a decimal' % _val
    try:
        len_ = float(Fraction(val[0]) * 4)
    except ValueError:
        raise ValueError('%r: len should be a fraction' % _val)
    assert len_ > 0, '%r: len should be positive' % _val
    # Check mul
    assert val[1].lower().endswith('x'), '%r: mul should end with an x' % _val
    try:
        mul = float(val[1][:-1])
    except ValueError:
        raise ValueError('%r: mul should be a decimal number' % _val)
    assert mul > 0, '%r: mul should be positive' % _val
    # Check def
    def_ = defs.get(val[2])
    if not def_:
        def_ = builtin_gimmicks.get(val[2])
    if not def_:
        raise ValueError('%r: nonexistent definition' % _val)
    return {
        'type': 'normal',
        'len': len_,
        'mul': mul,
        'def': def_,
    }


def parse_gimmick_line(_pos, _val, defs):
    """
    Parses a gimmick line.
    
    There are some constraints not covered by parse_gimmick_position or
    parse_gimmick_value: copy gimmicks need an ending position, and the source
    range cannot overlap with the destination. BPM changes and constant stops
    cannot have an ending point.
    """
    pos = parse_gimmick_position(_pos)
    val = parse_gimmick_value(_val, defs)
    e = "%s: %s" % (_pos, _val)
    
    if val['type'] == 'copy':
        assert pos['end'], '%r: need an ending beat' % e
        assert val['source'] + (pos['end'] - pos['start']) <= pos['start'], \
            '%r: source region cannot overlap destination' % e
    
    elif val['type'] in ('bpm', 'stop'):
        assert not pos['end'], '%r: position should be one number' % e
    
    # Implicit ending point
    elif not pos['end']:
            pos['end'] = pos['start'] + val['len']
    
    return {
        'pos': pos,
        'val': val,
    }


def parse_gimmick_lines(lines, defs):
    gimmicks = []
    for line in lines:
        next_gimmick = parse_gimmick_line(line[0], line[1], defs)
        # Don't allow gimmicks to intersect
        if gimmicks:
            end = gimmicks[-1]['pos']['end']
            if end:
                assert next_gimmick['pos']['start'] >= end, \
                    '%r: intersects with the previous gimmick' % ' '.join(line)
        gimmicks.append(next_gimmick)
    return gimmicks


def add_timing(timing, timing_type, pos, val):
    pos = decimal_from_192nd(decimal_to_192nd(pos))
    val = decimal_from_192nd(val)
    if timing_type == 'BPMS' and timing['BPMS']:
        # Replace BPM change that coincides with the previous BPM change
        if timing[timing_type][-1][0] == pos:
            del timing[timing_type][-1]
        # Don't add BPM change that's equal to the previous BPM value
        if timing[timing_type][-1][1] == val:
            return
    timing[timing_type].append((pos, val))


def process_gimmick(gimmick, timing, current_bpm):
    # BPM changes
    if gimmick['val']['type'] == 'bpm':
        # Must have a BPM change on beat 0
        if not current_bpm:
            assert not gimmick['pos']['start'], 'Initial BPM must be on beat 0'
        add_timing(timing, 'BPMS', gimmick['pos']['start'],
                   gimmick['val']['bpm'])
        # Set current BPM to the BPM that was just parsed + inserted
        return timing['BPMS'][-1][1]
    
    # Past this point, current_bpm must be defined
    assert current_bpm, 'Need an initial BPM value'
    
    # Constant stops
    if gimmick['val']['type'] == 'stop':
        add_timing(timing, 'STOPS', gimmick['pos']['start'],
                   gimmick['val']['len'] * 60 / float(current_bpm))
        return
    
    # Copy gimmicks
    if gimmick['val']['type'] == 'copy':
        copy_length = gimmick['pos']['end'] - gimmick['pos']['start']
        source_start = gimmick['val']['source']
        source_end = source_start + copy_length
        for timing_type in ('BPMS', 'STOPS'):
            for beat, value in timing[timing_type]:
                if source_start <= beat < source_end:
                    timing[timing_type].append((
                        float(beat) + gimmick['pos']['start'] - source_start,
                        value
                    ))
            
            if timing_type == 'BPMS':
                add_timing(timing, 'BPMS', gimmick['pos']['end'], current_bpm)
        return
    
    # "Normal" gimmicks
    for timing_type in ('BPMS', 'STOPS'):
        if timing_type.lower() in gimmick['val']['def']:
            pos = gimmick['pos']['start']
            while (decimal_from_192nd(pos) <
                   decimal_from_192nd(gimmick['pos']['end'])):
                for loc, eq in gimmick['val']['def'][timing_type.lower()].iteritems():
                    val = eval(eq, {
                        '__builtins__': None,
                        'mul': gimmick['val']['mul'],
                        'len': gimmick['val']['len'],
                        'bpm': float(current_bpm),
                    })
                    add_timing(timing, timing_type,
                        pos + gimmick['val']['len'] * float(loc), val)
                pos += gimmick['val']['len']
            
            if timing_type == 'BPMS':
                add_timing(timing, 'BPMS', gimmick['pos']['end'], current_bpm)


def main(doc):
    # Initial timing data
    timing = {
        'BPMS': Timing(''),
        'STOPS': Timing(''),
    }
    
    defs = doc.get('definitions', {})
    
    # Stringify gimmick lines
    lines = [(str(pos), str(val)) for pos, val in doc['gimmicks'].iteritems()]
    
    # Parse and verify syntax
    gimmicks = parse_gimmick_lines(lines, defs)
    
    # Convert gimmicks to timing data
    current_bpm = None
    for gimmick in gimmicks:
        new_bpm = process_gimmick(gimmick, timing, current_bpm)
        if new_bpm:
            current_bpm = new_bpm
    
    return timing