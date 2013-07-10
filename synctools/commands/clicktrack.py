#!/usr/bin/env python
from decimal import Decimal
import math
import os
import random
import wave

from synctools import command

__all__ = ['ClickTrack']

class ClickTrack(command.SynctoolsCommand):
    
    title = 'Click track'
    description = 'generate a click track WAV file'
    fields = [
        {
            'name': 'metronome',
            'title': 'Metronome (noise on each beat)',
            'input': command.FieldInputs.boolean,
            'default': True,
            'type': command.FieldTypes.yesno,
        },
        {
            'name': 'taps',
            'title': 'Taps (sine bloop on each tap note)',
            'input': command.FieldInputs.boolean,
            'default': True,
            'type': command.FieldTypes.yesno,
        },
        {
            'name': 'mines',
            'title': 'Mines (square bloop on each mine)',
            'input': command.FieldInputs.boolean,
            'default': True,
            'type': command.FieldTypes.yesno,
        },
        {
            'name': 'amplitude',
            'title': 'Amplitude',
            'input': command.FieldInputs.text,
            'default': 0.8,
            'type': command.FieldTypes.between(0, 1, float),
        },
        command.common_fields['global_offset'],
    ]
    
    sample_rate = 44100
    
    def __init__(self, options):
        super(ClickTrack, self).__init__(options)
        # Generate sounds for the clicktrack
        amp = self.options['amplitude']
        self.sound = {
            'metronome': ''.join([
                chr(int(random.randrange(256) * a + 127 * (1 - a)))
                for a in [amp * b / 1024. for b in xrange(1024, 0, -1)]
            ]),
            'tap': ''.join([
                chr(int((math.sin(b / 4.) * 127 + 127) * a + 127 * (1 - a)))
                for a, b in [(amp * b / 1024., b) for b in xrange(1024, 0, -1)]
            ]),
            'mine': ''.join([
                chr(int((int(b / 128) % 2) * 255 * a + 127 * (1 - a)))
                for a, b in [(amp * b / 1024., b) for b in xrange(1024, 0, -1)]
            ]),
        }
    
    def get_hardest_chart(self):
        for diff in ('Challenge', 'Hard', 'Medium', 'Easy', 'Beginner', 'Edit'):
            for game in ('dance', 'pump', 'ez2'):
                for sd in ('single', 'double'):
                    try:
                        chart = self.simfile.charts.get(
                            difficulty=diff, stepstype=(game + '-' + sd)
                        )
                        return chart
                    except KeyError:
                        pass
    
    def current_bpm(self, beat):
        # Get all the BPMs that are before the current beat,
        # then return the last one
        return [value for t, value in self.simfile['BPMS'] if t <= beat][-1]
    
    def seconds_between_beats(self, start, end):
        bpm = self.current_bpm(start)
        pos = start
        seconds = 0.
        # Iterate over the timing events
        for event, t, value in self.timing_events:
            if start <= t < end:
                # Add the time elapsed between the previous and current beats,
                # which are guaranteed to have no timing events between them
                seconds += float(60 / bpm) * (t - pos)
                # Handle timing event
                if event == 'stop':
                    seconds += float(value)
                elif event == 'bpm':
                    bpm = value
                # Update position
                pos = t
            elif t >= end:
                # At this point there's no need to loop any further
                break
        # The last observed position will be less than the ending beat;
        # add the remaining time now
        seconds += float(60 / bpm) * (end - pos)
        return seconds
    
    def run(self, simfile):
        super(ClickTrack, self).run(simfile)
        self.simfile = simfile
        
        # Convert BPMS and STOPS to "timing events" - a combination of the two
        # event types in one list
        self.timing_events = [('bpm', t, v) for t, v in simfile['BPMS']]
        self.timing_events += [('stop', t, v) for t, v in simfile['STOPS']]
        self.timing_events.sort(key=lambda item: item[1])
        
        # Combine simfile's offset with the given global offset
        offset = Decimal(simfile['OFFSET']) + self.options['global_offset']
        
        # Retrieve the hardest chart, if possible
        chart = self.get_hardest_chart()
        if not chart:
            self.log.warning('Unable to find any dance, pump, or ez2 charts')
            # Get whatever the first chart is
            try:
                chart = simfile.charts[0]
            except IndexError:
                self.log.error('This simfile has no charts; aborting')
                return
        self.log.info('Using {stepstype} {difficulty} chart'.format(
            stepstype=chart.stepstype,
            difficulty=chart.difficulty,
        ))
        
        # Determine where to place clicks
        clicks = []
        if self.options['metronome']:
            for i in xrange(int(chart.notes[-1][0])):
                clicks.append((i, 'metronome'))
        for t, line in chart.notes:
            if any([c in '124' for c in line]) and self.options['taps']:
                clicks.append((t, 'tap'))
            if any([c == 'M' for c in line]) and self.options['mines']:
                clicks.append((t, 'mine'))
        clicks.sort(key=lambda item: item[0])
        self.log.debug('%s clicks loaded' % len(clicks))
        
        # Length of audio file = distance from beat 0 to last beat + padding
        audio_length = self.seconds_between_beats(0, clicks[-1][0]) + 1
        
        # Write click track to memory buffer
        self.log.info('Generating click track')
        buffer = bytearray('\x80' * int(self.sample_rate * audio_length))
        last_beat = second = 0
        for beat, sound in clicks:
            second += self.seconds_between_beats(last_beat, beat)
            sample = int(second * self.sample_rate)
            buffer[sample:sample+1024] = self.sound[sound]
            last_beat = beat
        
        # Compensate for offset
        offset_samples = int(offset * self.sample_rate)
        if offset_samples > 0:
            del buffer[:offset_samples]
        elif offset_samples < 0:
            buffer[0:0] = '\x80' * abs(offset_samples)
        
        # Write to WAV
        self.log.info('Writing WAV file')
        wav = os.path.join(os.path.dirname(simfile.filename), 'clicktrack.wav')
        clicks_h = wave.open(wav, 'w')
        clicks_h.setnchannels(1)
        clicks_h.setsampwidth(1)
        clicks_h.setframerate(self.sample_rate)
        clicks_h.writeframes(str(buffer))
        clicks_h.close()