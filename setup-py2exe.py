from distutils.core import setup
from distutils.sysconfig import get_python_lib
import os
import shutil
import sys

import py2exe

# Find GTK+ installation path
__import__('gtk')
m = sys.modules['gtk']
gtk_base_path = m.__path__[0]

# Find zlib.pyc
get_python_lib()

# Find installed commands
from synctools.commands.all_commands import module_names
modules = ['synctools/commands/%s.py' % name for name in module_names]

setup(
    name='synctools',
    description='Tools to assist synchronizing StepMania simfiles',
    version=__import__('synctools').__version__,
    packages=['synctools'],
    windows=[{'script': 'synctools-gui.py'}],
    options={
        'py2exe': {
            'packages': 'encodings',
            'includes': 'cairo, pango, pangocairo, atk, gobject, gtk, gio, wave, yaml',
            'skip_archive': True,
            'bundle_files': 3,
        },
    },
    data_files=[
        ('synctools/commands', modules),
        ('synctools/gui',  ['synctools/gui/synctools.glade']),
        os.path.join(gtk_base_path, '..', 'runtime', 'bin', 'libxml2-2.dll'),
    ],
)

for subdir in ('etc', 'lib', 'share'):
    shutil.copytree(os.path.join('include', subdir), os.path.join('dist', subdir))