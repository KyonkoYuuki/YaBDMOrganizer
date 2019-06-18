import wx
from pubsub import pub

from yabdm.panels.sub_entry import SubEntryPanel


class EntryPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.entry = None
        self.current_page = 0
        self.notebook = wx.Notebook(self)
        page_names = [
            '0: Default',
            '1: Unknown',
            '2: Primary Knockback',
            '3: Back',
            '4: Ground Impact',
            '5: Guarding',
            '6: Stumble',
            '7: Unknown',
            '8: Floating Knockback',
            '9: Lying on Ground'
        ]
        self.pages = []

        for idx, name in enumerate(page_names):
            page = SubEntryPanel(self.notebook, idx)
            self.notebook.AddPage(page, name)
            self.pages.append(page)

        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.on_page_changed, self.notebook)

        sizer = wx.BoxSizer()
        sizer.Add(self.notebook, 1, wx.ALL | wx.EXPAND, 10)

        # Publisher
        pub.subscribe(self.disable, 'disable')
        pub.subscribe(self.load_entry, 'load_entry')
        pub.subscribe(self.focus, 'focus')

        self.notebook.Hide()

        # Layout sizers
        self.SetSizer(sizer)
        self.SetAutoLayout(1)

    def disable(self):
        self.current_page = self.notebook.GetSelection()
        self.notebook.Hide()

    def load_entry(self, entry):
        for n, sub_entry in enumerate(entry.sub_entries):
            self.pages[n].load_sub_entry(sub_entry)
        self.entry = entry
        self.notebook.Show()
        self.Layout()

    def focus(self, entry, page):
        sub_entry = self.pages[page]
        sub_page = sub_entry.notebook.FindPage(sub_entry[entry].GetParent())
        sub_entry.notebook.ChangeSelection(sub_page)
        self.notebook.SetSelection(page)
        sub_entry[entry].SetFocus()

    def on_page_changed(self, e):
        self.current_page = e.GetSelection()
        old_selection = self.pages[e.GetOldSelection()]
        selection = self.pages[e.GetSelection()]

        selection.notebook.SetSelection(old_selection.notebook.GetSelection())
