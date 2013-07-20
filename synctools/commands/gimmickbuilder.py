#!/usr/bin/env python
from fractions import Fraction
import os
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from simfile import decimal_from_192nd, Timing
import yaml
import yaml.constructor
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from synctools import command

__all__ = ['GimmickBuilder']

class OrderedDictYAMLLoader(yaml.Loader):
    """
    A YAML loader that loads mappings into ordered dictionaries.
    """

    def __init__(self, *args, **kwargs):
        yaml.Loader.__init__(self, *args, **kwargs)

        self.add_constructor(u'tag:yaml.org,2002:map', type(self).construct_yaml_map)
        self.add_constructor(u'tag:yaml.org,2002:omap', type(self).construct_yaml_map)

    def construct_yaml_map(self, node):
        data = OrderedDict()
        yield data
        value = self.construct_mapping(node)
        data.update(value)

    def construct_mapping(self, node, deep=False):
        if isinstance(node, yaml.MappingNode):
            self.flatten_mapping(node)
        else:
            raise yaml.constructor.ConstructorError(None, None,
                'expected a mapping node, but found %s' % node.id, node.start_mark)

        mapping = OrderedDict()
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                hash(key)
            except TypeError, exc:
                raise yaml.constructor.ConstructorError('while constructing a mapping',
                    node.start_mark, 'found unacceptable key (%s)' % exc, key_node.start_mark)
            value = self.construct_object(value_node, deep=deep)
            mapping[key] = value
        return mapping


class GimmickBuilder(command.SynctoolsCommand):
    
    title = 'Gimmick builder'
    description='convert a gimmicks.txt file into BPM changes and stops'
    fields = [
        {
            'name': 'initialize',
            'title': 'Create gimmicks.txt skeleton?',
            'input': command.FieldInputs.boolean,
            'default': False,
            'type': command.FieldTypes.yesno,
        },
        command.common_fields['backup'],
    ]
    
    latest_version = '0.2.0'
    initial_data = """version: {version}

gimmicks:
    0: bpm {bpm}

# Add your definitions and gimmicks here
# See http://grantgarcia.org/synctools/ for more details"""
    
    def run(self, simfile):
        super(GimmickBuilder, self).run(simfile)
        
        gpath = os.path.join(os.path.dirname(simfile.filename), 'gimmicks.txt')
        
        # Initialize new gimmicks file
        if self.options['initialize']:
            if os.path.exists(gpath):
                self.log.error('Not overwriting existing file %s' % gpath)
                self.log.error('Aborting.')
                return
            with open(gpath, 'w') as gfile:
                gfile.write(self.initial_data.format(
                    version=self.latest_version,
                    bpm=simfile['BPMS'][0][1]
                ))
            return
        
        # Parse gimmicks.txt
        self.log.info('Loading gimmicks from file %r' % gpath)
        with open(gpath, 'r') as gfile:
            g = yaml.load(gfile, Loader=OrderedDictYAMLLoader)
        
        # Determine which parser to use
        if 'version' in g:
            ver = g['version']
        else:
            self.log.warn('No version found in file; assuming 0.1.0')
            ver = '0.1.0'
        module_name = 'version_%s' % ver.replace('.', '_')
        try:
            module = __import__('%s.gimmickbuilder_versions.%s' %
                                    (__package__, module_name),
                                fromlist=module_name)
        except ImportError:
            self.log.error('GimmickBuilder version %s is unavailable' % ver)
            return
        
        # Start parsing
        timing = module.main(g)
        
        # Insert returned data into simfile
        simfile['BPMS'] = timing['BPMS']
        simfile['STOPS'] = timing['STOPS']
        simfile.save()