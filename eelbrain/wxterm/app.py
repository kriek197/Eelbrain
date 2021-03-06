"""
the main application for Eelbrain's wx-terminal

"""

import logging 
import os

import wx

import shell


        
class MainApp(wx.App):
    """
    The main application. Creates the shell instance.
    
    """
    def __init__(self, global_namespace, redirect=False, filename=None):
        """
        redirect : bool
            Shows the output of internal ``print`` commands in a window
        
        """
        self.global_namespace = global_namespace
        wx.App.__init__(self, redirect=redirect, filename=filename)
    
    def OnInit(self):
        self.shell = shell.ShellFrame(None, self.global_namespace)
        if wx.__version__ >= '2.9':
            self.shell.ShowWithEffect(wx.SHOW_EFFECT_ROLL_TO_BOTTOM)
        else:
            self.shell.Show()
        return True
    
    def MacOpenFile(self, filename):
        """
        after
        http://wiki.wxpython.org/Optimizing%20for%20Mac%20OS%20X
        
        """
        logging.debug("MAC Open File: %s"%filename)
        if os.path.isfile(filename):
            self.shell.FileOpen(filename)


