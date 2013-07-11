import codecs
import glob
import logging
import os
import pprint
import sys
import time
import traceback
import urllib

import pygtk
pygtk.require('2.0')
import gtk
import gtk.glade

from simfile import Simfile
from simfile.msd import MSDParser

from synctools import __version__, command, settings, utils

class GtkTextViewHandler(logging.Handler):
    
    def __init__(self, tv):
        logging.Handler.__init__(self)
        self.tv = tv
        self.tbf = tv.get_buffer()
        self.formatter = None

    def emit(self, record):
        try:
            msg = self.format(record)
            fs  = "%s\n"
            self.tbf.insert(self.tbf.get_end_iter(), fs % msg)
            self.tv.scroll_to_iter(self.tbf.get_end_iter(), 0.0, False, 0, 0)
        except:
            self.handleError(record)


class SynctoolsGUI:
    
    file_uri_target = 80
    path_strip = '\r\n\x00'
    gladefile = os.path.join(os.path.dirname(__file__), 'synctools.glade')
    
    def delete_event(self, widget, *args):
        gtk.main_quit()
        return False
    
    def hide_on_delete(self, widget, event):
        widget.hide()
        return True
    
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
            simfile_paths.extend(utils.find_simfiles(path))
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
    
    # Managing selected simfiles
    
    def simfile_tree_delete_selected(self):
        simfile_tree = self.glade.get_object('simfile_tree')
        model, pathlist = simfile_tree.get_selection().get_selected_rows()
        # Iters need to be retrieved before altering the model, otherwise
        # they become invalid as paths are removed
        for iter in [model.get_iter(path) for path in pathlist]:
            model.remove(iter)
    
    def simfile_tree_key_press(self, tree, event):
        keyname = gtk.gdk.keyval_name(event.keyval)
        if keyname == 'Delete':
            self.simfile_tree_delete_selected()
    
    def simfile_tree_button_press(self, tree, event):
        # Right click
        if event.button == 3:
            simfile_tree = self.glade.get_object('simfile_tree')
            if simfile_tree.get_selection().get_selected_rows()[1]:
                self.glade.get_object('simfile_tree_right_click').popup(
                    None, None, None, 3, int(time.time())
                )
                return True
    
    def simfile_tree_right_click_delete(self, menuitem):
        self.simfile_tree_delete_selected()
    
    # Run buttons
    
    def run_button(self, button, command_name):
        # Get command class
        for cn, Command in utils.get_commands().items():
            if command_name == cn:
                break
        
        # Get option fields
        options = {}
        for field, widget in self.optionfields[command_name].items():
            field_dict = [f for f in Command.fields if f['name'] == field][0]
            if field_dict['input'] == command.FieldInputs.boolean:
                options[field] = widget.get_active()
            elif field_dict['input'] == command.FieldInputs.text:
                options[field] = widget.get_text()
        
        # Create output window
        self.glade.get_object('output').show_all()
        self.log.debug(str(options))
        
        # Process the simfiles
        simfile_list = self.glade.get_object('simfiles')
        try:
            command_instance = Command(options)
        except Exception:
            self.log.error(traceback.format_exc().splitlines()[-1])
        for item in simfile_list:
            while gtk.events_pending():
                gtk.main_iteration_do(False)
            try:
                command_instance.run(Simfile(item[-1]))
            except Exception:
                self.log.error(traceback.format_exc().splitlines()[-1])
        command_instance.done()
        self.log.info('')
    
    # Output window
    
    def output_clear(self, button):
        self.glade.get_object('output_textview').get_buffer().set_text('')
    
    def output_close(self, button):
        self.glade.get_object('output').hide()
    
    # Initialization
    
    def __init__(self):
        # Set up Glade
        self.glade = gtk.Builder()
        self.glade.add_from_file(SynctoolsGUI.gladefile)
        self.glade.connect_signals(self)
        
        # Set up logging
        self.log = logging.getLogger('synctools')
        self.log.setLevel(logging.INFO)
        self.log.addHandler(GtkTextViewHandler(
            self.glade.get_object('output_textview')
        ))
        
        # Populate command combo box
        notebook = self.glade.get_object('command_notebook')
        self.optionfields = {}
        # Create a page for each command
        for cn, Command in utils.get_commands().items():
            # Save fields for future access
            self.optionfields[cn] = current_fields = {}
            # Each tab is a Table with the first column used for labels and the
            # second column for inputs.  There's an extra row at the top for
            # the description and one at the bottom for the "Run" button.
            page = gtk.Table(rows=len(Command.fields)+2, columns=2)
            for f, field in enumerate(Command.fields):
                page.attach(gtk.Label(field['title']), 0, 1, f + 1, f + 2)
                if field['input'] == command.FieldInputs.text:
                    # Add text field
                    field_widget = gtk.Entry()
                    field_widget.set_text(str(field['default']))
                elif field['input'] == command.FieldInputs.boolean:
                    # Add checkbox / check button
                    field_widget = gtk.CheckButton()
                    if field['default']:
                        field_widget.set_active(True)
                page.attach(field_widget, 1, 2, f + 1, f + 2)
                current_fields[field['name']] = field_widget
            # Add description
            page.attach(gtk.Label(Command.description), 0, 2, 0, 1)
            # Add "Run" button
            run_button = gtk.Button(Command.title)
            run_button.connect('clicked', self.run_button, cn)
            page.attach(run_button, 0, 2, f + 2, f + 3, 0, 0, 0, 5)
            notebook.append_page(page, gtk.Label(Command.title))
        
        # Allow selection of multiple simfiles
        selection = self.glade.get_object('simfile_tree').get_selection()
        selection.set_mode(gtk.SELECTION_MULTIPLE)
        
        # Parse any file arguments
        self.add_simfiles(sys.argv[1:])
        
        # Add version number to about window
        self.glade.get_object('about').set_comments('v' + __version__)
        
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
        gtk.main()