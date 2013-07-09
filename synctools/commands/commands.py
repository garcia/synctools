from decimal import *
import glob
import itertools
import logging
import os
import shutil
import sys
import traceback

from simfile import Simfile

__all__ = ['SynctoolsCommand', 'InputTypes', 'find_simfiles', 'main', 'common_fields']


class SynctoolsCommand(object):
    
    title = ''
    fields = []
    backup_simfiles = False
    
    def __init__(self, options):
        self.log = logging.getLogger('synctools')
        self.options = options
    
    def backup(self, simfile):
        shutil.copy2(simfile.filename, simfile.filename + '~')
    
    def run(self, simfile):
        if 'backup' in self.options and self.options['backup']:
            self.backup(simfile)
    
    def done(self):
        pass


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
    def float_between(start, end):
        def _float_between(value):
            value = float(value)
            assert start <= value <= end, "%s <= value <= %s" % (start, end)
            return value
        return _float_between


def find_simfiles(path):
    if os.path.isfile(path):
        if os.path.splitext(path)[1] == '.sm':
            return [path]
    elif os.path.isdir(path):
        paths = []
        for child in glob.iglob(os.path.join(path.replace('[', '[[]'), '*')):
            paths.extend(find_simfiles(child))
        return paths
    return []


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


def main(Command):
    # Get options from command line
    options = {}
    for field in Command.fields:
        while True:
            # Determine default value to show in brackets
            if field['input'] == FieldInputs.boolean:
                default_string = 'Y/n' if field['default'] else 'y/N'
            else:
                default_string = field['default']
            # Get option value from user
            value = raw_input('{title} [{default}]: '.format(
                title=field['title'], default=default_string))
            if not value:
                value = field['default']
            try:
                options[field['name']] = field['type'](value)
                break
            except Exception:
                print traceback.format_exc().splitlines()[-1]
        else:
            raise ValueError('invalid input')
    # Initialize command
    command = Command(options)
    # Find simfiles
    simfiles = [find_simfiles(arg) for arg in sys.argv[1:]]
    for simfile in itertools.chain(*simfiles):
        command.run(Simfile(simfile))
    command.done()


common_fields = {
    'backup': {
        'name': 'backup',
        'title': 'Backup simfiles?',
        'input': FieldInputs.boolean,
        'default': True,
        'type': yesno,
    },
    'global_offset': {
        'name': 'global_offset',
        'title': 'Global offset',
        'input': FieldInputs.text,
        'default': '0.000',
        'type': Decimal,
    },
}


# This is no longer used, but remains for future reference
config_structure = {
    'synctools': {
        'verbosity': str,
        'global_offset': float,
        'delayed_exit': bool,
        'extensions': str,
        'backup': bool,
        'backup_extension': str,
    },
    'clicktrack': {
        'metronome': bool,
        'first_beat': bool,
        'taps': bool,
        'mines': bool,
        'amplitude': float,
    },
    'adjustoffset': {
        'amount': str,
    },
    'formatter': {
        'in_file': str,
        'out_file': str,
    },
    'magicstops': {
        'margin': float,
    },
    'rename': {
        'keep_other_files': bool,
        'directory': str,
        'simfile': str,
        'music': str,
        'background': str,
        'banner': str,
        'cdtitle': str,
        'lyricspath': str,
    },
    'resynthesize': {
        'input': str,
        'output': str,
    },
    'patch': {
        'backup': bool,
        'patched_length': int,
    },
}