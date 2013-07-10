#!/usr/bin/env python
from decimal import *

from synctools import command

__all__ = ['AdjustOffset']

class AdjustOffset(command.SynctoolsCommand):
    
    title = 'Adjust offset'
    description = 'tweak offsets for hardware delay and/or personal preference'
    fields = [
        {
            'name': 'amount',
            'title': 'Seconds to add',
            'input': command.FieldInputs.text,
            'default': '0.000',
            'type': Decimal,
        },
        command.common_fields['backup'],
    ]
    
    def run(self, simfile):
        super(AdjustOffset, self).run(simfile)
        old_offset = simfile['OFFSET']
        new_offset = Decimal(old_offset) + Decimal(self.options['amount'])
        self.log.info('%s -> %s' % (old_offset, new_offset))
        simfile['OFFSET'] = new_offset
        simfile.save()