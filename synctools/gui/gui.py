#!/usr/bin/env python
import glob
import os
import urllib

import pygtk
pygtk.require('2.0')
import gtk
import gtk.glade

from simfile.msd import MSDParser

class SynctoolsGUI:
    
    file_uri_target = 80
    path_strip = '\r\n\x00'
    gladefile = 'synctools.glade'
    
    def delete_event(self, widget, event, data=None):
        gtk.main_quit()
        return False
    
    def get_path(self, uri):
        path = ''
        for protocol in ('file:\\\\\\', 'file://', 'file:'):
            if uri.startswith(protocol):
                path = uri[len(protocol):]
                break
        path = urllib.url2pathname(path)
        path = path.strip(SynctoolsGUI.path_strip)
        return path
    
    def discover_simfiles(self, path):
        if os.path.isfile(path):
            if os.path.splitext(path)[1] == '.sm':
                return [path]
        elif os.path.isdir(path):
            paths = []
            for child in glob.iglob(os.path.join(path, '*')):
                paths.extend(self.discover_simfiles(child))
            return paths
        return []
    
    def drag_files(self, widget, context, x, y, selection, target_type, timestamp):
        if target_type == SynctoolsGUI.file_uri_target:
            uris = selection.data.strip(SynctoolsGUI.path_strip)
            simfiles = []
            for uri in uris.split():
                simfiles.extend(self.discover_simfiles(self.get_path(uri)))
            for simfile in simfiles:
                print simfile
    
    def __init__(self):
        self.glade = gtk.Builder()
        self.glade.add_from_file(SynctoolsGUI.gladefile)
        self.glade.connect_signals(self)
        
        self.window = self.glade.get_object('synctools')
        self.window.drag_dest_set(
            gtk.DEST_DEFAULT_MOTION |
            gtk.DEST_DEFAULT_HIGHLIGHT |
            gtk.DEST_DEFAULT_DROP,
            [('text/uri-list', 0, SynctoolsGUI.file_uri_target)],
            gtk.gdk.ACTION_COPY
        )
        self.window.show_all()
    
    def main(self):
        gtk.main()


if __name__ == "__main__":
   gui = SynctoolsGUI()
   gui.main()