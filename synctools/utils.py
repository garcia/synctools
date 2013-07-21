from inspect import isclass
import glob
import os

from synctools import settings
from synctools.command import SynctoolsCommand

def get_commands():
    """
    Get a mapping of commands' names to the command classes themselves.

    Only modules defined in synctools.settings.COMMANDS are searched for
    Command subclasses. Command names are their class names, not their `title`
    attributes.
    """
    if hasattr(get_commands, 'commands'):
        return get_commands.commands
    get_commands.commands = {}
    for module in [__import__('synctools.commands.' + name, fromlist=name)
                   for name in settings.COMMANDS]:
        for name, attr in module.__dict__.items():
            if (isclass(attr) and issubclass(attr, SynctoolsCommand) and
                    attr is not SynctoolsCommand):
                get_commands.commands[name] = attr
    return get_commands.commands

def find_simfiles(path):
    """
    Recursively search the given path for .sm files. Returns a list of paths.
    """
    if os.path.isfile(path):
        if os.path.splitext(path)[1] == '.sm':
            return [path]
    elif os.path.isdir(path):
        paths = []
        for child in glob.iglob(os.path.join(path.replace('[', '[[]'), '*')):
            paths.extend(find_simfiles(child))
        return paths
    return []
