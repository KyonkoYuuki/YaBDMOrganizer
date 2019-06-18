import wx

from wx.lib.dialogs import MultiMessageDialog
import pickle
from wx.dataview import (
    TreeListCtrl, EVT_TREELIST_SELECTION_CHANGED, EVT_TREELIST_ITEM_CONTEXT_MENU, TLI_FIRST, TL_MULTIPLE
)
from pyxenoverse.bdm.entry import Entry
from yabdm.dlg.new import NewEntryDialog
from pubsub import pub


class MainPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.bdm = None
        self.parent = parent

        self.entry_list = TreeListCtrl(self, style=TL_MULTIPLE)
        self.entry_list.AppendColumn("Entry")
        self.entry_list.Bind(EVT_TREELIST_ITEM_CONTEXT_MENU, self.on_right_click)
        self.entry_list.Bind(EVT_TREELIST_SELECTION_CHANGED, self.on_select)
        self.cdo = wx.CustomDataObject("BDMEntry")

        self.Bind(wx.EVT_MENU, self.on_delete, id=wx.ID_DELETE)
        self.Bind(wx.EVT_MENU, self.on_copy, id=wx.ID_COPY)
        self.Bind(wx.EVT_MENU, self.on_paste, id=wx.ID_PASTE)
        self.Bind(wx.EVT_MENU, self.on_new, id=wx.ID_NEW)
        accelerator_table = wx.AcceleratorTable([
            (wx.ACCEL_CTRL, ord('c'), wx.ID_COPY),
            (wx.ACCEL_CTRL, ord('v'), wx.ID_PASTE),
            (wx.ACCEL_NORMAL, wx.WXK_DELETE, wx.ID_DELETE),
        ])
        self.entry_list.SetAcceleratorTable(accelerator_table)

        pub.subscribe(self.on_select, 'on_select')

        # Use some sizers to see layout options
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.entry_list, 1, wx.ALL | wx.EXPAND, 10)

        # Layout sizers
        self.SetSizer(sizer)
        self.SetAutoLayout(1)

    def build_tree(self):
        self.entry_list.DeleteAllItems()
        root = self.entry_list.GetRootItem()
        for entry in sorted(self.bdm.entries, key=lambda e: e.id):
            self.entry_list.AppendItem(root, f'{entry.id}: Entry', data=entry)

    def get_current_entry_ids(self):
        entry_ids = []
        item = self.entry_list.GetFirstItem()
        while item.IsOk():
            data = self.entry_list.GetItemData(item)
            entry_ids.append(data.id)
            item = self.entry_list.GetNextItem(item)
        return entry_ids

    def get_previous_entry(self, entry_id):
        item = self.entry_list.GetFirstItem()
        prev = TLI_FIRST
        while item.IsOk():
            data = self.entry_list.GetItemData(item)
            if data.id > entry_id:
                break
            prev, item = item, self.entry_list.GetNextItem(item)
        return prev

    def on_right_click(self, _):
        selected = self.entry_list.GetSelections()
        if not selected:
            return
        menu = wx.Menu()
        menu.Append(wx.ID_NEW)
        menu.Append(wx.ID_DELETE)
        menu.Append(wx.ID_COPY)
        paste = menu.Append(wx.ID_PASTE)
        add = menu.Append(wx.ID_ADD, '&Add Copied Entry')
        success = False

        # Check Clipboard
        if wx.TheClipboard.Open():
            success = wx.TheClipboard.IsSupported(wx.DataFormat("BDMEntry"))
            wx.TheClipboard.Close()
        add.Enable(success)
        paste.Enable(success)
        self.PopupMenu(menu)
        menu.Destroy()

    def on_select(self, _):
        selected = self.entry_list.GetSelections()
        if len(selected) != 1:
            pub.sendMessage('disable')
            return
        pub.sendMessage('load_entry', entry=self.entry_list.GetItemData(selected[0]))

    def add_entry(self, entry):
        root = self.entry_list.GetRootItem()
        prev = self.get_previous_entry(entry.id)
        item = self.entry_list.InsertItem(root, prev, f'{entry.id}: Entry', data=entry)
        self.entry_list.Select(item)
        self.on_select(None)

    def on_new(self, _):
        # Ask for ID
        if self.bdm is None:
            return
        with NewEntryDialog(self, self.get_current_entry_ids()) as dlg:
            if dlg.ShowModal() != wx.ID_OK:
                return
            entry_id = dlg.GetValue()
        self.entry_list.UnselectAll()

        # Add it
        entry = Entry(entry_id=entry_id)
        self.add_entry(entry)
        pub.sendMessage('set_status_bar', text='Added new entry')

    def on_add(self, _):
        if self.bdm is None:
            return
        cdo = wx.CustomDataObject("BDMEntry")
        success = False
        if wx.TheClipboard.Open():
            success = wx.TheClipboard.GetData(cdo)
            wx.TheClipboard.Close()
        if not success:
            with wx.MessageDialog(self, 'Unable to get copied data') as dlg:
                dlg.ShowModal()
                return
        paste_data = pickle.loads(cdo.GetData())

        # Get new Id's
        with NewEntryDialog(self, self.get_current_entry_ids()) as dlg:
            if dlg.ShowModal() != wx.ID_OK:
                return
            entry_id = dlg.GetValue()
        current_entry_ids = self.get_current_entry_ids()
        self.entry_list.UnselectAll()

        # Paste
        for paste in paste_data:
            while entry_id in current_entry_ids:
                entry_id += 1
            entry = Entry(entry_id=entry_id)
            entry.paste(paste)
            self.add_entry(entry)
            entry_id += 1

        self.on_select(None)
        pub.sendMessage(f'Pasted {len(paste_data)} new entry(s)')

    def on_delete(self, _):
        selected = self.entry_list.GetSelections()
        if not selected:
            return

        for item in selected:
            self.entry_list.DeleteItem(item)
        pub.sendMessage('disable')
        pub.sendMessage('set_status_bar', text=f'Deleted {len(selected)} entries')

    def on_copy(self, _):
        selected = self.entry_list.GetSelections()

        self.cdo = wx.CustomDataObject("BDMEntry")
        self.cdo.SetData(pickle.dumps([self.entry_list.GetItemData(item) for item in selected]))
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(self.cdo)
            wx.TheClipboard.Flush()
            wx.TheClipboard.Close()
        pub.sendMessage('set_status_bar', text=f'Copied {len(selected)} entries')

    def on_paste(self, _):
        selected = self.entry_list.GetSelections()
        if not selected:
            return

        success = False
        cdo = wx.CustomDataObject("BDMEntry")
        if wx.TheClipboard.Open():
            success = wx.TheClipboard.GetData(cdo)
            wx.TheClipboard.Close()
        if success:
            paste_data = pickle.loads(cdo.GetData())
            paste_length = len(paste_data)
            selected_length = len(selected)
            if selected_length > paste_length:
                for item in selected[paste_length:]:
                    self.entry_list.Unselect(item)
                selected = selected[:paste_length]

            item = selected[-1]
            self.entry_list.Select(item)
            for n in range(paste_length - selected_length):
                item = self.entry_list.GetNextItem(item)
                if not item.IsOk():
                    with wx.MessageDialog(self, f'Not enough entries to paste over. Expected {paste_length}') as dlg:
                        dlg.ShowModal()
                        return
                self.entry_list.Select(item)
                selected.append(item)

            if len(selected) > 1:
                msg = '\n'.join([f' * {self.entry_list.GetItemData(item).id}: Entry' for item in selected])
                with MultiMessageDialog(self, 'Are you sure you want to replace the following entries?',
                                      'Warning', msg, wx.YES | wx.NO) as dlg:
                    if dlg.ShowModal() != wx.ID_YES:
                        return

            for n, paste in enumerate(paste_data):
                data = self.entry_list.GetItemData(selected[n])
                data.paste(paste)

            self.on_select(None)
            pub.sendMessage('set_status_bar', text=f'Pasted {len(paste_data)} entry(s)')

    def reindex(self):
        selected = self.entry_list.GetSelections()
        if len(selected) != 1:
            return
        item = selected[0]
        entry = self.entry_list.GetItemData(item)
        self.entry_list.DeleteItem(item)
        self.add_entry(entry)




