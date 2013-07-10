from distutils.core import setup
from distutils.sysconfig import get_python_lib
import os
import shutil
import sys

import py2exe

from synctools import __version__
from synctools.settings import COMMANDS

# Find GTK+ installation path
__import__('gtk')
m = sys.modules['gtk']
gtk_base_path = m.__path__[0]

# Find zlib.pyc
get_python_lib()

# Find installed commands
modules = ['synctools/commands/%s.py' % name for name in COMMANDS]

setup(
    name='synctools',
    description='synctools v'+__version__,
    version=__version__,
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

dist_synctools = os.path.join('dist', 'synctools')
if os.path.exists(dist_synctools):
    shutil.rmtree(dist_synctools)
shutil.copytree('synctools', dist_synctools)

for subdir in ('etc', 'lib', 'share'):
    dist_path = os.path.join('dist', subdir)
    if not os.path.exists(dist_path):
        print 'copying', subdir
        shutil.copytree(os.path.join('include', subdir), dist_path)