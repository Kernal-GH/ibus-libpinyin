# vim:set et ts=4 sts=4:
# -*- coding: utf-8 -*-
#
# ibus-libpinyin - Intelligent Pinyin engine based on libpinyin for IBus
#
# Copyright (c) 2008-2010 Peng Huang <shawn.p.huang@gmail.com>
# Copyright (c) 2010 BYVoid <byvoid1@gmail.com>
# Copyright (c) 2011-2012 Peng Wu <alexepico@gmail.com>
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

from __future__ import print_function

import gettext

import locale
import os
import sys

from gi import require_version as gi_require_version
gi_require_version('GLib', '2.0')
gi_require_version('Gtk', '3.0')
gi_require_version('IBus', '1.0')

from gi.repository import GLib

# set_prgname before importing other modules to show the name in warning
# messages when import modules are failed. E.g. Gtk.
GLib.set_prgname('ibus-setup-libpinyin')

from gi.repository import Gtk
from gi.repository import IBus

import config
from dicttreeview import DictionaryTreeView
from shortcuteditor import ShortcutEditor

locale.setlocale(locale.LC_ALL, "")
localedir = os.getenv("IBUS_LOCALEDIR")
pkgdatadir = os.getenv("IBUS_PKGDATADIR") or "."
gettext.install('ibus-libpinyin', localedir)

class PreferencesDialog:
    def __init__(self, engine):
        self.__bus = IBus.Bus()
        self.__config = self.__bus.get_config()
        self.__builder = Gtk.Builder()
        self.__builder.set_translation_domain("ibus-libpinyin")
        self.__builder.add_from_file("ibus-libpinyin-preferences.ui")
        self.__dialog = self.__builder.get_object("dialog")
        self.__init_pages()
        
        if engine == "libpinyin":
            self.__config_namespace = "engine/libpinyin"
            self.__values = dict(self.__config.get_values(self.__config_namespace))
            self.__init_general()
            self.__init_pinyin()
            self.__init_fuzzy()
            self.__init_dictionary()
            self.__init_user_data()
            self.__init_shortcut()
            self.__init_about()
        elif engine == "libbopomofo":
            self.__config_namespace = "engine/libbopomofo"
            self.__values = dict(self.__config.get_values(self.__config_namespace))
            self.__init_general()
            self.__init_bopomofo()
            self.__init_fuzzy()
            self.__init_dictionary()
            #self.__init_user_data()
            self.__init_shortcut()
            self.__init_about()
            self.__convert_fuzzy_pinyin_to_bopomofo()

        else:
            print("Error: Unknown Engine")
            exit()

        self.__pages.set_current_page(0)

    def __init_pages(self):
        self.__pages = self.__builder.get_object("pages")
        self.__page_general = self.__builder.get_object("pageGeneral")
        self.__page_pinyin_mode = self.__builder.get_object("pagePinyinMode")
        self.__page_bopomofo_mode = self.__builder.get_object("pageBopomofoMode")
        self.__page_fuzzy = self.__builder.get_object("pageFuzzy")
        self.__page_dictionary = self.__builder.get_object("pageDictionary")
        self.__page_user_data = self.__builder.get_object("pageUserData")
        self.__page_shortcut = self.__builder.get_object("pageShortcut")
        self.__page_about = self.__builder.get_object("pageAbout")

        self.__page_general.hide()
        self.__page_pinyin_mode.hide()
        self.__page_bopomofo_mode.hide()
        self.__page_fuzzy.hide()
        self.__page_dictionary.hide()
        self.__page_user_data.hide()
        self.__page_about.hide()

    def __init_general(self):
        # page General
        self.__page_general.show()

        # init state
        self.__init_chinese = self.__builder.get_object("InitChinese")
        self.__init_english = self.__builder.get_object("InitEnglish")
        self.__init_full = self.__builder.get_object("InitFull")
        self.__init_half = self.__builder.get_object("InitHalf")
        self.__init_full_punct = self.__builder.get_object("InitFullPunct")
        self.__init_half_punct = self.__builder.get_object("InitHalfPunct")
        self.__init_simp = self.__builder.get_object("InitSimplifiedChinese")
        self.__init_trad = self.__builder.get_object("InitTraditionalChinese")

        # UI
        self.__lookup_table_page_size = self.__builder.get_object("LookupTablePageSize")
        self.__lookup_table_orientation = self.__builder.get_object("LookupTableOrientation")

        self.__dynamic_adjust = self.__builder.get_object("DynamicAdjust")
        self.__remember_every_input = self.__builder.get_object("RememberEveryInput")

        # read values
        self.__init_chinese.set_active(self.__get_value("initchinese", True))
        self.__init_full.set_active(self.__get_value("initfull", False))
        self.__init_full_punct.set_active(self.__get_value("initfullpunct", True))
        self.__init_simp.set_active(self.__get_value("initsimplifiedchinese", True))

        self.__lookup_table_orientation.set_active(self.__get_value("lookuptableorientation", 0))
        self.__lookup_table_page_size.set_value(self.__get_value("lookuptablepagesize", 5))

        self.__dynamic_adjust.set_active(self.__get_value("dynamicadjust", True))
        self.__remember_every_input.set_active(self.__get_value("remembereveryinput", False))
        # connect signals
        self.__init_chinese.connect("toggled", self.__toggled_cb, "initchinese")
        self.__init_full.connect("toggled", self.__toggled_cb, "initfull")
        self.__init_full_punct.connect("toggled", self.__toggled_cb, "initfullpunct")
        self.__init_simp.connect("toggled", self.__toggled_cb, "initsimplifiedchinese")
        self.__dynamic_adjust.connect("toggled", self.__toggled_cb, "dynamicadjust")
        self.__remember_every_input.connect("toggled", self.__toggled_cb, "remembereveryinput")

        def __lookup_table_page_size_changed_cb(adjustment):
            self.__set_value("lookuptablepagesize", int(adjustment.get_value()))

        def __lookup_table_orientation_changed_cb(widget):
            self.__set_value("lookuptableorientation", widget.get_active())

        self.__lookup_table_orientation.connect("changed", __lookup_table_orientation_changed_cb)
        self.__lookup_table_page_size.connect("value-changed", __lookup_table_page_size_changed_cb)

    def __init_pinyin(self):
        # page
        self.__page_pinyin_mode.show()
        
        # pinyin
        self.__full_pinyin = self.__builder.get_object("FullPinyin")
        self.__incomplete_pinyin = self.__builder.get_object("IncompletePinyin")
        self.__double_pinyin = self.__builder.get_object("DoublePinyin")
        self.__double_pinyin_schema = self.__builder.get_object("DoublePinyinSchema")
        # self.__double_pinyin_schema_label = self.__builder.get_object("labelDoublePinyinSchema")
        self.__double_pinyin_show_raw = self.__builder.get_object("DoublePinyinShowRaw")
        self.__double_pinyin_show_raw.hide ()

        # read value
        self.__incomplete_pinyin.set_active(self.__get_value("incompletepinyin", True))
        self.__full_pinyin.set_active(not self.__get_value("doublepinyin", False))
        self.__double_pinyin_schema.set_active(self.__get_value("doublepinyinschema", 0))
        if self.__full_pinyin.get_active():
            # self.__incomplete_pinyin.set_sensitive(True)
            self.__double_pinyin_schema.set_sensitive(False)
            # self.__double_pinyin_schema_label.set_sensitive(False)
            self.__double_pinyin_show_raw.set_sensitive(False)
        else:
            # self.__incomplete_pinyin.set_sensitive(False)
            self.__double_pinyin_schema.set_sensitive(True)
            # self.__double_pinyin_schema_label.set_sensitive(True)
            self.__double_pinyin_show_raw.set_sensitive(True)

        def __double_pinyin_toggled_cb(widget):
            val = widget.get_active()
            self.__set_value("doublepinyin", val)
            self.__double_pinyin_schema.set_sensitive(val)
            # self.__double_pinyin_schema_label.set_sensitive(val)
            self.__double_pinyin_show_raw.set_sensitive(val)

        def __double_pinyin_schema_changed_cb(widget):
            self.__set_value("doublepinyinschema", widget.get_active())

        # connect signals
        self.__double_pinyin.connect("toggled", __double_pinyin_toggled_cb)
        self.__incomplete_pinyin.connect("toggled", self.__toggled_cb, "incompletepinyin")
        self.__double_pinyin_schema.connect("changed", __double_pinyin_schema_changed_cb)
        self.__double_pinyin_show_raw.connect("toggled", self.__toggled_cb, "doublepinyinshowraw")

        self.__init_input_custom()
        self.__init_correct_pinyin()

    def __init_bopomofo(self):
        # page Bopomodo Mode
        self.__page_bopomofo_mode.show()

        # bopomofo mode
        self.__incomplete_bopomofo = self.__builder.get_object("IncompleteBopomofo")
        self.__bopomofo_keyboard_mapping = self.__builder.get_object("BopomofoKeyboardMapping")
        
        # selection mode
        self.__select_keys = self.__builder.get_object("SelectKeys")
        self.__guide_key = self.__builder.get_object("GuideKey")
        self.__auxiliary_select_key_f = self.__builder.get_object("AuxiliarySelectKey_F")
        self.__auxiliary_select_key_kp = self.__builder.get_object("AuxiliarySelectKey_KP")

        # other
        self.__enter_key = self.__builder.get_object("CommitFirstCandidate")

        # read value
        self.__bopomofo_keyboard_mapping.set_active(self.__get_value("bopomofokeyboardmapping", 0))
        self.__incomplete_bopomofo.set_active(self.__get_value("incompletepinyin", False))
        self.__select_keys.set_active(self.__get_value("selectkeys", 0))
        self.__guide_key.set_active(self.__get_value("guidekey", 1))
        self.__auxiliary_select_key_f.set_active(self.__get_value("auxiliaryselectkey_f", 1))
        self.__auxiliary_select_key_kp.set_active(self.__get_value("auxiliaryselectkey_kp", 1))
        self.__enter_key.set_active(self.__get_value("enterkey", True))

        # connect signals
        def __bopomofo_keyboard_mapping_changed_cb(widget):
            self.__set_value("bopomofokeyboardmapping", widget.get_active())
        def __select_keys_changed_cb(widget):
            self.__set_value("selectkeys", widget.get_active())

        self.__bopomofo_keyboard_mapping.connect("changed", __bopomofo_keyboard_mapping_changed_cb)
        self.__incomplete_bopomofo.connect("toggled", self.__toggled_cb, "incompletepinyin")
        self.__select_keys.connect("changed", __select_keys_changed_cb)
        self.__guide_key.connect("toggled", self.__toggled_cb, "guidekey")
        self.__auxiliary_select_key_f.connect("toggled", self.__toggled_cb, "auxiliaryselectkey_f")
        self.__auxiliary_select_key_kp.connect("toggled", self.__toggled_cb, "auxiliaryselectkey_kp")
        self.__enter_key.connect("toggled", self.__toggled_cb, "enterkey")

    def __init_input_custom(self):
        # others
        self.__shift_select_candidate = self.__builder.get_object("ShiftSelectCandidate")
        self.__minus_equal_page = self.__builder.get_object("MinusEqualPage")
        self.__comma_period_page = self.__builder.get_object("CommaPeriodPage")
        self.__auto_commit = self.__builder.get_object("AutoCommit")

        # read values
        self.__shift_select_candidate.set_active(self.__get_value("shiftselectcandidate", False))
        self.__minus_equal_page.set_active(self.__get_value("minusequalpage", True))
        self.__comma_period_page.set_active(self.__get_value("commaperiodpage", True))
        self.__auto_commit.set_active(self.__get_value("autocommit", False))

        # connect signals
        self.__shift_select_candidate.connect("toggled", self.__toggled_cb, "shiftselectcandidate")
        self.__minus_equal_page.connect("toggled", self.__toggled_cb, "minusequalpage")
        self.__comma_period_page.connect("toggled", self.__toggled_cb, "commaperiodpage")
        self.__auto_commit.connect("toggled", self.__toggled_cb, "autocommit")

    def __init_correct_pinyin(self):
        # auto correct
        self.__correct_pinyin = self.__builder.get_object("CorrectPinyin")
        self.__correct_pinyin_widgets = [
            ("CorrectPinyin_GN_NG", True),
            ("CorrectPinyin_MG_NG", True),
            ("CorrectPinyin_IOU_IU", True),
            ("CorrectPinyin_UEI_UI", True),
            ("CorrectPinyin_UEN_UN", True),
            ("CorrectPinyin_UE_VE", True),
            ("CorrectPinyin_V_U", True),
            ("CorrectPinyin_ON_ONG", True),
        ]

        def __correct_pinyin_toggled_cb(widget):
            val = widget.get_active()
            for w in self.__correct_pinyin_widgets:
                self.__builder.get_object(w[0]).set_sensitive(val)
        self.__correct_pinyin.connect("toggled", __correct_pinyin_toggled_cb)

        # init value
        self.__correct_pinyin.set_active(self.__get_value("correctpinyin", True))
        for name, defval in self.__correct_pinyin_widgets:
            widget = self.__builder.get_object(name)
            widget.set_active(self.__get_value(name.lower(), defval))

        self.__correct_pinyin.connect("toggled", self.__toggled_cb, "correctpinyin")
        for name, defval in self.__correct_pinyin_widgets:
            widget = self.__builder.get_object(name)
            widget.connect("toggled", self.__toggled_cb, name.lower())

    def __init_fuzzy(self):
        # page Fuzzy
        self.__page_fuzzy.show()

        # fuzzy pinyin
        self.__fuzzy_pinyin = self.__builder.get_object("FuzzyPinyin")
        self.__fuzzy_pinyin_widgets = [
            ("FuzzyPinyin_C_CH", True),
            ("FuzzyPinyin_Z_ZH", True),
            ("FuzzyPinyin_S_SH", True),
            ("FuzzyPinyin_L_N", True),
            ("FuzzyPinyin_F_H", True),
            ("FuzzyPinyin_L_R", False),
            ("FuzzyPinyin_G_K", False),
            ("FuzzyPinyin_AN_ANG", True),
            ("FuzzyPinyin_EN_ENG", True),
            ("FuzzyPinyin_IN_ING", True),
        ]

        def __fuzzy_pinyin_toggled_cb(widget):
            val = widget.get_active()
            for w in self.__fuzzy_pinyin_widgets:
                self.__builder.get_object(w[0]).set_sensitive(val)
        self.__fuzzy_pinyin.connect("toggled", __fuzzy_pinyin_toggled_cb)

        # init value
        self.__fuzzy_pinyin.set_active(self.__get_value("fuzzypinyin", False))
        for name, defval in self.__fuzzy_pinyin_widgets:
            widget = self.__builder.get_object(name)
            widget.set_active(self.__get_value(name.lower(), defval))

        self.__fuzzy_pinyin.connect("toggled", self.__toggled_cb, "fuzzypinyin")
        for name, defval in self.__fuzzy_pinyin_widgets:
            widget = self.__builder.get_object(name)
            widget.connect("toggled", self.__toggled_cb, name.lower())

    def __convert_fuzzy_pinyin_to_bopomofo(self):
        options = [
            ("FuzzyPinyin_C_CH",   "ㄘ <=> ㄔ"),
            ("FuzzyPinyin_Z_ZH",   "ㄗ <=> ㄓ"),
            ("FuzzyPinyin_S_SH",   "ㄙ <=> ㄕ"),
            ("FuzzyPinyin_L_N",    "ㄌ <=> ㄋ"),
            ("FuzzyPinyin_F_H",    "ㄈ <=> ㄏ"),
            ("FuzzyPinyin_L_R",    "ㄌ <=> ㄖ"),
            ("FuzzyPinyin_G_K",    "ㄍ <=> ㄎ"),
            ("FuzzyPinyin_AN_ANG", "ㄢ <=> ㄤ"),
            ("FuzzyPinyin_EN_ENG", "ㄣ <=> ㄥ"),
            ("FuzzyPinyin_IN_ING", "ㄧㄣ <=> ㄧㄥ"),
        ]

        for name, label in options:
            self.__builder.get_object(name).set_label(label)


    def __init_dictionary(self):
        # page Dictionary
        self.__page_dictionary.show()

        # dictionary tree view
        self.__dict_treeview = self.__builder.get_object("Dictionaries")
        self.__dict_treeview.show()
        self.__dict_treeview.set_dictionaries(self.__get_value("dictionaries", "2"))

        def __notified_dicts_cb(self, param, dialog):
            dialog.__set_value("dictionaries", self.get_dictionaries())

        # connect notify signal
        self.__dict_treeview.connect("notify::dictionaries", __notified_dicts_cb, self)

    def __init_user_data(self):
        #page User Data
        self.__page_user_data.show()

        self.__frame_lua_script = self.__builder.get_object("frameLuaScript")
        path = os.path.join(pkgdatadir, 'user.lua')
        if not os.access(path, os.R_OK):
            self.__frame_lua_script.hide()

        self.__edit_lua = self.__builder.get_object("EditLua")
        self.__edit_lua.connect("clicked", self.__edit_lua_cb)

        self.__import_dictionary = self.__builder.get_object("ImportDictionary")
        self.__import_dictionary.connect("clicked", self.__import_dictionary_cb)

        self.__export_dictionary = self.__builder.get_object("ExportDictionary")
        self.__export_dictionary.connect("clicked", self.__export_dictionary_cb)

        self.__clear_user_data = self.__builder.get_object("ClearUserData")
        self.__clear_user_data.connect("clicked", self.__clear_user_data_cb, "user")
        self.__clear_all_data = self.__builder.get_object("ClearAllData")
        self.__clear_all_data.connect("clicked", self.__clear_user_data_cb, "all")

    def __edit_lua_cb(self, widget):
        import shutil
        path = os.path.join(GLib.get_user_config_dir(), "ibus", "libpinyin")
        os.path.exists(path) or os.makedirs(path)
        path = os.path.join(path, "user.lua")
        if not os.path.exists(path):
            src = os.path.join(pkgdatadir, "user.lua")
            shutil.copyfile(src, path)
        os.system("xdg-open %s" % path)

    def __import_dictionary_cb(self, widget):
        dialog = Gtk.FileChooserDialog \
            (_("Please choose a file"), self.__dialog,
             Gtk.FileChooserAction.OPEN,
             (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
              Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

        filter_text = Gtk.FileFilter()
        filter_text.set_name("Text files")
        filter_text.add_mime_type("text/plain")
        dialog.add_filter(filter_text)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.__set_value("importdictionary", dialog.get_filename())

        dialog.destroy()

    def __export_dictionary_cb(self, widget):
        dialog = Gtk.FileChooserDialog \
                 (_("Please save a file"), self.__dialog,
                  Gtk.FileChooserAction.SAVE,
                  (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                   Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
        dialog.set_do_overwrite_confirmation(True)

        filter_text = Gtk.FileFilter()
        filter_text.set_name("Text files")
        filter_text.add_mime_type("text/plain")
        dialog.add_filter(filter_text)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.__set_value("exportdictionary", dialog.get_filename())

        dialog.destroy()

    def __clear_user_data_cb(self, widget, name):
        self.__set_value("clearuserdata", name)

    def __init_shortcut(self):
        # page Shortcut
        self.__page_shortcut.show()

        # shortcut tree view
        self.__shortcut_editor = self.__builder.get_object("ShortcutsEditor")
        # work around for fedora 21
        self.__shortcut_editor.set_orientation(Gtk.Orientation.VERTICAL)
        self.__shortcut_editor.show()

        # connect "shortcut-changed" signal
        self.__shortcut_editor.connect("shortcut-changed", self.__shortcut_changed_cb)

        # set shortcuts
        self.__shortcut_editor.update_shortcuts(self.__values)

    def __shortcut_changed_cb(self, editor, key, value):
        self.__set_value(key, value)

    def __init_about(self):
        # page About
        self.__page_about.show()

        self.__name_version = self.__builder.get_object("NameVersion")
        self.__name_version.set_markup(_("<big><b>Intelligent Pinyin %s</b></big>") % config.get_version())

    def __changed_cb(self, widget, name):
        self.__set_value(name, widget.get_active())

    def __toggled_cb(self, widget, name):
        self.__set_value(name, widget.get_active ())

    def __get_value(self, name, defval):
        if name in self.__values:
            var = self.__values[name]
            if isinstance(defval, type(var)):
                return var
        self.__set_value(name, defval)
        return defval

    def __set_value(self, name, val):
        var = None
        if isinstance(val, bool):
            var = GLib.Variant.new_boolean(val)
        elif isinstance(val, int):
            var = GLib.Variant.new_int32(val)
        elif isinstance(val, str):
            var = GLib.Variant.new_string(val)
        else:
            print("val(%s) is not in support type." % repr(val), file=sys.stderr)
            return

        self.__values[name] = val
        self.__config.set_value(self.__config_namespace, name, var)

    def run(self):
        return self.__dialog.run()

def main():
    name = "libpinyin"
    if len(sys.argv) == 2:
        name = sys.argv[1]
    if name not in ("libpinyin", "libbopomofo"):
        name = "libpinyin"
    PreferencesDialog(name).run()


if __name__ == "__main__":
    main()
