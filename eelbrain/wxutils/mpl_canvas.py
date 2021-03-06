'''
Created on Dec 21, 2010

Mpl examples:
http://matplotlib.sourceforge.net/examples/user_interfaces/index.html


'''

import tempfile
import logging

import numpy as np
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.backends import backend_wx
from matplotlib.figure import Figure
import wx

from basic import Icon
from eelbrain import ui
import ID


class FigureCanvasPanel(FigureCanvasWxAgg):
    """
    Subclass mpl's Canvas to allow interaction with wx.py (such as copying the
    contents to the clipboard)
    start search at wx.py.frame.Frame.OnUpdateMenu() 
    
    """
    _copy_as_pdf = True
    def __init__(self, parent, dpi=100):
        self.figure = Figure(dpi=dpi)
        FigureCanvasWxAgg.__init__(self, parent, -1, self.figure)
        self.Bind(wx.EVT_ENTER_WINDOW, self.ChangeCursor)
        self.Bind(wx.EVT_MENU, self.OnFileSave, id=wx.ID_SAVE)
    
    def CanCopy(self):
        "pretend to be wx.py.frame.Frame "
        return True
    
    def bufferHasChanged(self):
        return True
    
    def ChangeCursor(self, event):
        "http://matplotlib.sourceforge.net/examples/user_interfaces/wxcursor_demo.html"
        self.SetCursor(wx.StockCursor(wx.CURSOR_CROSS))
    
    def store_canvas(self):
        self._background = self.copy_from_bbox(self.figure.bbox)
    
#    def OnPaint(self, event):
#        self.draw()
    
    def Copy(self):
        if self._copy_as_pdf:
            try:
                if wx.TheClipboard.Open():
                    # same code in mpl_tools
                    path = tempfile.mktemp('.pdf')#, text=True)
                    logging.debug("Temporary file created at: %s"%path)
                    self.figure.savefig(path)
                    # copy path
                    do = wx.FileDataObject()
                    do.AddFile(path)
                    wx.TheClipboard.SetData(do)
                    wx.TheClipboard.Close()
            except wx._core.PyAssertionError:
                wx.TheClipboard.Close()
                    
        else:
            self.figure.set_facecolor((1,1,1))
            self.draw()
            self.Copy_to_Clipboard()
    
    def OnFileSaveAs(self, event):
        self.OnFileSave(event)
    
    def OnFileSave(self, event):
        """
        FIXME: maybe start search at wx.py.frame.Frame.OnUpdateMenu() 
        
        """
        path = ui.ask_saveas("Save Figure", "Save the current figure. The format is " 
                             "determined from the extension.", None)
        if path:
            self.figure.savefig(path)
    
    def redraw(self, axes=[], artists=[]):
        self.restore_region(self._background)
        for ax in axes:
            ax.draw_artist(ax)
            extent = ax.get_window_extent()
            self.blit(extent)
        for artist in artists:
            ax = artist.get_axes()
            # substitute redrawing whole ax
            ax.draw_artist(ax)
            extent = ax.get_window_extent()
            self.blit(extent)
            # FIXME:
#            ax.draw_artist(artist)
#            extent = artist.get_window_extent(self.get_renderer())
#            self.blit(extent)
    
    def redraw_artist(self, artist):
        "redraw a single artist"
        ax = artist.get_axes()
        self.restore_region(self._background)
        ax.draw_artist(artist)
        extent = artist.get_window_extent(self)
        self.blit(extent)
    
    def redraw_ax(self, *axes):
        "redraw one or several axes"
        self.restore_region(self._background)
        for ax in axes:
            ax.draw_artist(ax)
            extent = ax.get_window_extent()
            self.blit(extent)
    



class CanvasFrame(wx.Frame):
    """
    
    after:
    http://matplotlib.sourceforge.net/examples/user_interfaces/embedding_in_wx2.html
    
    """
    def __init__(self, parent, title="Matplotlib Frame", 
                 size=(800,600), dpi=50, 
                 statusbar=True, toolbar=True, mpl_toolbar=False):
        wx.Frame.__init__(self, parent, -1, title=title, size=size)
#        self.SetBackgroundColour(wx.NamedColour("WHITE"))
        
    # set up the canvas
        # prepare the plot panel
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        self.canvas = FigureCanvasPanel(self, dpi=dpi)
        sizer.Add(self.canvas, 1, flag=wx.EXPAND)
#        sizer.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
        sizer.Layout()
        
        # get figure
        self.figure = self.canvas.figure
        
        if statusbar:
            self.CreateStatusBar()
            self.canvas.mpl_connect('motion_notify_event', self.OnMotionStatusBarUpdate)
            self.canvas.mpl_connect('axes_leave_event', self.OnLeaveAxesStatusBarUpdate)
        
        if toolbar:
            tb = self.CreateToolBar(wx.TB_HORIZONTAL)
            tb.SetToolBitmapSize(size=(32,32))
            self._init_FillToolBar(tb)
            tb.Realize()
        
        if mpl_toolbar:
            self.add_mpl_toolbar()  # comment this out for no toolbar
    
    def _init_FillToolBar(self, tb):
        if wx.__version__ >= '2.9':
            tb.AddStretchableSpace()
        else:
            tb.AddSeparator()
        
        tb.AddLabelTool(ID.FULLSCREEN, "Fullscreen", Icon("tango/actions/view-fullscreen"))
        self.Bind(wx.EVT_TOOL, self.OnShowFullScreen, id=ID.FULLSCREEN)
    
    def add_mpl_toolbar(self):
        self.toolbar = backend_wx.NavigationToolbar2Wx(self.canvas_panel)
        self.toolbar.Realize()
        if 0:#wx.Platform == '__WXMAC__':
            # Mac platform (OSX 10.3, MacPython) does not seem to cope with
            # having a toolbar in a sizer. This work-around gets the buttons
            # back, but at the expense of having the toolbar at the top
            self.SetToolBar(self.toolbar)
        else:
            # On Windows platform, default window size is incorrect, so set
            # toolbar width to figure width.
            tw, th = self.toolbar.GetSizeTuple()
            fw, fh = self.canvas_panel.GetSizeTuple()
            # By adding toolbar in sizer, we are able to put it at the bottom
            # of the frame - so appearance is closer to GTK version.
            # As noted above, doesn't work for Mac.
            self.toolbar.SetSize(wx.Size(fw, th))
            self.Sizer.Add(self.toolbar, 0, wx.LEFT | wx.EXPAND)
        # update the axes menu on the toolbar
        self.toolbar.update()
    
    def OnFileSave(self, event):
        """
        FIXME: maybe start search at wx.py.frame.Frame.OnUpdateMenu() 
        
        """
        path = ui.ask_saveas("Save Figure", "Save the current figure. The format is " 
                             "determined from the extension.", None)
        if path:
            self.figure.savefig(path)
    
    def OnLeaveAxesStatusBarUpdate(self, event):
        "update the status bar when the cursor leaves axes"
        sb = self.GetStatusBar()
        sb.SetStatusText("", 0)
    
    def OnMotionStatusBarUpdate(self, event):
        "update the status bar for mouse movement"
        ax = event.inaxes
        if ax:
            # update status bar
            sb = self.GetStatusBar()
            txt = "t = %.3f s" % event.xdata
            sb.SetStatusText(txt, 0)
    
    def OnShowFullScreen(self, event):
        self.ShowFullScreen(not self.IsFullScreen())



class TestCanvas(CanvasFrame):
    def __init__(self, effect=10, mpl_toolbar=True):
        parent = wx.GetApp().shell
        CanvasFrame.__init__(self, parent, title="Test MPL Frame", 
                             mpl_toolbar=mpl_toolbar)
        self.plot()
        self.ShowWithEffect(effect)
    def plot(self):
        self.axes = self.figure.add_subplot(111)
        t = np.arange(0.0, 3.0, 0.01)
        s = np.sin(2*np.pi*t)
        self.axes.plot(t,s)
