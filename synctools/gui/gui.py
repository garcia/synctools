import codecs
import glob
import os
import sys
import urllib

import pygtk
pygtk.require('2.0')
import gtk
import gtk.glade
from simfile.msd import MSDParser

from synctools import commands
from synctools.commands.all_commands import all_commands

class SynctoolsGUI:
    
    file_uri_target = 80
    path_strip = '\r\n\x00'
    gladefile = os.path.join(os.path.dirname(__file__), 'synctools.glade')
    
    def delete_event(self, widget, *args):
        gtk.main_quit()
        return False
    
    # Adding simfiles
    
    def uri_to_path(self, uri):
        path = ''
        for protocol in ('file:\\\\\\', 'file://', 'file:'):
            if uri.startswith(protocol):
                path = uri[len(protocol):]
                break
        path = urllib.url2pathname(path)
        path = path.strip(SynctoolsGUI.path_strip)
        return path
    
    def add_simfiles(self, paths):
        simfile_paths = []
        for path in paths:
            simfile_paths.extend(commands.find_simfiles(path))
        simfile_list = self.glade.get_object('simfiles')
        for path in simfile_paths:
            # Don't re-add simfiles that were already added
            already_added = False
            for existing_simfile in simfile_list:
                if path == existing_simfile[-1]:
                    already_added = True
                    break
            if already_added:
                break
            # Get metadata from the simfiles (without creating Simfile objects)
            metadata = {'TITLE': None, 'ARTIST': None, 'CREDIT': None}
            metadata_missing = len(metadata)
            with codecs.open(path, 'r', encoding='utf-8') as msdfile:
                for param in MSDParser(msdfile):
                    if param[0].upper() in metadata:
                        metadata[param[0].upper()] = ':'.join(param[1:])
                        metadata_missing -= 1
                        if not metadata_missing: break
                    # We're probably not going to find any useful
                    # parameters once we're down to the charts
                    elif param[0].upper() == 'NOTES':
                        break
            simfile_list.append([metadata['TITLE'], metadata['ARTIST'],
                                  metadata['CREDIT'], path])
    
    def drag_files(self, widget, context, x, y, selection, target_type, timestamp):
        if target_type == SynctoolsGUI.file_uri_target:
            # Normalize URIs
            uris = selection.data.strip(SynctoolsGUI.path_strip)
            paths = []
            for uri in uris.split():
                paths.append(self.uri_to_path(uri))
            self.add_simfiles(paths)
    
    # Menu items
    
    def menu_file_open(self, menuitem):
        self.glade.get_object('choose_simfiles').show_all()
    
    def menu_help_about(self, menuitem):
        self.glade.get_object('about').show_all()
    
    # File chooser
    
    def choose_simfiles_response(self, dialog, response):
        dialog.hide()
        # Anything but the Open button was pressed
        if response != 1:
            return
        # Open button was pressed
        self.add_simfiles(dialog.get_filenames())
    
    # About dialog
    
    def about_response(self, dialog, response):
        dialog.hide()
    
    # Run buttons
    
    def run_button(self, button, command):
        print command
    
    # Initialization
    
    def __init__(self):
        # Set up Glade
        self.glade = gtk.Builder()
        self.glade.add_from_file(SynctoolsGUI.gladefile)
        self.glade.connect_signals(self)
        
        # Populate command combo box
        notebook = self.glade.get_object('command_notebook')
        self.optionfields = {}
        # Create a page for each command
        for command in all_commands:
            # Save fields for future access
            self.optionfields[command.__name__] = current_fields = {}
            # Each tab is a Table with the first column used for labels
            # and the second column for inputs.  There's one extra row that
            # contains a "Run" button.
            page = gtk.Table(rows=len(command.fields)+1, columns=2)
            for f, field in enumerate(command.fields):
                page.attach(gtk.Label(field['title']), 0, 1, f, f + 1)
                if field['input'] == commands.FieldInputs.text:
                    # Add text field
                    field_widget = gtk.Entry()
                    field_widget.set_text(str(field['default']))
                elif field['input'] == commands.FieldInputs.boolean:
                    # Add checkbox / check button
                    field_widget = gtk.CheckButton()
                    if field['default']:
                        field_widget.set_active(True)
                page.attach(field_widget, 1, 2, f, f + 1)
                current_fields[field['name']] = field_widget
            # Add "Run" button
            run_button = gtk.Button(command.title)
            run_button.connect('clicked', self.run_button, command.__name__)
            page.attach(run_button, 0, 2, f + 1, f + 2, 0, 0, 0, 5)
            notebook.append_page(page, gtk.Label(command.title))
        
        # Parse any file arguments
        self.add_simfiles(sys.argv[1:])
        
        # Set up main window
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