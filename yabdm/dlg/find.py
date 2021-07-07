import re

import wx

from pubsub import pub
from pyxenoverse.bdm.subentry.type0 import BDMType0
from pyxenoverse.gui.ctrl.hex_ctrl import HexCtrl
from pyxenoverse.gui.ctrl.multiple_selection_box import MultipleSelectionBox
from pyxenoverse.gui.ctrl.single_selection_box import SingleSelectionBox
from pyxenoverse.gui.ctrl.single_selection_info_box import SingleSelectionInfoBox
from pyxenoverse.gui.ctrl.unknown_hex_ctrl import UnknownHexCtrl

pattern = re.compile(r'([ \n/_])([a-z0-9]+)')


class FindDialog(wx.Dialog):
    def __init__(self, parent, entry_list, entry_panel, *args, **kw):
        super().__init__(parent, *args, **kw, style=wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP)
        self.entry_list = entry_list
        self.entry_panel = entry_panel
        self.SetTitle("Find")

        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.hsizer = wx.BoxSizer()
        self.sizer.Add(self.hsizer)
        self.choices = BDMType0.__fields__

        self.entry = wx.Choice(self, -1, choices=self.choices)

        # Setup Selections
        self.entry.SetSelection(0)

        self.find_ctrl = wx.TextCtrl(self, -1, '', size=(150, -1), style=wx.TE_PROCESS_ENTER)
        self.find_ctrl.Bind(wx.EVT_TEXT_ENTER, self.on_find)
        self.find_ctrl.SetFocus()

        self.grid_sizer = wx.FlexGridSizer(rows=3, cols=2, hgap=10, vgap=10)
        self.grid_sizer.Add(wx.StaticText(self, -1, 'Entry: '))
        self.grid_sizer.Add(self.entry, 0, wx.EXPAND)
        self.grid_sizer.Add(wx.StaticText(self, -1, 'Find: '))
        self.grid_sizer.Add(self.find_ctrl, 0, wx.EXPAND)
        self.hsizer.Add(self.grid_sizer, 0, wx.ALL, 10)

        self.button_sizer = wx.BoxSizer(wx.VERTICAL)
        self.find_button = wx.Button(self, -1, "Find Next")
        self.find_button.Bind(wx.EVT_BUTTON, self.on_find)

        self.button_sizer.Add(self.find_button, 0, wx.ALL, 2)
        self.button_sizer.Add(wx.Button(self, wx.ID_CANCEL, "Cancel"), 0, wx.ALL, 2)
        self.hsizer.Add(self.button_sizer, 0, wx.ALL, 8)

        self.status_bar = wx.StatusBar(self)
        self.sizer.Add(self.status_bar, 0, wx.EXPAND)

        self.Bind(wx.EVT_SHOW, self.on_show)

        self.SetSizer(self.sizer)
        self.sizer.Fit(self)

        self.SetAutoLayout(0)

    def on_show(self, e):
        if not e.IsShown():
            return
        try:
            ctrl = self.FindFocus()
            if type(ctrl.GetParent()) in (wx.SpinCtrlDouble, SingleSelectionBox, SingleSelectionInfoBox, MultipleSelectionBox):
                ctrl = ctrl.GetParent()
            elif type(ctrl.GetParent().GetParent()) in (SingleSelectionBox, SingleSelectionInfoBox, MultipleSelectionBox):
                ctrl = ctrl.GetParent().GetParent()
            name = pattern.sub(r'_\2', ctrl.GetName().lower())
            try:
                self.entry.SetSelection(self.choices.index(name))
                if type(ctrl) in (HexCtrl, UnknownHexCtrl, SingleSelectionBox, SingleSelectionInfoBox, MultipleSelectionBox):
                    self.find_ctrl.SetValue(f'0x{ctrl.GetValue():X}')
                else:
                    self.find_ctrl.SetValue(str(ctrl.GetValue()))
            except ValueError:
                pass
        except AttributeError:
            pass

    def select_found(self, item, page, entry_type):
        self.entry_list.UnselectAll()
        self.entry_list.Select(item)
        pub.sendMessage('on_select', _=None)
        pub.sendMessage('focus', entry=entry_type, page=page)
        self.SetFocus()
        self.status_bar.SetStatusText('')

    def find(self, selected, page, entry_type, find):
        if not selected.IsOk():
            self.status_bar.SetStatusText('No matches found')
            return
        item = selected
        first_pass = True
        while item != selected or first_pass:
            data = self.entry_list.GetItemData(item)
            for i, sub_entry in enumerate(data.sub_entries):
                if i <= page and first_pass:
                    continue
                if find is None or sub_entry[entry_type] == find or (
                        isinstance(sub_entry[entry_type], float) and abs(sub_entry[entry_type] - find) < 0.000001):
                    self.select_found(item, i, entry_type)
                    return

            item = self.entry_list.GetNextItem(item)
            first_pass = False
            if not item.IsOk():
                item = self.entry_list.GetFirstItem()
        else:
            self.status_bar.SetStatusText('No matches found')

    def on_find(self, _):
        entry_type = self.choices[self.entry.GetSelection()]
        value = None
        try:
            value = self.get_value(self.find_ctrl)
        except ValueError:
            self.status_bar.SetStatusText("Invalid Value")
        selected = self.entry_list.GetSelections()
        if len(selected) == 1:
            selected = selected[0]
            page = self.entry_panel.current_page
        else:
            selected = self.entry_list.GetFirstItem()
            page = -1
        self.find(selected, page, entry_type, value)

    @staticmethod
    def get_value(ctrl):
        #old logic caused EVERY value that was not hexadecimal to be converted to float type
        #that causes struct.pack exception when writing and corrupts the file
        value = ctrl.GetValue()
        if value.startswith('0x'):
            return int(value, 16)
        if isinstance(value, float):
            return float(value)
        return int(value, 10)
