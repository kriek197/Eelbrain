"""
Topographic maps
================


Figure Types
------------

butterfly:
    plot a butterfly plot and a corresponding topomap 
series:
    Plot a series of topomaps with mean data for each time bin
topomap:
    plot individual topomaps
xbyx: 
    Plot a uts array and dynamic topomaps


topomap kwargs
--------------

plotSensors:
    mark sensor locations on a topomap; False, True, or list of sensor IDs

"""

from __future__ import division


#import time

import numpy as np
import matplotlib.pyplot as _plt
import wx

from eelbrain.vessels import colorspaces as cs
from eelbrain.wxutils import mpl_canvas
import _base
import uts


__hide__ = ['cs', 'test', 'uts']



class butterfly(mpl_canvas.CanvasFrame): #_base.CallbackFigure
    """
    Butterfly plot with corresponding topomap
    
    """
    def __init__(self, epochs, size=2.5, bflywidth=2, dpi=90, 
                 res=50, interpolation='nearest', 
                 title=True, xlabel=True, ylabel=True,
                 color=None, sensors=None, ylim=None):
        """
        
        size : float
            in inches: height of the butterfly axes and side length of the 
            topomap axes
        bflywidth : float
            multiplier for the width of butterfly plots based on their height
        
        """
        epochs = self.epochs = _base.unpack_epochs_arg(epochs)
        
        # create figure
        n_plots = len(epochs)
        x_size = size * (1 + bflywidth)
        y_size = size * n_plots
        # old
#        figsize = (x_size, y_size)
#        fig = self.create_figure(figsize=figsize, facecolor='w', dpi=dpi)
        # new
        parent = wx.GetApp().shell
        title = "plot.topo.butterfly"
        mpl_canvas.CanvasFrame.__init__(self, parent, title, dpi=dpi)
        fig = self.figure
        
        # plot epochs (x/y are in figure coordinates)
        x_axsep = 1 - (size / x_size)
        y_axsep = 1 / n_plots
        frame = .05
        frame_lbl = frame * 2
        
        self.topo_kwargs = {'res': res,
                            'interpolation': interpolation}
        
        t = 0
        self.topo_axes = []
        self.t_markers = []
        self.topos = []
        for i, layers in enumerate(epochs):
            y_bottom = 1 - y_axsep * (1 + i) 
            ax1_rect = [frame, 
                        y_bottom + frame_lbl, 
                        x_axsep - 2 * frame, 
                        y_axsep - frame_lbl - frame]
            ax2_rect = [x_axsep + frame, 
                        y_bottom + frame, 
                        1 - x_axsep - 2 * frame, 
                        y_axsep - 2 * frame]
            ax1 = fig.add_axes(ax1_rect)
            ax1.ID = i
            t_marker = ax1.axvline(t, color='k')
            
            ax2 = fig.add_axes(ax2_rect, frameon=False)
            ax2.set_axis_off()
            if len(self.topo_axes) == 0:
                ax2.set_title('t = %.3f' % t)
                self._t_title = ax2.title
            
            self.topo_axes.append(ax2)
            self.t_markers.append(t_marker)
            self.topos.append((t_marker, ax2, layers))
            
            uts._ax_butterfly(ax1, layers, sensors=sensors, ylim=ylim, title=title, 
                              xlabel=xlabel, ylabel=ylabel, color=color)
            
        
        # setup callback
        self.canvas.mpl_connect('button_press_event', self._on_click)
        self._realtime_topo = True
        self.canvas.mpl_connect('motion_notify_event', self._on_mouse_motion)
        self.canvas.store_canvas()
        self.set_topo_t(0, draw=False)
        self.Show()
        
    
    def _on_mouse_motion(self, event):
        ax = event.inaxes
        if self._realtime_topo and ax and hasattr(ax, 'ID'):
            self.set_topo_t(event.xdata)
    
    def set_topo_t(self, t, draw=True):
        "set the time point of the topo-maps"
        self._current_t = t
        self._t_title.set_text("t = %.3f" % t)
        for t_marker, topo_ax, layers in self.topos:
            t_marker.set_xdata([t, t])
            
            topo_ax.cla()
            layers = [l.subdata(time=t) for l in layers]
            _ax_topomap(topo_ax, layers, **self.topo_kwargs)
        
        if draw:
            if self._realtime_topo:
                self.canvas.redraw_ax(*self.topo_axes)
            else:
                self.canvas.redraw(axes=self.topo_axes, artists=self.t_markers)
    
    def _on_click(self, event):
        ax = event.inaxes
        if ax and hasattr(ax, 'ID'):
            button = {1:'l', 2:'r', 3:'r'}[event.button]
            if button == 'l':
                self._realtime_topo = False
            elif button == 'r':
                self._realtime_topo = not self._realtime_topo
            self.set_topo_t(event.xdata)
    
    def OnLeaveAxesStatusBarUpdate(self, event):
        "update the status bar when the cursor leaves axes"
        sb = self.GetStatusBar()
        txt = "Topomap: t = %.3f" % self._current_t
        sb.SetStatusText(txt, 0)

    def OnMotionStatusBarUpdate(self, event):
        "update the status bar for mouse movement"
        ax = event.inaxes
        if ax and hasattr(ax, 'ID'):
            super(self.__class__, self).OnMotionStatusBarUpdate(event)



#def topomap(epochs, time=0, size=2.5, labels=True, dpi=50):
#    """ 
#    displays a topographic map
#    
#    """
#    epochs = _base.read_epochs_arg(epochs)
#    epochs = [e.subdata(time=time) for e in epochs]
#    
#    n_plots = len(epochs)
#    fig = _plt.figure(figsize=(n_plots * size, size), dpi=dpi)
#    
#    for i, epoch in enumerate(epochs):
#        ax = _plt.subplot(1, n_plots, i+1)
##        ax.set_axis_off()
#        _ax_topomap(ax, epoch)
#        
#    return fig




def _axgrid_topomaps(nRows, nCols, nAxes = False,
                        header=.25, footer='auto', 
                        figsize=_base.defaults['figsize'], # if one is negative, this dim is derived. 
                                                        # float --> fig width
                        resolution=1,   # (multiplier)
                        frame = .0,      # element size (inches)
                        between = .05,
                        axsize = 'auto',    # if not auto, it overrides figsize
                        structured = True,
                        **kwargs):
    # elements in inches:
    fix_space_x = 2*frame + (nCols-1)*between
    if axsize == 'auto':
        x_inches, y_inches = figsize
        assert x_inches > 0
        axsize = (x_inches - fix_space_x)/nCols
    else:
        x_inches = nCols*axsize + fix_space_x
        y_inches = -1
    if y_inches == -1:
        if footer == 'auto':
            footer = axsize+between
        y_inches = frame*2 + axsize*nRows + \
                   between * (nRows-1+bool(header)+bool(footer)) + \
                   header + footer
    else:
        raise NotImplementedError()
    #x_inches = frame*2 + axsize*nCols + between*(nCols-1)
    fig  = _plt.figure(figsize=(x_inches, y_inches))
    # make axes
    if not nAxes:
        nAxes = nRows * nCols
    axes = []
    width = axsize/x_inches
    height = axsize/y_inches
    left_coords = [(frame + (between+axsize)*u) / x_inches for u in range(nCols)]
    for v in range(nRows-1, -1 , -1):
        bottom = (footer+v*(axsize+between)) / y_inches
        lineaxes = []
        for left in left_coords:
            if nAxes:
                lineaxes.append(_plt.axes((left, bottom, width, height)))
                nAxes -= 1
        if structured:
            axes.append(lineaxes)
        else:
            axes += lineaxes
    return fig, axes





def _plt_topomap(ax, epoch, proj='default', res=100, 
                 im_frame=0.02, # empty space around sensors in the im
                 colorspace=None,
                 **im_kwargs):
    colorspace = _base.read_cs_arg(epoch, colorspace)
    handles = {}
    
    Y = epoch.get_epoch_data()
    Ymap = epoch.sensor.get_im_for_topo(Y, proj=proj, res=res, frame=im_frame)
    
    emin = -im_frame
    emax = 1 + im_frame
    map_kwargs = {'origin': "lower", 
                  'extent': (emin, emax, emin, emax)}
    
    if colorspace.cmap:
        im_kwargs.update(map_kwargs)
        im_kwargs.update(colorspace.get_imkwargs())
        handles['im'] = ax.imshow(Ymap, **im_kwargs)
    
    # contours
    if colorspace.contours:
        #print "contours: {0}".format(colorspace.contours)
        map_kwargs.update(colorspace.get_contour_kwargs())
        h = ax.contour(Ymap, **map_kwargs)
        handles['contour'] = h
    
    return handles



def _ax_topomap(ax, layers, sensors=None, proj='default', **im_kwargs):
    """
    sensors : 
        sensors to plot: list of IDs, or True/'all'
    """
    ax.set_axis_off()
    handles = {}
    for l in layers:
        handles[l.name] = _plt_topomap(ax, l, **im_kwargs)
    
    # plot sensors
    if sensors:
        epoch = layers[0]
        loc2d = epoch.sensor.getLocs2d(proj=proj)
        cs = epoch.properties['colorspace']
        if np.iterable(sensors):
            loc2d = loc2d[sensors]
        h = ax.scatter(loc2d[:,0], loc2d[:,1], 
                       color=cs.sensorColor,
                       marker=cs.sensorMarker, s=6, linewidth=.25)
        handles['sensors'] = h
    
    return handles





# MARK: XBYX plots (ANOVA results plots)


class _Window_Topo:
    """Helper class for array"""
    def __init__(self, ax, pointer_xy, layers):
        self.ax = ax
        self.pointer_xy = pointer_xy
        #initial plot state
        self.t_line = None
        self.pointer = None
        self.layers = layers
    
    def update(self, parent_ax=None, t=None, cs=None, sensors=None):
        if t != None:
            if self.t_line:
                self.t_line.remove()
            self.t_line = parent_ax.axvline(t, c='r')
            #self.pointer.xy=(t,1)
            #self.pointer.set_text("t = %s"%t)
            if self.pointer:
                #print 't =', t
                self.pointer.set_axes(parent_ax)
                self.pointer.xy=(t,1)
                self.pointer.set_text("t = %.3g"%t)
                self.pointer.set_visible(True)
            else:
                self.pointer = parent_ax.annotate("t = %.4g"%t, (t,1), 
                                    xycoords='data',
                                    xytext=self.pointer_xy, 
                                    textcoords='figure fraction',
                                    horizontalalignment='center',
                                    verticalalignment='top',
                                    arrowprops={'width':1, 'frac':0, 
                                                'headwidth':0, 'color':'r', 
                                                'shrink':.05},
                                    zorder=99)
            
            self.ax.cla()
            layers = [l.subdata(time=t) for l in self.layers]
            _ax_topomap(self.ax, layers)
    
    def clear(self):
        self.ax.cla()
        self.ax.set_axis_off()
        if self.t_line:
            self.t_line.remove()
            self.t_line = None
        #self.pointer.set_text(None)
        #print dir(self.pointer)
        if self.pointer:
            self.pointer.set_visible(False)
        #self.pointer.remove()  NOT IMPLEMENTED IN MPL




class array(mpl_canvas.CanvasFrame):
    def __init__(self, epochs, title=None, height=3, width=2.5, ntopo=3, dpi=90,
                 ylim=None, t=[], **kwargs):
        """
        Interface for exploring channel by sample plots by extracting topo-plots
        
        kwargs
        ------
        title
        ntopo=None  number of topoplots per segment (None -> 6 / nplots)
        
        """
        # convenience for single segment
        epochs = _base.unpack_epochs_arg(epochs)
        
        # figure properties
        n_epochs = len(epochs)
        n_topo_total = ntopo * n_epochs
        fig_width, fig_height = n_epochs * width, height
        
        # fig coordinates
        x_frame_l = .1 / n_epochs
        x_frame_r = .025 / n_epochs
        x_per_ax = (1 - x_frame_l - x_frame_r) / n_epochs
        
        # create figure
        parent = wx.GetApp().shell
        if isinstance(title, basestring):
            frame_title = title
        else:
            frame_title = "plot.topo.array"
#        figsize=(fig_width, fig_height)
        mpl_canvas.CanvasFrame.__init__(self, parent, frame_title, dpi=dpi)
        fig = self.figure
        
        fig.subplots_adjust(left = x_frame_l, 
                            bottom = .05, 
                            right = 1 - x_frame_r, 
                            top = .9, 
                            wspace = .1, hspace = .3)
        if title:
            fig.suptitle(title)
        self.title = title
        
        # im_array plots
        self.main_axes=[]
        ax_height = .4 + .075 * (not title)
        ax_bottom = .45# + .05*(not title)
        ax_width = .9 * x_per_ax
        for i,layers in enumerate(epochs):
            ax_left = x_frame_l + i * x_per_ax
            ax = fig.add_axes((ax_left, ax_bottom, ax_width, ax_height),
                              picker=True)  # rect = [left, bottom, width, height]
            self.main_axes.append(ax)
            ax.ID = i
            ax.type = 'main'
            _base._ax_im_array(ax, layers)
            if i > 0:
                ax.yaxis.set_visible(False)
        
        # topo plots
        self.windows=[]
        for i, layers in enumerate(epochs):
            for j in range(ntopo):
                ID = i * ntopo + j
                ax = fig.add_subplot(3, n_topo_total, 2 * n_topo_total + 1 + ID, 
                                     picker=True, xticks=[], yticks=[])
                ax.ID = ID
                ax.type = 'window'
                pointer_xy = (.1 + (.85 / n_topo_total) * (.5 + ID), .3)
                self.windows.append(_Window_Topo(ax, pointer_xy, layers))
        
        # save important properties
        self.epochs = epochs
        
        # if t argument is provided, set topo-pol time points
        if t:
            if np.isscalar(t):
                t = [t]
            self.setwins(*t)
        
        # setup callback
        self._selected_window = None
        self.canvas.mpl_connect('pick_event', self._pick_handler)
        self.canvas.mpl_connect('motion_notify_event', self._motion_handler)
        self.canvas.store_canvas()
        self.Show()
    
    def __repr__(self):
        seg_repr = [('<%r>' % e.name) for e in self.epochs]
        seg_names = ', '.join(seg_repr)
        kwargs = dict(s = seg_names)
        if self.title:
            kwargs['t'] = ' %r' % self.title
        else:
            kwargs['t'] = ''
        txt = "<plot.xbyx{t} ({s})>".format(**kwargs)
        return txt
    
    def set_topo_single(self, topo, t, parent_im_id='auto'):
        "Set the time of a single topomap (numbered throughout the figure)"
        # get parent ax
        if parent_im_id == 'auto':
            parent_im_id = int(topo / self._ntopo)
        parent_ax = self.main_axes[parent_im_id]
        # get window ax
        w = self.windows[topo]
        w.clear()
        # get data
        w.update(parent_ax=parent_ax, t=t)
        self.canvas.draw()
    
    def set_topowin(self, topo_id, t):
        """
        Set the time point for a topo-map (for all xbyx plots; In order to 
        modify a single topoplot, use setone method).
        
        """
        for i in xrange(len(self.main_axes)):
            _topo = self._ntopo * i + topo_id
            self.set_topo_single(_topo, t, parent_im_id=i)
    
    def set_topowins(self, *t_list):
        """
        Set time points for several topomaps (calls self.set() for each value 
        in t_list)
        
        """
        for i, t in enumerate(t_list):
            self.set_topowin(i, t)
    
    def _window_update(self, mouseevent, parent_ax):
        "update a window (used for mouse-over and for pick)"
        t = mouseevent.xdata
        # FIXME: does not refresh properly
        self._selected_window.update(parent_ax=parent_ax, t=t)
        self.canvas.redraw_ax(self._selected_window.ax)
    
    def _pick_handler(self, pickevent):
        mouseevent = pickevent.mouseevent
        ax = pickevent.artist
        button = {1:'l', 2:'r', 3:'r'}[mouseevent.button]
        if ax.type=='window':
            window = self.windows[ax.ID]
            if button == 'l':
                self._selected_window = window
            elif button == 'r':
                window.clear()
                self.canvas.draw()
            else:
                pass
        elif (ax.type == 'main') and (self._selected_window != None):
            self._selected_window.clear() # to side track pdf export transparency issue
            self._window_update(mouseevent, ax)
            self._selected_window = None
            self.canvas.draw()
    
    def _motion_handler(self, mouseevent):
        ax = mouseevent.inaxes
        if ax in self.main_axes:
            if self._selected_window != None:
                self._window_update(mouseevent, ax)


