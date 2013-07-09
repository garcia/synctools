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
           'main', 'common_fields']


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
    def between(start, end, number_type=int):
        def _between(value):
            value = number_type(value)
            assert start <= value <= end, "%s <= value <= %s" % (start, end)
            return value
        return _between


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
    # Set up logging
    log = logging.getLogger('synctools')
    log.setLevel(logging.INFO)
    log.addHandler(logging.StreamHandler())
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