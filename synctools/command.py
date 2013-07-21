from decimal import *
import glob
import itertools
import logging
import os
import shutil
import sys
import traceback

from simfile import Simfile

__all__ = ['SynctoolsCommand', 'FieldInputs', 'FieldTypes', 'common_fields']

class SynctoolsCommand(object):
    """
    Base class for synctools commands.

    The following attributes must be defined:

        * `title` -- a human-friendly title for the command
        * `description` -- a brief overview of what the command does
        * `fields` -- a list of option fields to be presented to the user

    Each option field is a dict containing the following items:

        * "name" -- the name the field will be given in self.options
        * "title" -- a human-friendly title for the field
        * "input" -- an attribute of synctools.command.FieldInputs
        * "default" -- the default value for the field
        * "type" -- a callable that returns a parsed object or raises an error

    Fields are parsed in __init__ and exposed through a dict at self.options. A
    handful of common fields are defined in synctools.command.common_fields:
    "backup", which backs up the input .sm files, and "global_offset", which
    gets the user's global offset and stores it as a Decimal object.

    Logging should be done through the Logger object at self.log.
    """
    
    title = ''
    description = ''
    fields = []
    
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
        """
        Backup the current simfile. If `backup` is set to True in the command's
        options, this is automatically called before each run().
        """
        shutil.copy2(simfile.filename, simfile.filename + '~')
    
    def run(self, simfile):
        """
        Process the current simfile. See `simfile's documentation
        <http://grantgarcia.org/simfile/>`_ for details on the simfile object.
        """
        self.log.info('Processing %s...' % simfile.get('TITLE', '<untitled>'))
        if self.options.get('backup'):
            self.backup(simfile)
    
    def done(self):
        """
        Clean up after all simfiles have been processed.
        """
        self.log.info('Done.')


class FieldInputs(object):
    """
    Exposes two attributes, `text` and `boolean`, that determine the input
    method for a field. In the synctools GUI, `text` creates a text input box
    and `boolean` creates a checkbox. The CLI ignores the input method.
    """
    text, boolean = xrange(2)


class FieldTypes(object):
    """
    Contains static methods that can be used as field types.
    """
    
    @staticmethod
    def yesno(value):
        """
        Returns the boolean for boolean arguments, or returns True or False for
        strings beginning with "Y" or "N", respectively. This should always be
        used in place of `bool` when defining checkbox fields.
        """
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
        """
        Returns a function that coerces its input value to `number_type` and
        asserts that it is between `start` and `end` inclusively.
        """
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
