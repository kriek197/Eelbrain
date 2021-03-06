"""
Colorspaces provides colormaps for plotting functions. A segment's properties
dictionary can contain a colormap to provide defaults to plotting functions.

This module provides functions to create some default colorspaces (the ``get_...`` 
functions), and custom colorspaces can be created using the Colorspace class.


"""

import numpy as np
#import matplotlib.pyplot as plt
import matplotlib as mpl




class Colorspace:
    """
    - Stores information for mapping segment data to colors
    - can plot a colorbar for the legend with toax(ax) method
    """
    def __init__(self, vmax=None, vmin=None, cmap=None, 
                 # contours: {v -> color} 
                 contours={},
                 # decoration
                 sensor_color='k', sensor_marker='x', cbar_data='vrange',
                 unit=None, ticks=None, ticklabels=None):
        """
        cmap:
            matplotlib colormap (default is ``mpl.cm.jet``)
        unit: str
            the unit of measurement (used for labels)
        vmax, vmin:
            max and min values that the colormap should be mapped to. If 
            vmin is not specified, it defaults to -vmax.
            
         
        """
        # sort out arguments
        self.cmap = cmap
        if cmap:
            self.vmax = vmax
            if (vmin is None) and (vmax is not None):
                vmin = - vmax
            self.vmin = vmin
        
        self.unit = unit
        self.ticks = ticks # = r_[0.:length:samplingrate/testWindowFreq ]
        self.ticklabels = ticklabels # = (ticks/samplingrate)-start
        self.sensor_color = sensor_color
        self.sensor_marker = sensor_marker
        
        if cbar_data=='vrange':
            self.cbar_data = [(vmin, vmax)]
        else:
            self.cbar_data = cbar_data
        
        # contour
        self.contours = contours
        self.contour_kwargs = {'linestyles': 'solid'}
    
    def get_imkwargs(self):
        kwargs = {'vmin': self.vmin,
                  'vmax': self.vmax,
                  'cmap': self.cmap}
        return kwargs
    
    def get_contour_kwargs(self):
        """
        Example::
        
            >>> map_kwargs = {'origin': "lower", 
                              'extent': (emin, emax, emin, emax)}
            >>> map_kwargs.update(colorspace.get_contour_kwargs())
            >>> ax.contour(im, **map_kwargs)
        
        """
        levels = sorted(self.contours)
        d = {'levels': levels,
             'colors': [self.contours[l] for l in levels],
             }
        d.update(self.contour_kwargs)
        return d
    
    def toax(self, ax, data='auto', num=1001):   # NEW !!
        "kwarg data: data to use for plot (array)"
        if data=='auto':
            num_part = num / len(self.cbar_data)
            data = np.hstack([np.linspace(x1,x2, num=num_part) for x1,x2 in self.cbar_data])
        if data.ndim==1:
            data = data[None,:]
        #print data[:,::20]
        #print self.vmin, self.vmax
        ax.imshow(data, cmap=self.cmap, aspect='auto', extent=(0,num,0,1), vmin=self.vmin, vmax=self.vmax)
        #labelling
        ax.set_xlabel(self.unit)
        if self.ticks == None:
            ticks =  ax.xaxis.get_ticklocs() 
            ticks = np.unique(np.clip( ticks.astype(int), 0, num-1 )).astype(int)
            ticklabels = data[0,ticks]
        else:
            ticks = np.hstack([np.max(np.where(data[0]<=t)[0]) for t in self.ticks])
        if self.ticklabels == None:
            ticklabels = data[0,ticks]
        else:
            ticklabels = self.ticklabels
        ax.xaxis.set_ticks(ticks)
        ax.xaxis.set_ticklabels(ticklabels)
        ax.yaxis.set_visible(False)
    


def colorbars_toFig_row_(cspaces, fig, row, nRows=None):
    """plots several colorbars into one row of a figure"""
    # interpret / prepare arguments
    if nRows == None:
        nRows = row
    if not np.iterable(cspaces):
        cspaces = [cspaces]
#    nCols = len(cspaces)
    # plot
    ysize = 1./nRows
    ymin = ysize*( nRows-row +.5)
    height = ysize/5
    xmin = np.r_[0.:len(cspaces)] /len(cspaces) + .1/len(cspaces)
    width = .8/len(cspaces)
    for i,c in enumerate( cspaces ):
        #ax = fig.add_subplot(nRows, nCols, nCols*(row-1)+i+1)
        ax=fig.add_axes([xmin[i], ymin, width, height])
        c.toax(ax)
        #c.toAxes_(ax)





# MARK: colorspace factories


def _get_polar_cmap():
    cdict = {'red':[(0.,  .0,  .0),
                    (.5, 1.,  1.),
                    (1.,  1.0,  1.0)],
         'green':  [(0.0,  0.,  0.),
                    (.5, 1.,  1.),
                    (1.0,  0.,   0.)],
         'blue':   [(0.0,  1.0,  1.0),
                    (.5,  1.,  1.),
                    (1.0,  0.,  0.)]}
    cmap = mpl.colors.LinearSegmentedColormap("polarCmap", cdict)
    cmap.set_bad('w', alpha=0.)
    return cmap

def get_default():
    return Colorspace(cmap=mpl.cm.jet)


def get_EEG(vmax=1.5, unit=r'$\mu V$', p='unused', **kwargs):
    kwargs['cmap'] = _get_polar_cmap()
    return Colorspace(vmax, unit=unit, **kwargs)

def get_MEG(vmax=2e-12, unit='Tesla', p='unused', **kwargs):
    kwargs['cmap'] = _get_polar_cmap()
    return Colorspace(vmax, unit=unit, **kwargs)


'''
def phaseCmap():
    cdict = {'red':[(0.,  .0,  .0),
                    (.5, 1.,  1.),
                    (1.,  .0,  .0)],
         'green':  [(0.0,  0.,  0.),
                    (.5, 0.,  0.),
                    (1.0,  0.,   0.)],
         'blue':   [(0.0,  1.0,  1.0),
                    (.5,  0.,  0.),
                    (1.0,  1.,  1.)]}
    cmap = colors.LinearSegmentedColormap("phaseCmap", cdict)
    cmap.set_bad('w', alpha=0.)
    return cmap
#def phaseColorspace():
#    return Colorspace( phaseCmap(), 
'''


# black, red-yellow for significant
def get_sig(p=.05, vmax='unused', **kwargs): #intercept vmin/vmax aras
        pstr = str(p)[1:]
        kwargs['ticks'] = [0, p]
        kwargs['ticklabels'] = ['0', pstr]
        kwargs['sensor_color'] = '.5'
        kwargs['cbar_data'] = [(0, 1.5*p)]
        
        cdict = {'red':[(0.0,   1.,     1.),
                        (p,     1.,     0.),
                        (1.0,   0.,     0.)],
             'green':  [(0.0,   1.,     1.),
                        (p,     .0,     0.),
                        (1.0,   0.,     0.)],
             'blue':   [(0.0,   0.,     0.),
                        (p,     0.,     0.),
                        (1.0,   0.,     0.)]}
        cmap = mpl.colors.LinearSegmentedColormap("sigCmap", cdict, N=1000)
        cmap.set_bad('w', alpha=0.)
        return cmap
                        
        return Colorspace(vmax=1, vim=0, unit='p', **kwargs)


# white, red-yellow for significant
def get_sig_white(p=.05, vmax='unused', **kwargs):
    pstr = str(p)[1:]
    
    cdict = {'red':[(0.0,   1.,     1.),
                    (p,     1.,     1.),
                    (1.0,   1.,     1.)],
         'green':  [(0.0,   1.,     1.),
                    (p,     .0,     1.),
                    (1.0,   1.,     1.)],
         'blue':   [(0.0,   0.,     0.),
                    (p,     0.,     1.),
                    (1.0,   1.,     1.)]}
    cmap = mpl.colors.LinearSegmentedColormap("sig White", cdict, N=1000)
    cmap.set_bad('w', alpha=0.)
    kwargs['cmap'] = cmap
    
    return Colorspace(vmax=1, vmin=0, unit='p',
                      ticks=[0,p], ticklabels=['0',pstr],
                      sensor_color='.5', cbar_data=[(0, 1.5*p)],
                      **kwargs)


def get_symsig(p=.05, contours=[], vmax='unused', **kwargs):
    pstr = str(p)[1:]
    cs_kwargs = {'ticks': [-1, -1+p, 1-p, 1],
                 'ticklabels': ['0', pstr, pstr, '0'],
                 'sensor_color': '.5',
                 'cbar_data': [(-1, -1+2*p), (1-2*p, 1)],
                 }
    cs_kwargs.update(kwargs)
    if contours:
        if np.isscalar(contours):
            contours = [contours]
        cont = []
        for c in contours:
            cont += [1-c, -1+c]
        cs_kwargs['contours'] = cont

    cdict = {'red':   [(0.,     1.,     1.),
                   (p/2,   .25,    0.),
                   (1.-p/2,   0.,     1.),
                   (1.,     1.,     1.)],
         'green': [(0.0,    0.,     0.),
                   (1.-p/2,   0.,     0.),
                   (1.,     1.,     1.)],
         'blue':  [(.0,     1.,     1.),
                   (p/2,   1.,     0.),
                   (1.0,    0.,     0.)]}
    cmap = mpl.colors.LinearSegmentedColormap("sigCmapSym", cdict, N=2000)
    cmap.set_bad('w', alpha=0.)
    
    return Colorspace(vmax=1, vmin=-1, unit='$p$', cmap=cmap, **cs_kwargs)


