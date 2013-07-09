from inspect import isclass

import synctools.commands

module_names = ['adjustoffset', 'clicktrack', 'fixstops', 'gimmickbuilder', 'patch']
modules = [__import__(__package__ + '.' + name, fromlist=name) for name in module_names]

all_commands = []
for module in modules:
    for attr in module.__dict__.values():
        if (isclass(attr) and
                issubclass(attr, synctools.commands.SynctoolsCommand) and
                attr is not synctools.commands.SynctoolsCommand):
            all_commands.append(attr)