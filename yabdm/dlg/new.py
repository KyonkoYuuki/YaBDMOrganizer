import wx


class NewEntryDialog(wx.Dialog):
    def __init__(self, parent, current_entries, *args, **kw):
        super().__init__(parent, *args, **kw)
        self.current_entries = current_entries

        self.SetTitle("New Entry ID")

        entry_sizer = wx.BoxSizer()
        entry_sizer.Add(wx.StaticText(self, -1, 'Enter new ID:'), 0, wx.ALL, 10)
        self.entry_id = wx.SpinCtrl(self, min=0, max=0xFFFF, initial=current_entries[-1] + 1)
        self.entry_id.SetFocus()
        entry_sizer.Add(self.entry_id, 0, wx.ALL, 10)

        ok_button = wx.Button(self, wx.ID_OK, "Ok")
        ok_button.SetDefault()
        cancel_button = wx.Button(self, wx.ID_CANCEL, "Cancel")

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(ok_button, 0, wx.LEFT | wx.RIGHT, 2)
        button_sizer.Add(cancel_button, 0, wx.LEFT | wx.RIGHT, 5)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(entry_sizer, 1, wx.ALL, 10)
        sizer.Add(wx.StaticLine(self), 0, wx.EXPAND | wx.ALL, 10)
        sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 10)

        self.Bind(wx.EVT_BUTTON, self.on_close)
        self.Bind(wx.EVT_MENU, self.on_close)

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.Layout()

    def on_close(self, e):
        entry_id = self.GetValue()
        if e.GetId() == wx.ID_OK and entry_id in self.current_entries:
            with wx.MessageDialog(self, f'An Entry with ID {entry_id} already exists!', 'Warning') as dlg:
                dlg.ShowModal()
            return
        e.Skip()

    def GetValue(self):
        return self.entry_id.GetValue()
