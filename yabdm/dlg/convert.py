import wx


class ConvertDialog(wx.Dialog):
    def __init__(self, parent, choices, *args, **kw):
        super().__init__(parent, *args, **kw)

        self.SetTitle('Select Skill ID to replace with 0xBACA (47818)')

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(wx.StaticText(self, -1, 'Skill Id'), 0, wx.ALL, 10)

        self.skill_id = wx.Choice(self, -1, size=(100, -1), choices=choices)
        self.skill_id.Select(0)
        hsizer.Add(self.skill_id, 0, wx.ALL, 10)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_button = wx.Button(self, wx.ID_OK, "Ok")
        ok_button.SetDefault()
        button_sizer.Add(ok_button)
        cancel_button = wx.Button(self, wx.ID_CANCEL, "Cancel")
        button_sizer.AddSpacer(10)
        button_sizer.Add(cancel_button)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(hsizer, 0, wx.EXPAND, 10)
        sizer.Add(wx.StaticLine(self, size=(300, -1)), 0, wx.EXPAND | wx.ALL, 10)
        sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 10)

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.Layout()

    def GetValue(self):
        return int(self.skill_id.GetString(self.skill_id.GetSelection()))

