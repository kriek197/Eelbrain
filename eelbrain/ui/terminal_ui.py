"""
This is the terminal-based implementation of the fmtxt.ui functions and 
depends only on the Python standard library os.

"""


import os



def ask_saveas(title = "Save File",
               message = "Please Pick a File Name", 
               ext = [('eelbrain', "pickled eelbrain experiment")]):
    """
    ext: list of (extension, description) tuples
         or None
    
    """
    msg = "%s (%s): " % (title, message)
    path = raw_input(msg)
    path = os.path.expanduser(path)
    
    dirname = os.path.split(path)[0]
    if os.path.exists(path):
        if ask(title="File Exists. Overwrite?",
               message=repr(path)):
            return path
        else:
            return False
    elif os.path.exists(dirname):
        return path
    else:
        if ask(title="Directory does not exist. Create?",
               message=repr(dirname)):
            os.makedirs(dirname)
            return path
        else:
            return False


def ask_dir(title = "Select Folder",
            message = "Please Pick a Folder",
            must_exist = True):
    msg = "%s (%s): " % (title, message)
    path = raw_input(msg)
    path = os.path.expanduser(path)
    if os.path.exists(path) and os.path.isdir(path):
        return path
    else:
        return False


def ask_file(title = "Pick File",
             message = "Please Pick a File", 
             ext = [('*', "all files")],
             directory='',
             mult=False):
    """
    returns a path (str) or False
    
    """
    msg = "%s (%s): " % (title, message)
    path = raw_input(msg)
    path = os.path.expanduser(path)
    if os.path.exists(path):
        return path
    else:
        return False


def ask(title = "Overwrite File?",
        message = "Duplicate filename. Do you want to overwrite?",
        cancel=False,
        default=True,
        ):
    """
    returns:
     YES    -> True
     NO     -> False
     CANCEL -> None
    """
    print title
    print message
    c = ''
    while c not in ['y', 'n', 'c']:
        c = raw_input("([y]es / [n]o / [c]ancel)")
    if c == 'y':
        return True
    elif c == 'n':
        return False
    else:
        return None


def ask_color(parent=None, default=None):
    c = raw_input('Color = ')
    return eval(c)


def message(title, message=None, icon='i'):
    """
    icon : str
        can be one of the following: '?', '!', 'i', 'error', None
    
    """
    if icon:
        title = "%s: %s" % (icon, title)
    print title
    if message:
        print message


class progress:
    def __init__(self, 
                 i_max=None,
                 title="Progress",
                 message="We're getting there...",
                 cancel=True):
        if i_max: 
            end_msg = " %i>" % i_max
        else:
            end_msg = ''
        txt = "%s (%s)%s" % (title, message, end_msg)
        print txt,
        self._i = 0
        self._i_max = i_max
    
    def advance(self, new_msg=None):
        self.i += 1
        if self._i_max:
            print self._i_max - self._i,
        else:
            print self._i
    
    def terminate(self):
        print ']'


def copy_file(path):
    """
    copies a file to the clipboard
    
    """
    raise NotImplementedError


def copy_text(text):
    """
    copies a file to the clipboard
    
    """
    raise NotImplementedError
