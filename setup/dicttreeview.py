# vim:set et ts=4 sts=4:
# -*- coding: utf-8 -*-
#
# ibus-libpinyin - Intelligent Pinyin engine based on libpinyin for IBus
#
# Copyright (c) 2012 Peng Wu <alexepico@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import gettext
from gi.repository import GObject
from gi.repository import Gtk

_ = lambda x : gettext.gettext(x)


(
COLUMN_SENSITIVE,
COLUMN_PHRASE_INDEX,
COLUMN_DESCRIPTION,
COLUMN_ACTIVE
) = range(4)

dictionaries = \
    ((False, 1, _("GB Dictionary"), True),
     (True,  2, _("GBK Dictionary"), True))


class DictionaryTreeView(Gtk.TreeView):
    __gtype_name__ = 'DictionaryTreeView'
    __gproperties__ = {
        'dictionaries': (
            str,
            'dictionaries',
            'Enabled Dictionaries',
            "",
            GObject.PARAM_READWRITE
        )
    }

    def __init__(self):
        super(DictionaryTreeView, self).__init__()

        self.__changed = False

        self.set_headers_visible(True)

        self.__model = self.__create_model()
        self.set_model(self.__model)

        self.__add_columns()

    def __create_model(self):
        model = Gtk.ListStore(bool, int, str, bool)

        model.connect("row-changed", self.__emit_changed, "row-changed")

        for dict in dictionaries:
            iter = model.append()
            model.set(iter,
                      COLUMN_SENSITIVE, dict[COLUMN_SENSITIVE],
                      COLUMN_PHRASE_INDEX, dict[COLUMN_PHRASE_INDEX],
                      COLUMN_DESCRIPTION, dict[COLUMN_DESCRIPTION],
                      COLUMN_ACTIVE, dict[COLUMN_ACTIVE])

        return model

    def __add_columns(self):
        # column for toggles
        renderer = Gtk.CellRendererToggle()
        renderer.connect('toggled', self.__active_toggled, self.__model)
        column = Gtk.TreeViewColumn('Active', renderer, active=COLUMN_ACTIVE, sensitive=COLUMN_SENSITIVE)
        self.append_column(column)

        # column for description
        render = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn('Description', render, text=COLUMN_DESCRIPTION)
        self.append_column(column)

    def __active_toggled(self, cell, path, model):
        # get toggled iter
        iter = model.get_iter((int(path),))
        active = model.get_value(iter, COLUMN_ACTIVE)

        # toggle active
        active = not active

        # save value
        model.set(iter, COLUMN_ACTIVE, active)

        # mark changed
        self.__changed = True

    def __emit_changed(self, *args):
        if self.__changed:
            self.__changed = False
            self.notify("dictionaries")

    def get_dictionaries(self):
        dicts = []
        for row in self.__model:
            if (not row[COLUMN_SENSITIVE]):
                continue;
            if (row[COLUMN_ACTIVE]):
                dicts.append(row[COLUMN_PHRASE_INDEX])
        return ';'.join(dicts)

    def set_dictionaries(self, dicts):
        # clean dictionaries
        for row in self.__model:
            if not row[COLUMN_SENSITIVE]:
                continue
            row[COLUMN_ACTIVE] = False

        if not dicts:
            self.__emit_changed()
            return

        for dict in dicts.split(";"):
            dict = int(dict)
            for row in self.__model:
                if not row[COLUMN_SENSITIVE]:
                    continue
                if dict == row[COLUMN_PHRASE_INDEX]:
                    row[COLUMN_ACTIVE] = True
        self.__emit_changed()

    def do_get_property(self, prop):
        if prop.name == 'dictionaries':
            return self.get_dictionaries()
        else:
            raise AttributeError, 'unknown property %s' % prop.name

    def do_set_property(self, prop, value):
        if prop.name == "dictionaries":
            self.set_dictionaries(value)
        else:
            raise AttributeError, 'unknown property %s' % prop.name


GObject.type_register(DictionaryTreeView)


if __name__ == "__main__":
    tree = DictionaryTreeView()
    tree.set_dictionaries("")
    w = Gtk.Window()
    w.add(tree)
    w.show_all()
    Gtk.main()