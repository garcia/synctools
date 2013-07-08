#!/usr/bin/env python
import codecs
from decimal import *
import logging
import os
import sys

import commands

__all__ = ['AdjustOffset']

class AdjustOffset(commands.SynctoolsCommand):
    
    name = 'Adjust offset'
    fields = [
        {
            'name': 'amount',
            'title': 'Seconds to add',
            'input': commands.InputTypes.text,
            'default': '0.000',
            'type': Decimal,
        },
        commands.common_fields['backup'],
    ]
    
    def run(self, simfile):
        super(AdjustOffset, self).run(simfile)
        old_offset = simfile['OFFSET']
        new_offset = Decimal(old_offset) + Decimal(self.options['amount'])
        self.log.info('%s -> %s' % (old_offset, new_offset))
        simfile['OFFSET'] = new_offset
        simfile.save()


if __name__ == '__main__':
    commands.main(AdjustOffset)