#!/usr/bin/env python
import codecs
import logging
import os
import sys
from decimal import *

import synctools

__all__ = ['distribute']

def distribute(simfile):
    log = logging.getLogger('synctools')
    cfg = synctools.get_config()
    filename_split = os.path.splitext(simfile.filename)
    # Add ITG offset
    offset_param = simfile.get('OFFSET')
    offset = Decimal(offset_param[1])
    offset2 = offset + Decimal("0.009")
    offset_param[1] = str(offset2)
    # Write to ITG simfile
    simfile.filename = '%s itg%s' % filename_split
    simfile.save()
    # Remove file references
    for identifier in ('BANNER', 'BACKGROUND', 'CDTITLE', 'LYRICSPATH',
            'BGCHANGES', 'FGCHANGES'):
        try:
            simfile.get(identifier)
            simfile.set(identifier, '')
        except KeyError:
            pass
    # Write to r21 simfile
    simfile.filename = '%s r21%s' % filename_split
    simfile.save()


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))
    synctools.main_iterator(distribute, sys.argv[1:])