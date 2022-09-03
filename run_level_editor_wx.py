import wx

from leveledit_wx.wxlev import LevelEditor

if __name__ == '__main__':
    app = wx.PySimpleApp()
    frame = LevelEditor(None, wx.ID_ANY, "Level Editor", (800, 600))
    frame.Show()
    app.MainLoop()