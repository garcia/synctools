import argparse
import itertools
import logging
import os
import sys

from simfile import Simfile

from synctools import __version__, command, settings, utils

def main():
    # Set up logging
    log = logging.getLogger('synctools')
    log.setLevel(logging.INFO)
    log.addHandler(logging.StreamHandler())
    
    # Set up argument parsing
    parser = argparse.ArgumentParser()
    parser.add_argument('command', metavar='cmd',
                        help='the command to run')
    parser.add_argument('paths', metavar='path', nargs='+',
                        help='paths to simfiles and/or simfile directories')
    parser.add_argument('-v', '--version', action='version',
                        version=__version__)
    parser.add_argument('-l', '--ls', action='store_true',
                        help='list installed commands and exit')
    parser.add_argument('-d', '--defaults', action='store_true',
                        help="don't prompt for input; just use default values")
    
    # argparse doesn't know how to handle print-and-exit options outside of
    # --help and --version, so this has to be done before the arguments are
    # parsed.
    if len(sys.argv) >= 2 and sys.argv[1] in ('-l', '--ls'):
        for command_name, Command in utils.get_commands().items():
            print '{name}: {description}'.format(
                name=command_name,
                description=Command.description
            )
        sys.exit()
    
    args = parser.parse_args()
    
    # Make sure input files exist
    for path in args.paths:
        if not os.path.exists(path):
            parser.error('%r: no such file or directory' % path)
    
    # Determine the command to run
    commands = utils.get_commands()
    keys = commands.keys()
    # Map lowercase keys to the original CamelCase versions
    keys_ci = dict(zip((k.lower() for k in keys), keys))
    command_normalized = keys_ci.get(args.command.lower(), None)
    if not command_normalized:
        parser.error('invalid command %r' % args.command)
    Command = commands[command_normalized]
    
    # Get options from command line
    options = {}
    for field in Command.fields:
        while True:
            if args.defaults:
                # Use the default value
                value = None
            else:
                # Determine default value to show in brackets
                if field['input'] == command.FieldInputs.boolean:
                    default_string = 'Y/n' if field['default'] else 'y/N'
                else:
                    default_string = field['default']
                # Request user input
                value = raw_input('{title} [{default}]: '.format(
                    title=field['title'], default=default_string))
            if not value:
                value = field['default']
            try:
                options[field['name']] = field['type'](value)
                break
            except Exception:
                print traceback.format_exc().splitlines()[-1]
    
    command_instance = Command(options)
    
    # Find simfiles
    simfiles = [utils.find_simfiles(arg) for arg in args.paths]
    for simfile in itertools.chain(*simfiles):
        command_instance.run(Simfile(simfile))
    command_instance.done()