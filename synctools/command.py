from decimal import *
import glob
import itertools
import logging
import os
import shutil
import sys
import traceback

from simfile import Simfile

__all__ = ['SynctoolsCommand', 'FieldInputs', 'FieldTypes', 'find_simfiles',
           'common_fields']


class SynctoolsCommand(object):
    
    title = ''
    fields = []
    backup_simfiles = False
    
    def __init__(self, options):
        self.log = logging.getLogger('synctools')
        self.log.info('Initializing %s...' % self.__class__.__name__)
        # Verify option types
        self.options = {}
        for key, value in options.items():
            field = [field for field in self.fields if key == field['name']]
            if not field:
                raise ValueError('Invalid field %r.' % key)
            field = field[0]
            try:
                parsed_value = field['type'](value)
            except Exception:
                raise TypeError('Invalid value %r for field %r.' %
                                (value, key))
            self.options[key] = parsed_value
    
    def backup(self, simfile):
        shutil.copy2(simfile.filename, simfile.filename + '~')
    
    def run(self, simfile):
        self.log.info('Processing %s...' % simfile.get('TITLE', '<untitled>'))
        if self.options.get('backup'):
            self.backup(simfile)
    
    def done(self):
        self.log.info('Done.')


class FieldInputs(object):
    text, boolean = xrange(2)


class FieldTypes(object):
    
    @staticmethod
    def yesno(value):
        if isinstance(value, bool):
            return value
        elif isinstance(value, basestring):
            first_letter = value[0].upper()
            if first_letter == 'Y':
                return True
            elif first_letter == 'N':
                return False
            raise ValueError('expecting Y or N')
        else:
            raise TypeError('expecting a string or boolean')
    
    @staticmethod
    def between(start, end, number_type=int):
        def _between(value):
            value = number_type(value)
            assert start <= value <= end, "%s <= value <= %s" % (start, end)
            return value
        return _between


common_fields = {
    'backup': {
        'name': 'backup',
        'title': 'Back up simfiles?',
        'input': FieldInputs.boolean,
        'default': True,
        'type': FieldTypes.yesno,
    },
    'global_offset': {
        'name': 'global_offset',
        'title': 'Global offset',
        'input': FieldInputs.text,
        'default': '0.000',
        'type': Decimal,
    },
}