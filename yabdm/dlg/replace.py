import wx
from pubsub import pub

from yabdm.dlg.find import FindDialog


class ReplaceDialog(FindDialog):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.SetTitle("Replace")

        self.replace_ctrl = wx.TextCtrl(self, -1, '', style=wx.TE_PROCESS_ENTER)
        self.replace_ctrl.MoveAfterInTabOrder(self.find_ctrl)

        self.grid_sizer.Add(wx.StaticText(self, -1, 'Replace: '))
        self.grid_sizer.Add(self.replace_ctrl, 0, wx.EXPAND)

        self.replace_button = wx.Button(self, -1, "Replace")
        self.replace_button.Bind(wx.EVT_BUTTON, self.on_replace)
        self.replace_button.MoveAfterInTabOrder(self.find_button)
        self.replace_all_button = wx.Button(self, -1, "Replace All")
        self.replace_all_button.Bind(wx.EVT_BUTTON, self.on_replace_all)
        self.replace_all_button.MoveAfterInTabOrder(self.replace_button)

        self.button_sizer.Insert(1, self.replace_button, 0, wx.ALL, 2)
        self.button_sizer.Insert(2, self.replace_all_button, 0, wx.ALL, 2)

        self.sizer.Fit(self)
        self.Layout()

    def on_replace(self, _):
        entry_type = self.choices[self.entry.GetSelection()]
        try:
            find = int(self.find_ctrl.GetValue(), 0)
            replace = int(self.replace_ctrl.GetValue(), 0)
        except ValueError:
            self.status_bar.SetStatusText("Invalid Value")
            return None
        selected = self.entry_list.GetSelections()

        # Only do this if we have one selected item
        if len(selected) != 1:
            self.find(self.entry_list.GetFirstItem(), -1, entry_type, find)
            return
        selected = selected[0]
        data = self.entry_list.GetItemData(selected)
        page = self.entry_panel.current_page

        # Check to see if current entry is not one we're looking for
        for i, sub_entry in enumerate(data.sub_entries):
            if sub_entry[entry_type] == find:
                sub_entry[entry_type] = replace
                self.select_found(selected, i, entry_type)
                break
        self.find(selected, page, entry_type, find)

    def on_replace_all(self, _):
        entry_type = self.choices[self.entry.GetSelection()]
        try:
            find = int(self.find_ctrl.GetValue(), 0)
            replace = int(self.replace_ctrl.GetValue(), 0)
        except ValueError:
            self.status_bar.SetStatusText("Invalid Value")
            return None

        # Replace all
        count = 0
        item = self.entry_list.GetFirstItem()
        while item.IsOk():
            data = self.entry_list.GetItemData(item)
            for sub_entry in data.sub_entries:
                if sub_entry[entry_type] == find:
                    sub_entry[entry_type] = replace
                    count += 1
            item = self.entry_list.GetNextItem(item)
        pub.sendMessage('on_select', _=None)
        self.status_bar.SetStatusText(f'Replaced {count} entry(s)')
