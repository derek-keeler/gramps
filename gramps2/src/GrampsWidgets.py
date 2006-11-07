#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2006  Donald N. Allingham
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

# $Id$

import cgi
import os
import cPickle as pickle
from gettext import gettext as _

#-------------------------------------------------------------------------
#
# GTK/Gnome modules
#
#-------------------------------------------------------------------------
import gobject
import gtk
import pango

import AutoComp
import DateHandler
import DateEdit
import const
import Errors
from DdTargets import DdTargets

_lock_path = os.path.join(const.image_dir, 'stock_lock.png')
_lock_open_path = os.path.join(const.image_dir, 'stock_lock-open.png')

hand_cursor = gtk.gdk.Cursor(gtk.gdk.HAND2)
def realize_cb(widget):
    widget.window.set_cursor(hand_cursor)

class LinkLabel(gtk.EventBox):

    def __init__(self, label, func, handle):
        gtk.EventBox.__init__(self)
        self.orig_text = cgi.escape(label[0])
        self.gender = label[1]
        text = '<span underline="single">%s</span>' % self.orig_text
        
        self.label = gtk.Label(text)
        self.label.set_use_markup(True)
        self.label.set_alignment(0, 0.5)

        hbox = gtk.HBox()
        hbox.pack_start(self.label, False, False, 0)
        if label[1]:
            hbox.pack_start(GenderLabel(label[1]), False, False, 4)
        self.add(hbox)
        
        self.connect('button-press-event', func, handle)
        self.connect('enter-notify-event', self.enter_text, handle)
        self.connect('leave-notify-event', self.leave_text, handle)
        self.connect('realize', realize_cb)

    def set_padding(self, x, y):
        self.label.set_padding(x, y)
        
    def enter_text(self, obj, event, handle):
        text = '<span foreground="blue" underline="single">%s</span>' % self.orig_text
        self.label.set_text(text)
        self.label.set_use_markup(True)

    def leave_text(self, obj, event, handle):
        text = '<span underline="single">%s</span>' % self.orig_text
        self.label.set_text(text)
        self.label.set_use_markup(True)

class IconButton(gtk.Button):

    def __init__(self, func, handle, icon=gtk.STOCK_EDIT,
                 size=gtk.ICON_SIZE_MENU):
        gtk.Button.__init__(self)
        image = gtk.Image()
        image.set_from_stock(icon, size)
        image.show()
        self.add(image)
        self.set_relief(gtk.RELIEF_NONE)
        self.show()

        if func:
            self.connect('button-press-event', func, handle)

class WarnButton(gtk.Button):
    def __init__(self):
        gtk.Button.__init__(self)
        image = gtk.Image()

        # Some versions of FreeBSD don't seem to have STOCK_INFO
        try:
            image.set_from_stock(gtk.STOCK_INFO, gtk.ICON_SIZE_MENU)
        except:
            image.set_from_stock(gtk.STOCK_DIALOG_INFO, gtk.ICON_SIZE_MENU)
            
        image.show()
        self.add(image)
        self.set_relief(gtk.RELIEF_NONE)
        self.show()
        self.func = None
        self.hide()

    def on_clicked(self, func):
        self.connect('button-press-event', self._button_press)
        self.func = func

    def _button_press(self, obj, event):
        if event.type == gtk.gdk.BUTTON_PRESS and event.button == 1:
            self.func(obj)

class SimpleButton(gtk.Button):

    def __init__(self, image, func):
        gtk.Button.__init__(self)
        self.set_relief(gtk.RELIEF_NONE)
        self.add(gtk.image_new_from_stock(image, gtk.ICON_SIZE_BUTTON))
        self.connect('clicked', func)
        self.show()
        
class LinkBox(gtk.HBox):

    def __init__(self, link, button):
        gtk.HBox.__init__(self)
        self.set_spacing(6)
        self.pack_start(link, False)
        self.pack_start(button, False)
        self.show()

class EditLabel(gtk.HBox):
    def __init__(self, text):
        gtk.HBox.__init__(self)
        label = BasicLabel(text)
        self.pack_start(label, False)
        self.pack_start(gtk.image_new_from_stock(gtk.STOCK_EDIT, 
                                                 gtk.ICON_SIZE_MENU), False)
        self.set_spacing(4)
        self.show_all()

class BasicLabel(gtk.Label):

    def __init__(self, text):
        gtk.Label.__init__(self, text)
        self.set_alignment(0, 0.5)
        self.show()

class GenderLabel(gtk.Label):

    def __init__(self, text):
        gtk.Label.__init__(self, text)
        self.set_alignment(0, 0.5)
        if os.sys.platform == "win32":
            pangoFont = pango.FontDescription('Arial')
            self.modify_font(pangoFont)
        self.show()

class MarkupLabel(gtk.Label):

    def __init__(self, text):
        gtk.Label.__init__(self, text)
        self.set_alignment(0, 0.5)
        self.set_use_markup(True)
        self.show_all()

class DualMarkupLabel(gtk.HBox):

    def __init__(self, text, alt):
        gtk.HBox.__init__(self)
        label = gtk.Label(text)
        label.set_alignment(0, 0.5)
        label.set_use_markup(True)

        self.pack_start(label, False, False, 0)
        b = GenderLabel(alt)
        b.set_use_markup(True)
        self.pack_start(b, False, False, 4)
        self.show()
        
class IntEdit(gtk.Entry):
    """An gtk.Edit widget that only allows integers."""
    
    def __init__(self):
	gtk.Entry.__init__(self)

        self._signal = self.connect("insert_text", self.insert_cb)

    def insert_cb(self, widget, text, length, *args):        
        # if you don't do this, garbage comes in with text
        text = text[:length]
        pos = widget.get_position()
        # stop default emission
        widget.emit_stop_by_name("insert_text")
        gobject.idle_add(self.insert, widget, text, pos)

    def insert(self, widget, text, pos):
        if len(text) > 0 and text.isdigit():            
            # the next three lines set up the text. this is done because we
            # can't use insert_text(): it always inserts at position zero.
            orig_text = widget.get_text()            
            new_text = orig_text[:pos] + text + orig_text[pos:]
            # avoid recursive calls triggered by set_text
            widget.handler_block(self._signal)
            # replace the text with some new text
            widget.set_text(new_text)
            widget.handler_unblock(self._signal)
            # set the correct position in the widget
            widget.set_position(pos + len(text))

class TypeCellRenderer(gtk.CellRendererCombo):

    def __init__(self, values):
        gtk.CellRendererCombo.__init__(self)

        model = gtk.ListStore(str, int)
        for key in values:
            model.append(row=[values[key], key])
        self.set_property('editable', True)
        self.set_property('model', model)
        self.set_property('text-column', 0)

class PrivacyButton:

    def __init__(self, button, obj, readonly=False):
        self.button = button
        self.button.connect('toggled', self._on_toggle)
        self.tooltips = gtk.Tooltips()
        self.obj = obj
        self.set_active(obj.get_privacy())
        self.button.set_sensitive(not readonly)

    def set_sensitive(self, val):
        self.button.set_sensitive(val)

    def set_active(self, val):
        self.button.set_active(val)
        self._on_toggle(self.button)

    def get_active(self):
        return self.button.get_active()

    def _on_toggle(self, obj):
        child = obj.child
        if child:
            obj.remove(child)
        image = gtk.Image()
        if obj.get_active():
#            image.set_from_icon_name('stock_lock', gtk.ICON_SIZE_MENU)
            image.set_from_file(_lock_path)
            self.tooltips.set_tip(obj, _('Record is private'))
            self.obj.set_privacy(True)
        else:
#            image.set_from_icon_name('stock_lock-open', gtk.ICON_SIZE_MENU)
            image.set_from_file(_lock_open_path)
            self.tooltips.set_tip(obj, _('Record is public'))
            self.obj.set_privacy(False)
        image.show()
        obj.add(image)

class MonitoredCheckbox:

    def __init__(self, obj, button, set_val, get_val, on_toggle=None):
        self.button = button
        self.button.connect('toggled', self._on_toggle)
        self.on_toggle = on_toggle
        self.obj = obj
        self.set_val = set_val
        self.get_val = get_val
        self.obj.set_active(get_val())

    def _on_toggle(self, obj):
        self.set_val(obj.get_active())
        if self.on_toggle:
            self.on_toggle(self.get_val())
        
class MonitoredEntry:

    def __init__(self, obj, set_val, get_val, read_only=False,
                 autolist=None, changed=None):
        self.obj = obj
        self.set_val = set_val
        self.get_val = get_val
        self.changed = changed

        if get_val():
            self.obj.set_text(get_val())
        self.obj.connect('changed', self._on_change)
        self.obj.set_editable(not read_only)

        if autolist:
            AutoComp.fill_entry(obj,autolist)

    def reinit(self, set_val, get_val):
        self.set_val = set_val
        self.get_val = get_val
        self.update()

    def set_text(self, text):
        self.obj.set_text(text)
        
    def connect(self, signal, callback):
        self.obj.connect(signal, callback)

    def _on_change(self, obj):
        self.set_val(unicode(obj.get_text()))
        if self.changed:
            self.changed(obj)

    def force_value(self, value):
        self.obj.set_text(value)

    def get_value(self, value):
        return unicode(self.obj.get_text())

    def enable(self, value):
        self.obj.set_sensitive(value)
        self.obj.set_editable(value)

    def grab_focus(self):
        self.obj.grab_focus()

    def update(self):
        if self.get_val():
            self.obj.set_text(self.get_val())

class MonitoredText:

    def __init__(self, obj, set_val, get_val, read_only=False):
        self.buf = obj.get_buffer()
        self.set_val = set_val
        self.get_val = get_val

        if get_val():
            self.buf.set_text(get_val())
        self.buf.connect('changed', self.on_change)
        obj.set_editable(not read_only)

    def on_change(self, obj):
        s, e = self.buf.get_bounds()
        self.set_val(unicode(self.buf.get_text(s, e, False)))

class MonitoredType:

    def __init__(self, obj, set_val, get_val, mapping, custom, readonly=False,
                 custom_values=None):
        self.set_val = set_val
        self.get_val = get_val

        self.obj = obj

        val = get_val()
        if val:
            default = val[0]
        else:
            default = None

        self.sel = AutoComp.StandardCustomSelector(
            mapping, obj, custom, default, additional=custom_values)

        self.set_val(self.sel.get_values())
        self.obj.set_sensitive(not readonly)
        self.obj.connect('changed', self.on_change)

    def reinit(self, set_val, get_val):
        self.set_val = set_val
        self.get_val = get_val
        self.update()

    def update(self):
        if self.get_val():
            self.sel.set_values(self.get_val())

    def on_change(self, obj):
        self.set_val(self.sel.get_values())

class MonitoredDataType:

    def __init__(self, obj, set_val, get_val, readonly=False,
                 custom_values=None):
        
        self.set_val = set_val
        self.get_val = get_val

        self.obj = obj

        val = get_val()

        if val:
            default = int(val)
        else:
            default = None

        self.sel = AutoComp.StandardCustomSelector(
            get_val().get_map(),
            obj,
            get_val().get_custom(),
            default,
            additional=custom_values)

        self.sel.set_values((int(get_val()),str(get_val())))
        self.obj.set_sensitive(not readonly)
        self.obj.connect('changed', self.on_change)

    def reinit(self, set_val, get_val):
        self.set_val = set_val
        self.get_val = get_val
        self.update()

    def fix_value(self, value):
        if value[0] == self.get_val().get_custom():
            return value
        else:
            return (value[0],'')

    def update(self):
        val = self.get_val()
        if type(val) == tuple :
            self.sel.set_values(val)
        else:
            self.sel.set_values((int(val),str(val)))

    def on_change(self, obj):
        value = self.fix_value(self.sel.get_values())
        self.set_val(value)

class MonitoredMenu:

    def __init__(self, obj, set_val, get_val, mapping,
                 readonly=False, changed=None):
        self.set_val = set_val
        self.get_val = get_val

        self.changed = changed
        self.obj = obj

        self.change_menu(mapping)
        self.obj.connect('changed', self.on_change)
        self.obj.set_sensitive(not readonly)

    def force(self, value):
        self.obj.set_active(value)

    def change_menu(self, mapping):
        self.data = {}
        self.model = gtk.ListStore(str, int)
        index = 0
        for t, v in mapping:
            self.model.append(row=[t, v])
            self.data[v] = index
            index += 1
        self.obj.set_model(self.model)
        self.obj.set_active(self.data.get(self.get_val(),0))

    def on_change(self, obj):
        self.set_val(self.model.get_value(obj.get_active_iter(), 1))
        if self.changed:
            self.changed()

class MonitoredStrMenu:

    def __init__(self, obj, set_val, get_val, mapping, readonly=False):
        self.set_val = set_val
        self.get_val = get_val

        self.obj = obj
        self.model = gtk.ListStore(str)
        
        if len(mapping) > 20:
            self.obj.set_wrap_width(3)

        self.model.append(row=[''])
        index = 0
        self.data = ['']

        default = get_val()
        active = 0
        
        for t, v in mapping:
            self.model.append(row=[v])
            self.data.append(t)
            index += 1
            if t == default:
                active = index
            
        self.obj.set_model(self.model)
        self.obj.set_active(active)
        self.obj.connect('changed', self.on_change)
        self.obj.set_sensitive(not readonly)

    def on_change(self, obj):
        self.set_val(self.data[obj.get_active()])

class MonitoredDate:

    def __init__(self, field, button, value, uistate, track, readonly=False):
        self.date = value
        self.date_check = DateEdit.DateEdit(
            self.date, field, button, uistate, track)
        field.set_editable(not readonly)
        button.set_sensitive(not readonly)
            
        field.set_text(DateHandler.displayer.display(self.date))

class PlaceEntry:
    """
    handles the selection of a existing or new Place
    """
    def __init__(self, dbstate, uistate, track, obj, set_val,
                 get_val, add_del, share):
        
        self.obj = obj
        self.add_del = add_del
        self.share = share
        self.dbstate = dbstate
        self.db = dbstate.db
        self.get_val = get_val
        self.set_val = set_val
        self.uistate = uistate
        self.track = track

        self.obj.drag_dest_set(gtk.DEST_DEFAULT_ALL, [DdTargets.PLACE_LINK.target()], 
                               gtk.gdk.ACTION_COPY)
        self.obj.connect('drag_data_received', self.drag_data_received)

        if get_val():
            self.set_button(True)
            p = self.db.get_place_from_handle(self.get_val())
            name = "%s [%s]" % (p.get_title(),p.gramps_id)
        else:
            name = u""
            self.set_button(False)

        if self.db.readonly:
            self.add_del.set_sensitive(False)
            self.share.set_sensitive(False)
        else:
            self.add_del.set_sensitive(True)
            self.share.set_sensitive(True)

        self.add_del.connect('clicked', self.add_del_clicked)
        self.share.connect('clicked', self.share_clicked)
        
        if not self.db.readonly and not name:
            obj.set_text("<i>%s</i>" % _('Drag and drop or use buttons to add or select'))
            obj.set_use_markup(True)
        else:
            obj.set_text(name)

    def after_edit(self, place):
        name = "%s [%s]" % (place.get_title(),place.gramps_id)
        self.obj.set_text(name)

    def add_del_clicked(self, obj):
        if self.get_val():
            self.set_val(None)
            self.obj.set_text(u'')
            self.set_button(False)
        else:
            from RelLib import Place
            from Editors import EditPlace

            place = Place()
            try:
                EditPlace(self.dbstate, self.uistate, self.track,
                          place, self.place_added)
            except Errors.WindowActiveError:
                pass

    def drag_data_received(self, widget, context, x, y, selection, info, time):
        (drag_type, idval, obj, val) = pickle.loads(selection.data)
        
        data = self.db.get_place_from_handle(obj)
        self.place_added(data)
        
    def place_added(self, data):
        self.set_val(data.handle)
        self.obj.set_text("%s [%s]" % (data.get_title(),data.gramps_id))
        self.set_button(True)

    def share_clicked(self, obj):
        if self.get_val():
            from Editors import EditPlace
            
            place = self.db.get_place_from_handle(self.get_val())
            try:
                EditPlace(self.dbstate, self.uistate, self.track, place,
                          self.after_edit)
            except Errors.WindowActiveError:
                pass
        else:
            from Selectors import selector_factory
            cls = selector_factory('Place')
            select = cls(self.dbstate, self.uistate, self.track)
            place = select.run()
            if place:
                self.place_added(place)

    def set_button(self, use_add):
        for i in self.add_del.get_children():
            self.add_del.remove(i)
        for i in self.share.get_children():
            self.share.remove(i)

        if use_add:
            image = gtk.Image()
            image.set_from_stock(gtk.STOCK_REMOVE,gtk.ICON_SIZE_BUTTON)
            image.show()
            self.add_del.add(image)
            image = gtk.Image()
            image.set_from_stock(gtk.STOCK_EDIT,gtk.ICON_SIZE_BUTTON)
            image.show()
            self.share.add(image)
        else:
            image = gtk.Image()
            image.set_from_stock(gtk.STOCK_ADD,gtk.ICON_SIZE_BUTTON)
            image.show()
            self.add_del.add(image)
            image = gtk.Image()
            image.set_from_stock(gtk.STOCK_INDEX,gtk.ICON_SIZE_BUTTON)
            image.show()
            self.share.add(image)
