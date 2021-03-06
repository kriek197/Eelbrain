"""
Help Viewer

TODO: use wx.html2

"""

import types
import wx
import wx.html
import logging

import ID
from eelbrain.wxutils import Icon



HtmlTemplate = """<pre class="literal-block">%s</pre>"""

"""
reStructuredText to HTML parsing following:
http://stackoverflow.com/questions/6654519
"""
try:
    import docutils.core
    
    def rst2html(rst):
#        html = docutils.core.publish_parts(rst, writer_name='html')['body']
        try:
            html = docutils.core.publish_parts(rst, writer_name='html')['body']
            logging.debug("rst success on: %s" % len(rst))
            html = '<span style="color: rgb(0, 0, 255);">RST2HTML:</span><br>' + html
#            delim = '<br><br>RST <hr style="width: 100%; height: 2px;"><br>HTML <br>'
#            html = delim.join([rst, html])
        except:
            logging.debug("rst fail on: %s" % len(rst))
            html = '<span style="color: rgb(255, 0, 0);">RST2HTML FAILED:</span><br>' \
                 + HtmlTemplate % rst
        return html
except:
    def rst2html(text):
        text = HtmlTemplate % text
        return text


def doc2html(obj, default='No doc-string.<br>'):
    """
    Returns the object's docstring as html, or the default value if there is
    no docstring.
    
    """
    if hasattr(obj, '__doc__') and isinstance(obj.__doc__, basestring):
        txt = rst2html(obj.__doc__)
    else:
        txt = default
    return txt




def format_chapter(title, txt):
    return '\n'.join(('\n',
                      '-'*80,
                      title + ' |',
                      '-'*(2+len(title)),
                      txt, '\n'))


class HelpViewer(wx.Frame):
    def __init__(self, parent, *args, **kwargs):
        wx.Frame.__init__(self, parent, *args, **kwargs)
        self.EnableCloseButton(False)
        self.parent_shell = parent
        
#        self.help_panel = TxtHelpPanel(self)
        self.help_panel = HtmlHelpPanel(self)
                
        # prepare data container
        self.history = []
        self.current_history_id = -1
        
        # TOOLBAR
        self.toolbar = tb = self.CreateToolBar(wx.TB_HORIZONTAL)
        tb.SetToolBitmapSize(size=(32,32))
        # hide
        tb.AddLabelTool(ID.HELP_HIDE, "Hide", Icon("tango/status/image-missing"))
        self.Bind(wx.EVT_TOOL, self.OnHide, id=ID.HELP_HIDE) 
        tb.AddSeparator()
        # forward/backward
        tb.AddLabelTool(wx.ID_HOME, "Home", Icon("tango/places/start-here"))
        self.Bind(wx.EVT_TOOL, self.OnHome, id=wx.ID_HOME)
        tb.AddLabelTool(wx.ID_BACKWARD, "Back", Icon("tango/actions/go-previous"))
        self.Bind(wx.EVT_TOOL, self.OnBackward, id=wx.ID_BACKWARD)
        tb.AddLabelTool(wx.ID_FORWARD, "Next", Icon("tango/actions/go-next"))
        self.Bind(wx.EVT_TOOL, self.OnForward, id=wx.ID_FORWARD)
        tb.EnableTool(wx.ID_FORWARD, False)
        tb.EnableTool(wx.ID_BACKWARD, False)
        tb.AddSeparator()

        # text search
        self.history_menu = wx.Menu()
        item = self.history_menu.Append(-1, "Help History")
        item.Enable(False)
        search_ctrl = wx.SearchCtrl(tb, wx.ID_HELP, style=wx.TE_PROCESS_ENTER, 
                                    size=(300,-1))
        search_ctrl.Bind(wx.EVT_TEXT_ENTER, self.OnSelfSearch)
        search_ctrl.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.OnSelfSearch)
        search_ctrl.SetMenu(self.history_menu)
        self.history_menu.Bind(wx.EVT_MENU, self.OnSearchhistory) 
        search_ctrl.ShowCancelButton(True)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnSearchCancel, search_ctrl)
        tb.AddControl(search_ctrl)
        self.search_ctrl = search_ctrl
        
        # window resizing
#        self.Bind(wx.EVT_MAXIMIZE, self.OnMaximize)
#        height = self.GetMaxHeight()
#        self.SetMaxSize((600, height))
        
        # finish
        tb.Realize()
    def GetCurLine(self):
        # FIXME: better implementation that returns the actual line!
        return self.help_panel.GetCurLine()
    def Help_Lookup(self, topic=None, name=None):
        """
        Display help for a topic. Topic can be 
         - None -> display default help
         - an object -> display help for the object based on its doc-string
        
        """
        if topic is None:
            name = 'Start Page'
        else:
            name = self.help_panel.add_object(topic)
                
        self.display(name)
        
        if name in self.history:
            index = self.history.index(name)
            self.history.pop(index)
        
        i = self.current_history_id
        if (i != -1) and (len(self.history) > i + 1):
            self.history = self.history[0:i+1]
        
        self.history.append(name)
        self.set_current_history_id(-1)
        
        self.Raise()
    
    def OnHide(self, event=None):
        self.Show(False)
    
    def OnHome(self, event=None):
        self.Help_Lookup(topic=None)
#    def OnMaximize(self, event=None):
#        logging.debug("help.OnMaximize")
#        height = self.GetMaxHeight()
#        x_pos = self.GetPosition()[0]
#        self.SetPosition((x_pos, 0))
#        self.SetSize((600, height))
    def OnSearchCancel(self, event=None):
        self.search_ctrl.Clear()
    
    def OnSearchhistory(self, event=None):
        i = event.GetId() - 1
        self.display(i)
    
    def display(self, name):
        self.help_panel.display(name)
        
        self.search_ctrl.SetValue(name)
        self.SetTitle("Help: %s" % name)
        self.Show()
        
    def OnSelfSearch(self, event=None):
        txt = event.GetString()
        if len(txt) > 0:
            self.text_lookup(txt)
    
    def OnForward(self, event=None):
        i = self.current_history_id + 1
        
        name = self.history[i]
        self.display(name)
        self.set_current_history_id(i)
    
    def OnBackward(self, event=None):
        i = self.current_history_id
        if i == -1:
            i = len(self.history) - 1
        
        i -= 1
        name = self.history[i]
        self.display(name)
        self.set_current_history_id(i)
        
    def set_current_history_id(self, i):
        self.current_history_id = i
        
        if i == -1:
            exists_greater = False
            exists_smaller = len(self.history) > 1
        else:
            exists_greater = len(self.history) > i + 1
            exists_smaller = i > 0
        self.toolbar.EnableTool(wx.ID_FORWARD, exists_greater)
        self.toolbar.EnableTool(wx.ID_BACKWARD, exists_smaller)
    
    def text_lookup(self, txt):
        logging.debug("Help text_lookup: %r" % txt)
        try:
            obj = eval(txt, self.parent_shell.global_namespace)
        except:
            dlg = wx.MessageDialog(self, "No object named %r in shell namespace"%txt,
                                   "Help Lookup Error:", wx.OK|wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy() 
        else:
            self.Help_Lookup(obj, name=txt)



class HelpPanel():
    """
    Baseclass for help panels, does not work in itself
    
    """
    def __init__(self, parent):
        self.parent = parent
        self.delete_cache()
    
    def add_object(self, obj, name=None):
        if not name: 
            if hasattr(obj, '__name__'):
                name = obj.__name__
            elif hasattr(obj, '__class__'):
                name = obj.__class__.__name__
            else:
                raise ValueError("No Name For Help Object")
        
        if name not in self.help_items:
            self.help_items[name] = self.parse_object(obj)
        
        return name

    def delete_cache(self):
        "removes all stored help entries"
        self.help_items = {'Start Page': self.get_help_home()}
    
    def display(self, name):
        if name in self.help_items:
            content = self.help_items[name]
            self.set_content(name, content)
        else:
            raise ValueError("No help object for %r"%name)
    
    def GetCurLine(self):
        raise NotImplementedError
    
    def get_help_home(self):
        title = "PyShell"
        title = '\n'.join([title, '-' * len(title)])
        intro = "PyShell ``HELP_TEXT``::"
        pyshell_doc = '\t' + wx.py.shell.HELP_TEXT.replace('\n', '\n\t')
        text = '\n\n'.join([_main_help, title, intro, pyshell_doc])
        return self.parse_text(text)

    def parse_object(self, obj):
        "parse an object (through its __doc__ string and attributes)"
        raise NotImplementedError
    
    def parse_text(self, text):
        "parse a string"
        raise NotImplementedError
    
    def set_content(self, name, content):
        raise NotImplementedError


    
class TxtHelpPanel(HelpPanel):
    def __init__(self, parent):
        HelpPanel.__init__(self, parent)
        self.TextCtrl = wx.TextCtrl(parent, -1, style=wx.TE_MULTILINE)
        self.TextCtrl.SetEditable(False)
        self.TextCtrl.SetFont(wx.Font(12, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, 
                                      wx.FONTWEIGHT_LIGHT, face='Monaco'))
        self.TextCtrl.SetBackgroundColour(wx.Colour(170,220,250))
        
    def GetCurLine(self):
        txt = self.TextCtrl.GetString(*self.TextCtrl.GetSelection())
        if len(txt) == 0:
            dlg = wx.MessageDialog(self.parent, "In the help viewer, the whole "
                                   "name must be selected to get help", "Help"
                                   "Lookup Error", wx.ICON_INFORMATION|wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
        else:
            return txt, 0
    
    def parse_object(self, obj):
        """
        Parse the object's doc-string
        
        """
        if not hasattr(obj, '__doc__'):
            raise ValueError("Object does not have a doc-string.")
        txt = obj.__doc__
        if txt is None:
            txt = ''
        
        attrs = {}
        title_indexes = []
#            # TODO: format text with             
#            for i1, i2 in title_indexes:
#                self.textCtrl.SetStyle(...))

        for attr in dir(obj):
            if attr[0] != '_' or attr=='__init__':
                a = getattr(obj, attr)
                if hasattr(a, '__doc__'):
                    attrs[attr] = a.__doc__
        
        if len(attrs) > 0:
            if len(txt) > 0:
                txt += '\n\n\n' + '-'*80 + '\n\n'
            txt += 'Attributes\n==========\n'
            items = sorted(attrs.keys())
            for i in items:
                if attrs[i]:
                    txt += '%s\n'%i
                else:
                    txt += '%s (no __doc__)\n'%i
            for i in items:
                docstr = attrs[i]
                if docstr:
                    id1 = len(txt)
                    id2 = id1 + len(i)
                    title_indexes.append((id1, id2))
                    txt += format_chapter(i, docstr)
        
        if txt == '':
            return "Error: No doc-string found."
        else:
            return txt
    
    def parse_text(self, text):
        return text
    
    def set_content(self, name, content):
        self.TextCtrl.SetValue(content)
        
    


class HtmlHelpPanel(HelpPanel):
    """
    """
    def __init__(self, parent):
        HelpPanel.__init__(self, parent)
        self.HtmlCtrl = html = wx.html.HtmlWindow(parent, -1, 
                                           style=wx.NO_FULL_REPAINT_ON_RESIZE)
#        html.SetRelatedFrame(parent)
        # after wxPython Demo
        if "gtk2" in wx.PlatformInfo:
            self.SetStandardFonts()
        
    def GetCurLine(self):
        return '', 0
    
    def parse_object(self, obj):
        """
        Parse the object's doc-string
        
        """
        if not hasattr(obj, '__doc__'):
            raise ValueError("Object does not have a doc-string.")
        
        attrs = {}
        ### new customized parsing        
        if isinstance(obj, (types.MethodType, types.BuiltinMethodType)):
            title = "%s(...)" % obj.__name__
            if isinstance(obj, types.MethodType):
                subtitle = "Method of %s" % str(type(obj.im_class))[1:-1]
            else:
                subtitle = "Method of %s" % str(type(obj.__self__))[1:-1]
            intro = doc2html(obj) + '<br>'
        else: ### OLD default parsing
            is_function = isinstance(obj, (types.FunctionType, types.BuiltinFunctionType,
                                           types.MethodType, types.BuiltinMethodType))
            
            # doc-string for the object itself
            obj_type = str(type(obj))[1:-1]
            if hasattr(obj, '__name__'):
                title = obj.__name__
                subtitle = obj_type
            else:
                title = obj_type
                subtitle = None
            
            intro = doc2html(obj)
            if not is_function:
                intro += '<br><br><hr style="width: 100%; height: 2px;"><br><br>'        
            
            # collect attributes
            if not is_function:
                for attr in dir(obj):
                    if attr[0] != '_' or attr=='__init__':
                        try:
                            a = getattr(obj, attr)
                        except:
                            pass
                        else:
                            attrs[attr] = doc2html(a)
        
        # add text for attrs
        TOC = []
        chapters = []
        if len(attrs) > 0:
            items = sorted(attrs.keys())
            for name in items:
                if attrs[name]:
                    TOC.append('<a href="#%s">%s</a><br>' % (name, name))
                    chapters.append('<h2><a href="#TOC">&uarr;</a><a name="%s"></a>%s</h2><br>%s' \
                                    % (name, name, attrs[name]))
                else:
                    TOC.append('<span style="color: rgb(102, 102, 102);">'
                               '%s (no __doc__)</span><br>' % name)
        
        # compose text
        txt = "<h1>%s</h1><br>" % title
        if subtitle:
            txt += '<span style="color: rgb(102, 102, 102);">%s</span><br>' % subtitle
        txt += intro
        
        if len(TOC) > 0:
            txt += '<h1><a name="TOC"></a>Attributes</h1><br>'
            txt += '<br>'.join(TOC)
            txt += '<br>'.join(chapters)
        
        if txt == '':
            txt = "Error: No doc-string found."
        
        return txt
    
    def parse_text(self, text):
        return rst2html(text)
    
    def set_content(self, name, content):
        self.HtmlCtrl.SetPage(content)



_main_help = """
Keyboard Shortcuts
------------------

* Shell:

  * ``ctrl``-``d``: copy the selected commands to the topmost editor window

* Editor:

  * ``ctrl``-``/``: comment or uncomment selected lines
  * ``alt``-arrow (up/down): move current line up or down (!!! uses copy-paste)


Shell Commands
--------------

help([object]):  
    Display help about the object in the help viewer. If no object 
    is provided, the main help page (this page) is displayed.

clear():  
    clear all text from the shell

load([filename]):  
    Load a pickled Experiment or a Python script. If no filename
    is provided, a file dialog will be displayed

attach(object):  
    object can be dict/dataset/Experiment

loadtable(file): 
    ???

"""

