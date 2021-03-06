import os

import wx

from eelbrain.wxutils import GetWxParent



def _wildcard_from_ext(ext):
    if ext:
        wildcard = '|'.join(["{d} (*.{e})|*.{e}".format(d=d, e=e) for e, d in ext])
        return wildcard
    else:
        return ""


def ask_saveas(title = "Save File",
               message = "Please Pick a File Name", 
               ext = [('eelbrain', "pickled eelbrain experiment")]):
    """
    ext: list of (extension, description) tuples
         or None
    
    """
    if not ext: # allow for []
        ext = None
    
    dialog = wx.FileDialog(GetWxParent(), message,
                           wildcard = _wildcard_from_ext(ext),
                           style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
    dialog.SetMessage(message)
#    dialog.SetWildcard(wildcard)
    dialog.SetTitle(title)
    if dialog.ShowModal() == wx.ID_OK:
        path = dialog.GetPath()
        if ext is not None:
            wc = dialog.GetFilterIndex()
            extension = ext[wc][0]
            if path.split(os.extsep)[-1] != extension:
                path = os.extsep.join([path, extension])
        return path
    else:
        return False


def ask_dir(title = "Select Folder",
            message = "Please Pick a Folder",
            must_exist = True):
    style = wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
    if must_exist:
        style = style | wx.DD_DIR_MUST_EXIST
        
    dialog = wx.DirDialog(GetWxParent(), message, name=title, 
                          style=style)
    dialog.SetTitle(title)
    if dialog.ShowModal() == wx.ID_OK:
        return dialog.GetPath()
    else:
        return False


def ask_file(title = "Pick File",
             message = "Please Pick a File", 
             ext = [('*', "all files")],
             directory='',
             mult=False):
    """
    returns path(s) or False
    
    :arg directory: path to initial directory
    
    """
    style = wx.FD_OPEN
    if mult:
        style = style|wx.FD_MULTIPLE
    dialog = wx.FileDialog(GetWxParent(), message, directory,
                           wildcard = _wildcard_from_ext(ext), 
                           style=style)
    dialog.SetTitle(title)
    if dialog.ShowModal() == wx.ID_OK:
        if mult:
            return dialog.GetPaths()
        else:
            return dialog.GetPath()
    else:
        return False


def ask(title = "Overwrite File?",
        message = "Duplicate filename. Do you want to overwrite?",
        cancel=False,
        default=True, # True=YES, False=NO, None=Nothing
        ):
    """
    returns:
     YES    -> True
     NO     -> False
     CANCEL -> None
    """
    style = wx.YES_NO|wx.ICON_QUESTION
    if cancel:
        style = style|wx.CANCEL
    if default:
        style = style|wx.YES_DEFAULT
    elif default == False:
        style = style|wx.NO_DEFAULT
    dialog = wx.MessageDialog(GetWxParent(), message, title, style)
    answer = dialog.ShowModal()
    if answer == wx.ID_NO:
        return False
    elif answer == wx.ID_YES:
        return True
    elif answer == wx.ID_CANCEL:
        return None

def ask_color(parent=None, default=(0,0,0)):
    dlg = wx.ColourDialog(parent)
    dlg.GetColourData().SetChooseFull(True)
    if dlg.ShowModal() == wx.ID_OK:
        data = dlg.GetColourData()
        out = data.GetColour().Get()
        out = tuple([o/255. for o in out])
    else:
        out = False
    dlg.Destroy()
    return out


def message(title, message=None, icon='i'):
    """
    icon : str
        can be one of the following: '?', '!', 'i', 'error', None
    
    """
    style = wx.OK
    if icon == 'i':
        style = style | wx.ICON_INFORMATION
    elif icon == '?':
        style = style | wx.ICON_QUESTION
    elif icon == '!':
        style = style | wx.ICON_EXCLAMATION
    elif icon == 'error':
        style = style | wx.ICON_ERROR
    elif icon is None:
        pass
    else:
        raise ValueError("Invalid icon argument: %r" % icon)
    dlg = wx.MessageDialog(GetWxParent(), message, title, style)
    dlg.ShowModal()


def progress(*args, **kwargs):
    """
    catches calls meant to create a progress indicator, because the wx 
    ProgressDialog was way too slow.
    
    """
    def __init__(self, i_max=None,
                 title="Progress",
                 message="Be positivistic!",
                 cancel=True):
        style = wx.PD_AUTO_HIDE|wx.GA_SMOOTH#|wx.PD_REMAINING_TIME
        if cancel:
            style = style|wx.PD_CAN_ABORT
        self.dialog = wx.ProgressDialog(title, message, i_max, GetWxParent(), style)
        self.i = 0
    
    def advance(self, new_msg=None):
        self.i += 1
        args = (self.i, )
        if new_msg:
            args += (new_msg, )
        cont, skip = self.dialog.Update(*args)
        if not cont:
            raise KeyboardInterrupt
    
    def terminate(self):
        self.dialog.Close()
        self.dialog.Destroy()


def copy_file(path):
    """
    copies a file to the clipboard
    
    """
    if wx.TheClipboard.Open():
        try:
            data_object = wx.FileDataObject()
            data_object.AddFile(path)
            wx.TheClipboard.SetData(data_object)
        except:
            wx.TheClipboard.Close()
            raise
        else:
            wx.TheClipboard.Close()


def copy_text(text):
    if wx.TheClipboard.Open():
        try:
            data_object = wx.TextDataObject(text)
            wx.TheClipboard.SetData(data_object)
        except:
            wx.TheClipboard.Close()
            raise
        else:
            wx.TheClipboard.Close()
