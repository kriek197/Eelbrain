"""
A few basic operations needed throughout Eelbrain

Created by Christian Brodbeck on 7/3/09.
"""

import os
import cPickle as pickle

import numpy as np

from eelbrain import ui


class intervals:
    """Iterator over each successive pair in a list.
    
    >> intervals([1,2,3, 45])
    (1, 2)
    (2, 3)
    (3, 45) """
    def __init__(self, l):
        self.l = l
        self.i=0
        if len(self.l) < 2:
            raise StopIteration
    def __iter__(self):
        return self
    def next(self):
        self.i += 1
        if len(self.l)<=self.i:
            raise StopIteration
        return self.l[self.i-1],self.l[self.i]


def toTuple(items):
    """
    makes sure items is a tuple
    """
    if not type(items) in [list, tuple, set]:
        items = (items,)
    else:
        items = tuple(items)
    return items

def toList(items):
    """
    makes sure items is a list
    """
    if not type(items) in [list, tuple, set]:
        items = [items]
    else:
        items = list(items)
    return items



# IO operations

def add_ext(path, ext, multiple=False, ask_overwrite=True):
    """
    Adds ext to path; 
    
    kwargs
    -----
    multiple=False: 
        =False: if path has an extension, nothing will be done
        ='r', 'replace': existing extension will be replaced.
        ='a', 'add': extension will be added independent of existing extension
    """
    name, old_ext = os.path.splitext(path)
    # remove leading dots
    old_ext = old_ext.lstrip(os.path.extsep)
    ext = ext.lstrip(os.path.extsep)
    # modify
    if old_ext:
        if multiple in ['r', 'replace']:
            pass
        elif  (multiple in ['a', 'add'])  and  (old_ext != ext):
            ext = os.path.extsep.join([old_ext, ext])
        else:
            ext = old_ext
    
    path = os.path.extsep.join([name, ext])
    if ask_overwrite:
        if os.path.exists(path):
            if not ui.ask(title="Overwrite File?",
                          message="The File '%s' already exists. Overwrite the existing file?"%path):
                return None
    return path
    

def loadtable(path, d='\t', txt='"', dtype=float, txtcols=[], txtrows=[], 
              empty=np.NaN):
    """
    loads a table from a file. If extension is '.pickled' or '.pickle', the 
    file will simply be unpickled. Otherwise it will be read as a table-
    separated-values (TSV) file.
    
    kwargs
    ------
    d: delimiter
    txt: string indicator
    dtype: data type for conversion if not string
    textcols/textrows: columns and rows that should be interpreted as text 
                       instead of dtype
    empty: replace empty strings with this value
    
    """
    name, ext = os.path.splitext(path)
    if ext in ['.pickled', '.pickle']:
        with open(path) as f:
            table = pickle.load(f)
    else:
        raw_table = []
        for line in open(path):
            row = line.replace('\n','')
            if len(row) > 0:
                raw_table.append(row.split(d))
        # data conversion
        table = []
        for i, row in enumerate(raw_table):
            if i in txtrows:
                table.append(row)
            else:
                row_c = []
                for j, val in enumerate(row):
                    if j in txtcols:
                        row_c.append(val.replace(txt, ''))
                    else:
                        if len(val) == 0:
                            val_c = empty
                        elif val[0] == txt:
                            val_c = val.replace(txt, '')
                        else:
                            try:
                                val_c = dtype(val)
                            except:
                                val_c = val
                        row_c.append(val_c)
                table.append(row_c)
    return table


def test_attr_name(name, printname=None):
    """
    Test whether name is a proper attribute name. Raises an Error if it is not.
    
    :arg printname: use this argument if the name that should be printed in 
        the error message diffes from the name to be tested (e.g. when name is
        formatted with dummy items)
    
    """
    assert isinstance(name, str)
    if printname is None:
        printname = name
    if name.startswith('_'):
        raise ValueError("Invalid ExpermentItem name: %r (Cannot start with"
                         "'_')" % printname)
    elif name[0].isdigit():
        raise ValueError("Invalid ExpermentItem name: %r (Cannot start with"
                         " a number)" % name)
    elif not name.replace('_', 'x').isalnum():
        raise ValueError("Invalid ExpermentItem name: %r (Must be alpha-"
                         "numeric & '_')" % printname)
