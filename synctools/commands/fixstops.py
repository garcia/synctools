#!/usr/bin/env python
from simfile import Timing

from synctools import command

__all__ = ['FixStops']

class FixStops(command.SynctoolsCommand):
    
    title = 'Fix stops'
    description = 'mitigate the effects of imprecise rounding in stop values'
    fields = [command.common_fields['backup']]
    margin = 0.001
    
    def run(self, simfile):
        super(FixStops, self).run(simfile)
        # Retrieve the needed data
        bpms = simfile['BPMS']
        stops = simfile['STOPS']
        # Fix stop values
        # 'residue' contains the number of seconds by which the chart is early
        drift = 0
        residue = 0.0
        new_stops = []
        while stops:
            stop_start, stop_value = (float(s) for s in stops.pop(0))
            # Get current BPM
            bpm_start = 0.0
            for bpm_s, bpm_v in bpms:
                if bpm_s > bpm_start and bpm_s <= stop_start:
                    bpm_start, bpm_value = float(bpm_s), float(bpm_v)
            # Really big BPM values should be decreased until they're reasonable
            while bpm_value > 625:
                bpm_value /= 2
            # Determine real stop value
            stop_real = stop_192nd = 60 / bpm_value / 48
            corrected_stop = False
            while stop_real <= stop_value + self.margin:
                # Found a good approximation yet?
                if stop_real >= stop_value - self.margin:
                    self.log.debug('Real value of stop at %s is %s' % (stop_start, stop_real))
                    residue += stop_value - stop_real
                    self.log.debug('Current residue is %s' % residue)
                    # Chart is more than half a ms early
                    if residue > .0005:
                        self.log.debug('Chart is now early; decreasing stop value')
                        residue -= .001
                        stop_value -= .001
                        drift -= 1
                    # Chart is at least half a ms late
                    elif residue <= -.0005:
                        self.log.debug('Chart is now late; increasing stop value')
                        residue += .001
                        stop_value += .001
                        drift += 1
                    corrected_stop = True
                    break
                stop_real += stop_192nd
            if not corrected_stop:
                self.log.warn('Could not correct stop at %s' % stop_start)
            new_stops.append((round(stop_start, 3), stop_value))
        # Reassemble stops data
        simfile['STOPS'] = Timing(','.join(
            ['%s=%s' % new_stop for new_stop in new_stops]
        ))
        simfile.save()
        self.log.info('Corrected about %s milliseconds of drift' % abs(drift))