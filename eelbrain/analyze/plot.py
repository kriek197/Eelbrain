'''
Plotting psystats objects.

'''
from __future__ import division

import logging

import numpy as np
import scipy as sp
import scipy.stats # without this sp.stats is not available
import matplotlib.pyplot as P
import matplotlib as mpl

from eelbrain import fmtxt as textab 

import test

from eelbrain.vessels.data import isfactor, asfactor, isvar, asvar, ismodel, asmodel
from eelbrain.vessels.data import _split_Y, multifactor
from eelbrain.vessels.structure import celltable


__hide__ = ['division', 'scipy',
            'textab', 'test',
            'isfactor', 'asfactor', 'isvar', 'asvar', 'ismodel', 'asmodel',
             'celltable', 'multifactor', 
            ]



defaults = dict(title_kwargs = {'size': 14,
                                'family': 'serif'},
              mono = False, # use monochrome instead of colors
              # defaults for color
              hatch = ['','','//','','*', 'O', '.', '', '/', '//'],
              linestyle = ['-', '-', '--', ':'],
              c = {'pw': ['#00FF00','#FFCC00','#FF6600','#FF3300'],
#                   'colors': ['.3', '.7', '1.', '1.'],
                   'colors': [(0.99609375, 0.12890625, 0.0), 
                              (0.99609375, 0.5859375, 0.0), 
                              (0.98046875, 0.99609375, 0.0), 
                              (0.19921875, 0.99609375, 0.0)],
                   'markers': ['o', 'o', '^', 'o'],
                   },
              # defaults for monochrome
              cm = {'pw': ['.6','.4','.2','.0'],
                    'colors': ['.3', '.7', '1.', '1.'],
                    'markers': ['o', 'o', '^', 'o'],
                    },
                ) # set by __init__








def _mark_plot_pairwise(ax, data, within, par, y_min, y_unit, x0=0,
                        levels=True, trend=".", pwcolors=None,
                        font_size=P.rcParams['font.size'] * 1.5
                        ):
    "returns y_max"
    if levels is not True: # to avoid test.star() conflict 
        trend = False
    # tests
    if not pwcolors:
        if defaults['mono']:
            pwcolors = defaults['cm']['pw'][1-bool(trend):]            
        else:
            pwcolors = defaults['c']['pw'][1-bool(trend):]
    k = len(data)
    tests = test._pairwise(data, within=within, parametric=par, trend=trend,
                            levels=levels)
    reservation = np.zeros((k, k-1))
    y_top = y_min # track top of plot
    y_start = y_min + 2 * y_unit
    # loop through possible connections
    for distance in xrange(1, k):
        for i in xrange(0, k - distance):
            j = i + distance # i, j are data indexes for the categories being compared 
            index = tests['pw_indexes'][(i, j)]
            stars = tests['stars'][index]
            if stars:
                c = pwcolors[stars-1]
                symbol = tests['symbols'][index]
                
                free_levels = np.where(reservation[:,i:j].sum(1) == 0)[0]
                level = min(free_levels)
                reservation[level, i:j] = 1
                
                y1 = y_start + 2 * y_unit * level
                y2 = y1 + y_unit
                y_top = max(y2, y_top)
                x1 = (x0 + i) + .025
                x2 = (x0 + j) - .025
                ax.plot([x1,x1,x2,x2], [y1, y2, y2, y1], color=c)
                ax.text((x1+x2)/2, y2, symbol, color=c, size=font_size,
                        horizontalalignment='center', clip_on=False,
                        verticalalignment='center', backgroundcolor='w')
    y_top = y_top + 2 * y_unit
    return y_top

def _mark_plot_1sample(ax, data, within, par, y_min, y_unit, x0=0, 
                        levels=True, trend=".", pwcolors=None,
                        popmean=0, #<- mod
                        font_size=P.rcParams['font.size'] * 1.5
                        ):
    "returns y_max"
    if levels is not True: # to avoid test.star() conflict 
        trend = False
    # tests
    if not pwcolors:
        if defaults['mono']:
            pwcolors = defaults['cm']['pw'][1-bool(trend):]            
        else:
            pwcolors = defaults['c']['pw'][1-bool(trend):]
    # mod
    ps = []
    if par:
        for d in data:
            t, p = scipy.stats.ttest_1samp(d, popmean)
            ps.append(p)
    else:
        raise NotImplementedError("nonparametric 1-sample test") 
    stars = test.star(ps, out=int, levels=levels, trend=trend)
    stars_str = test.star(ps, levels=levels, trend=trend)
    if any(stars):
        y_stars = y_min + 1.75 * y_unit
        for i, n_stars in enumerate(stars):
            if n_stars > 0:
                c = pwcolors[n_stars-1]
                P.text(x0+i, y_stars, stars_str[i], color=c, size=font_size,
                       horizontalalignment='center', clip_on=False,
                       verticalalignment='center')
        return y_min + 4 * y_unit
    else:
        return y_min


class _simple_fig():
    def __init__(self, title=None, xlabel=None, ylabel=None, 
                 titlekwargs=defaults['title_kwargs'], 
                 ax=None, yticks=None,
                 figsize=(2.5,2.5), 
                 xtick_rotation=0, ytick_rotation=0):
        #axes
        if ax is None:
            self.fig = P.figure(figsize=figsize)
            ax_x0 = .025 + .07*bool(ylabel)
            ax_y0 = .065 + .055*bool(xlabel)
            ax_dx = .975 - ax_x0
            ax_dy = .95 - ax_y0 - .08*bool(title)
            self.rect = [ax_x0, ax_y0, ax_dx, ax_dy]
            ax = self.ax = P.axes(self.rect)
            self.owns_axes = True
        else:
            self.ax = ax
            self.owns_axes = False
        
        # ticks / tick labels
        self._yticks = yticks
        self._x_tick_rotation = xtick_rotation
        self._y_tick_rotation = ytick_rotation
        xax = ax.get_xaxis()
        xax.set_ticks_position('none')
        
        # collector for handles for figlegend
        self._handles = []
        self._legend = None

        # title and labels
        if title:
#            if 'position' not in titlekwargs:
#                titlekwargs['position'] = [.5,2]
            if 'verticalalignment' not in titlekwargs:
                titlekwargs['verticalalignment'] = 'bottom' 
            ax.set_title(title, **titlekwargs)
        if ylabel:
            ax.set_ylabel(ylabel)#, labelpad=-20.)
        if xlabel:
            ax.set_xlabel(xlabel)
    def add_legend_handles(self, *handles):
        for handle in handles:
            label = handle.get_label()
            if not self.legend_has_label(label):
                self._handles.append(handle)
    def legend_has_label(self, label):
            return any(label==h.get_label() for h in self._handles)
    def legend(self, loc=0, fig=False, zorder=-1, ncol=1):
        "add a legend to the plot"
        if fig:
            l = P.figlegend(self._handles, 
                            (h.get_label() for h in self._handles), loc,
                            ncol=ncol)
            self._legend = l
        else:
            l = P.legend(loc=loc, ncol=ncol)
            if l:
                l.set_zorder(-1)
            else:
                raise ValueError("No labeled plot elements for legend")
    def finish(self):
        "resizes the axes to take into account tick spacing"
        
        if self._yticks:
            yticks = self._yticks
            if np.iterable(yticks[0]):
                locations, labels = yticks
            else:
                locations = yticks
                labels = None
            self.ax.set_yticks(locations)
            if labels:
                self.ax.set_yticklabels(labels)
        if self._x_tick_rotation:
            for t in self.ax.get_xticklabels():
                t.set_rotation(self._x_tick_rotation)
        if self._y_tick_rotation:
            for t in self.ax.get_yticklabels():
                t.set_rotation(self._y_tick_rotation)
        
        if self.owns_axes:
            # adjust the position of the aces to show all labels
            P.draw()
            if P.get_backend() == 'WXAgg':
                P.show()
            x_in, y_in = self.fig.get_size_inches()
            dpi = self.fig.get_dpi()
            border_x0 = 0.05 # in inches
            border_x1 = 0.05 # in inches
            border_y0 = 0.05 # in inches
            border_y1 = 0.05 # in inches
            if self._legend:
                w = self._legend.get_window_extent()
                border_y0 += w.ymax / dpi
            
#            # only shrink axes
#            xmin = 0
#            ymin = 0
#            xmax = x_in * dpi
#            ymax = y_in * dpi
            # also expand axes
            xmin = x_in * dpi
            ymin = y_in * dpi
            xmax = 0
            ymax = 0
            for c in self.ax.get_children():
                try:
                    w = c.get_window_extent()
                except:
                    pass
                else:
                    xmin = min(xmin, w.xmin)
                    ymin = min(ymin, w.ymin)
                    xmax = max(xmax, w.xmax)
                    ymax = max(ymax, w.ymax)
            
            for label in self.ax.get_ymajorticklabels() +\
                         [self.ax.get_yaxis().get_label()]:
                w = label.get_window_extent()
                xmin = min(xmin, w.xmin)
            
            for label in self.ax.get_xmajorticklabels() +\
                         [self.ax.get_xaxis().get_label()]:
                w = label.get_window_extent()
                ymin = min(ymin, w.ymin)
            
            # to figure proportion
            xmin = (xmin / dpi - border_x0) / x_in
            xmax = (xmax / dpi + border_x1 - x_in) / x_in
            ymin = (ymin / dpi - border_y0) / y_in
            ymax = (ymax / dpi + border_y1 - y_in) / y_in
            
            p = self.ax.get_position()
            p.x0 -= xmin
            p.x1 -= xmax
            p.y0 -= ymin
            p.y1 -= ymax
            self.ax.set_position(p)
                    
            P.draw()




def boxplot(Y, X=None, match=None, sub=None, datalabels=None,
            bottom=None, 
            title=None, ylabel=True, xlabel=True,
            titlekwargs=defaults['title_kwargs'],
            baseline=None, # category for plot of difference values
            ## pairwise kwargs
            test=True, par=True, trend=".", pwcolors=None,
            hatch = False, colors=False, 
            **simple_kwargs
            ):
    """
    
    :arg var Y:
    :arg X:
    
    :arg test: True (default): perform pairwise tests;  False/None: no tests;
        scalar: 1-sample tests against this value 

    :arg float datalabels: threshold for labeling outliers (in std)
    :arg baseline: Use one condition in X as baseline for plotting and test other conditions
        against this baseline (instead of pairwise)
    
    """
    # kwargs
    if hatch == True:
        hatch = defaults['hatch']
    if colors == True:
        if defaults['mono']:
            colors = defaults['cm']['colors']
        else:
            colors = defaults['c']['colors']
    # get data
    data, _datalabels, names, within = _split_Y(Y, X, match=match, sub=sub)
    # ylabel
    if ylabel is True:
        if hasattr(Y, 'name'):
            ylabel = textab.texify(Y.name)
        else:
            ylabel = False
    # xlabel
    if xlabel is True:
        if hasattr(X, 'factor_names'):
            xlabel = textab.texify(X.factor_names)
        else:
            xlabel = False
    # get axes     
    fig = _simple_fig(title, xlabel, ylabel, titlekwargs, **simple_kwargs)
    ax = fig.ax

    # diff (plot difference values instead of abs)
    if baseline is not None:
        if not match:
            raise NotImplementedError("baseline for between-design")
        if not isinstance(baseline, basestring):
            baseline = X.cells[baseline]
        diff_i = names.index(baseline)   
        diff_d = data.pop(diff_i)
        data = [d-diff_d for d in data]
        names.pop(diff_i)
    # determine ax lim
    if bottom == None:
        asarray = np.hstack(data)
        if np.min(asarray) >= 0:
            bottom = 0
        else:
            d_min = np.min(asarray)
            d_max = np.max(asarray)
            d_range = d_max - d_min
            bottom = d_min - .05 * d_range
    # boxplot
    k = len(data)
    bp = ax.boxplot(data)
    # Now fill the boxes with desired colors
    if hatch or colors:
        numBoxes = len(bp['boxes'])
        for i in range(numBoxes):
            box = bp['boxes'][i]
            boxX = box.get_xdata()[:5]# []
            boxY = box.get_ydata()[:5]#[]
            boxCoords = zip(boxX, boxY)
            # Alternate between Dark Khaki and Royal Blue
            if len(colors) >= numBoxes:
                c = colors[i]
            else:
                c = '.5'
            if len(hatch) >= numBoxes:
                h = hatch[i]
            else:
                h = '' 
            boxPolygon = mpl.patches.Polygon(boxCoords, facecolor=c, hatch=h, zorder=-999)
            ax.add_patch(boxPolygon)
    if defaults['mono']:
        for itemname in bp:
            P.setp(bp[itemname], color='black')
    #labelling
    P.xticks(np.arange(len(names))+1, names)
    y_min = np.max([np.max(d) for d in data])
    y_unit = (y_min - bottom) / 15
    
    # tests    
    if (test is True) and (not baseline):
        y_top = _mark_plot_pairwise(ax, data, within, par, y_min, y_unit, 
                                    x0=1, trend=trend)
    elif baseline or (test is False) or (test is None):
        y_top = y_min + y_unit
    else:
        P.axhline(test, color='black')
        y_top = _mark_plot_1sample(ax, data, within, par, y_min, y_unit, 
                                   x0=1, popmean=test, trend=trend)

        
    # data labels
    if datalabels:
        for i,d in enumerate(data, start=1):
            indexes = np.where(np.abs(d)/d.std() >= datalabels)[0]
            for index in indexes:
                label = _datalabels[i-1][index]
                ax.annotate(label, (i, d[index]))                
    # set ax limits
    ax.set_ylim(bottom, y_top)
    ax.set_xlim(.5, k+.5)
    # adjust axes rect
    fig.finish()
        



        

def barplot(Y, X=None, match=None, sub=None, 
            test=True, par=True,
            title=None, trend=".",
            # bar settings:
            ylabel='{err}', err='2sem', ec='k', xlabel=True,
            hatch = False, colors=False, 
            bottom=0, c='#0099FF', edgec=None,
            **simple_kwargs
            ):
    """
    
    :arg float bottom: lowest possible value on the y axis (default 0)
    
    :arg test: True (default): perform pairwise tests;  False/None: no tests;
        scalar: 1-sample tests against this value 
    
    
    kwargs:
    
    test:   True: pairwise tests
            False/None: no tests
            scalar: 1-sample tests against this number 
    
    bar: make bar plot (otherwise make box plot)
    
    pwcolors: list of mpl colors corresponding to levels (e.g. ['#FFCC00',
              '#FF6600','#FF3300'] with 3 levels
              
    err: "[x][type]"
         'std' : standard deviation
         '.95ci' : 95% confidence interval (see :func:`stats.CI`)
         '2sem' : 2 standard error of the mean
         
    ylabel formatting:
        {err} = error bar description
    """
    # prepare labels:
    # find label error
    ylabel_app = ''
    if isinstance(err, basestring):
        if err.endswith('ci'):
            if len(err) > 2:
                a = float(err[:-2])
            else:
                a = .95
            ylabel_app = '$\pm %g ci$'%a
        elif err.endswith('sem'):
            if len(err) > 3:
                a = float(err[:-3])
            else:
                a = 1
            ylabel_app = '$\pm %g sem$'%a
        elif err.endswith('std'):
            if len(err) > 3:
                a = float(err[:-3])
            else:
                a = 1
            ylabel_app = '$\pm %g std$'%a
    # ylabel
    if ylabel is True:
        if hasattr(Y, 'name'):
            ylabel = Y.name.replace('_', ' ')
        else:
            ylabel = False
    if '{err}' in ylabel:
        ylabel = ylabel.format(err=ylabel_app) 
    # xlabel
    if xlabel is True:
        if hasattr(X, 'name'):
            xlabel = X.name.replace('_', ' ')
        else:
            xlabel = False

    fig = _simple_fig(title, xlabel, ylabel, **simple_kwargs)
    ax = fig.ax
    
    ct = celltable(Y, X, match=match, sub=sub)
    
    x0,x1,y0,y1 = _barplot(ax, ct,
                           test=test, par=par, trend=trend,
                           # bar settings:
                           err=err, ec=ec,
                           hatch=hatch, colors=colors, 
                           bottom=bottom, c=c, edgec=edgec,
                           return_lim=True)
    
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    
    # figure decoration
    names = [ct.cells[i] for i in ct.indexes]
    P.xticks(np.arange(len(names)), names)
        
    fig.finish()



def _barplot(ax, ct, 
             test=True, par=True, trend=".",
             # bar settings:
             err='2sem', ec='k',
             hatch = False, colors=False, 
             bottom=0, c='#0099FF', edgec=None,
             left=None, width=.5,
             return_lim=False,
             ):
    """
    draw a barplot to axes ax for celltable ct.
    
    return_lim: return axes limits (x0, x1, y0, y1)
    """
    # kwargs
    if hatch == True:
        hatch = defaults['hatch']
    if colors == True:
        if defaults['mono']:
            colors = defaults['cm']['colors']
        else:
            colors = defaults['c']['colors']
    # data
    k = len(ct.cells)
    if left is None:
        left = np.arange(k) - width/2
    height = ct.get_statistic(np.mean, out=np.array)
    y_error = ct.get_statistic(err, out=np.array)
    
             
    # fig spacing
    plot_max = np.max(height + y_error)
    plot_min = np.min(height - y_error)
    plot_span = plot_max - plot_min
    y_bottom = min(bottom, plot_min - plot_span*.05)
    
    # main BARPLOT
    bars = ax.bar(left, height-bottom, width, bottom=bottom, 
                  color=c, edgecolor=edgec, linewidth=1, 
                  ecolor=ec, yerr=y_error)
    
    # hatch
    if hatch:
        for bar, h in zip(bars, hatch):
            bar.set_hatch(h)
    if colors:
        for bar, c in zip(bars, colors):
            bar.set_facecolor(c)
    
    # pairwise tests
    # prepare pairwise plotting
    if y_error == None:
        y_min = np.max(height)
    else:
        y_min = np.max(height + y_error)
    y_unit = (y_min - y_bottom) / 15
    data = [ct.data[i] for i in ct.indexes]
    if test is True:
        y_top = _mark_plot_pairwise(ax, data, ct.all_within, par, y_min, y_unit, 
                                    trend=trend)
    elif (test is False) or (test is None):
        y_top = y_min + y_unit
    else:
        P.axhline(test, color='black')
        y_top = _mark_plot_1sample(ax, data, ct.all_within, par, y_min, y_unit, 
                                   popmean=test, trend=trend)
    
    #      x0,                 x1,                  y0,       y1
    if return_lim:
        lim = (min(left)-.5*width, max(left)+1.5*width, y_bottom, y_top) 
        return lim


def timeplot(Y, categories, time, match=None, sub=None, 
             # data plotting
             main=np.mean,
             spread='box', x_jitter=False,
             datalabels=None,
             # mpl
             ax=None,
             # labelling
             ylabel=True, xlabel=True,
             legend=True, loc=0,
             ## pairwise kwargs
#             pairwise=True, par=True, trend=".", pwcolors=None,
             colors=True, hatch = False, markers=True, 
             **simple_kwargs
             ):
    """
    kwargs
    ------
    
    spread: 'box' - boxplots
            for lineplots:
            'Xsem' X standard error of the means
            'Xstd' X standard deviations
            None -  without 
            
    main: draw lines to connect values across time (default: np.mean)  
          can be 'bar' for barplots or False
    
    datalabels = float (in std) : label outlier data
    
    diff=Value   Use value as baseline for plotting; test other conditions
         agaist baseline (instead of pairwise)
    
    legend: bool or 'fig' to plot figlegend. The kwarg 'loc' is the legend kwarg.
    
    """
    categories = asfactor(categories)
    
    # transform to 3 kwargs:
    # - local_plot ('bar' or 'box')
    # - line_plot (function for values to connect)
    # - spread
    if main=='bar':
        assert spread != 'box'
        local_plot = 'bar'
        line_plot = None
    else:
        line_plot = main
        if spread=='box':
            local_plot = 'box'
            spread = None
        else:
            local_plot = None
    del main
    
    # hatch/marker
    if hatch == True:
        hatch = defaults['hatch']
    if markers == True:
        if defaults['mono']:
            markers = defaults['cm']['markers']
        else:
            markers = defaults['c']['markers']
    
    # colors: {category index -> color, ...}
    colors_arg = colors
    if defaults['mono']:
        colors = dict(zip(categories.indexes, defaults['cm']['colors']))
    else:
        colors = dict(zip(categories.indexes, defaults['c']['colors']))
    colors.update(categories.colors)
    if isinstance(colors_arg, dict):
        colors.update(colors_arg)
    elif isinstance(colors_arg, (tuple, list)):
        colors.update(dict(zip(categories.indexes, colors_arg)))
    
    for c in categories.cells.keys():
        if c not in colors:
            colors[c] = '.5'
    
    color_list  = [colors[i] for i in sorted(colors.keys())]
    
    # ylabel
    if ylabel is True:
        if hasattr(Y, 'name'):
            ylabel = textab.texify(Y.name)
        else:
            ylabel = False
    # xlabel
    if xlabel is True:
        xlabel = textab.texify(time.name)
    
    # get axes     
    fig = _simple_fig(ax=ax, xlabel=xlabel, ylabel=ylabel, **simple_kwargs)
    ax = fig.ax

    # sub
    if sub is not None:
        Y = Y[sub]
        categories = categories[sub]
        time = time[sub]
        match = match[sub]
    
    # categories
    n_cat = len(categories.cells)
    
    # find time points
    if isvar(time):
        time_points = np.unique(time.x)
        n_time_points = len(time_points)
        time_step = min(np.diff(time_points))
        if local_plot in ['box', 'bar']:
            within_spacing = time_step / (2 * n_cat)
            padding = (2 + n_cat/2) * within_spacing
        else:
            within_spacing = time_step / (8 * n_cat)
            padding = time_step / 4 #(2 + n_cat/2) * within_spacing
        
        rel_pos = np.arange(0, n_cat*within_spacing, within_spacing)
        rel_pos -= np.mean(rel_pos)
        
        t_min = min(time_points) - padding
        t_max = max(time_points) + padding
    else:
        raise NotImplementedError("time needs to be var object")
    
    # prepare array for timelines
    if line_plot: 
        line_values = np.empty((n_cat, n_time_points))
    if spread  and  local_plot!='bar':
        yerr = np.empty((n_cat, n_time_points))
    
    # loop through time points
    for i_t, t in enumerate(time_points):
        ct = celltable(Y, categories, match=match, sub=(time==t))
        if line_plot:
            line_values[:,i_t] = ct.get_statistic(line_plot, out=list)
        
        pos = rel_pos + t
        if local_plot == 'box':
            # boxplot
            bp = ax.boxplot(ct.get_data(out=list), positions=pos, widths=within_spacing)
            
            # Now fill the boxes with desired colors
#            if hatch or colors:
#                numBoxes = len(bp['boxes'])
            for i, cat in enumerate(ct.indexes):
                box = bp['boxes'][i]
                boxX = box.get_xdata()[:5]
                boxY = box.get_ydata()[:5]
                boxCoords = zip(boxX, boxY)
                
                c = colors[cat]
                try:
                    h = hatch[i]
                except:
                    h = '' 
                boxPolygon = mpl.patches.Polygon(boxCoords, facecolor=c, hatch=h, zorder=-999)
                ax.add_patch(boxPolygon)
            
            if True: #defaults['mono']:
                for itemname in bp:
                    P.setp(bp[itemname], color='black')
        elif local_plot == 'bar':
            lim = _barplot(ax, ct, test=False, err=spread, #ec=ec,
                           # bar settings:
                           hatch=hatch, colors=color_list, 
                           bottom=0, left=pos, width=within_spacing)
        elif spread:
            yerr[:,i_t] = ct.get_statistic(spread, out=list)
    
    if line_plot:
        # plot means
        x = time_points
        for i, cat in enumerate(sorted(categories.cells.keys())):
            y = line_values[i]
            name = categories.cells[cat]
    
            color = colors[cat]
            
            if hatch:
                ls = defaults['linestyle'][i]
                if color=='1.':
                    color = '0.'
            else:
                ls='-'
            
            if ls == '-':
                mfc = color
            else:
                mfc = '1.'
            
            try:
                marker = markers[i]
            except:
                marker = None
            
            handles = ax.plot(x, y, color=color, linestyle=ls, label=name,
                              zorder=6, marker=marker, mfc=mfc)
            fig.add_legend_handles(*handles)
            
            if spread:
                if x_jitter:
                    x_errbars = x + rel_pos[i]
                else:
                    x_errbars = x
                ax.errorbar(x_errbars, y, yerr=yerr[i], fmt=None, zorder=5,
                            ecolor=color, linestyle=ls, label=name)
    else:
        legend = False
    
    # finalize
    ax.set_xlim(t_min, t_max)
    ax.set_xticks(time_points)
    
    if any (legend is i for i in (False, None)):
        pass
    elif legend == 'fig':
        fig.legend(fig=True, loc='lower center')
    else:
        if legend is True:
            loc = 0
        else:
            loc = legend
        fig.legend(loc=loc)
    
#    ax.set_xticklabels

#    # determine ax lim
#    if bottom == None:
#        asarray = np.hstack(data)
#        if np.min(asarray) >= 0:
#            bottom = 0
#        else:
#            d_min = np.min(asarray)
#            d_max = np.max(asarray)
#            d_range = d_max - d_min
#            bottom = d_min - .05 * d_range
#
#    #labelling
#    P.xticks(np.arange(len(names))+1, names)
#    y_min = np.max([np.max(d) for d in data])
#    y_unit = (y_min - bottom) / 20.
#    if pairwise and (not diff):
#        y_top = _mark_plot_pairwise(ax, data, within, par, y_min, y_unit, 
#                                        x0=1, trend=trend)
#    else:
#        y_top = y_min + y_unit
#    # data labels
#    if datalabels:
#        for i,d in enumerate(data, start=1):
#            indexes = np.where(np.abs(d)/d.std() >= datalabels)[0]
#            for index in indexes:
#                label = _datalabels[i-1][index]
#                ax.annotate(label, (i, d[index]))                
#    # set ax limits
#    ax.set_ylim(bottom, y_top)
#    ax.set_xlim(.5, k+.5)
    # adjust axes rect
    fig.finish()
    return fig



class multitimeplot:
    def __init__(self, figsize=(7,2.5), 
                 tpad = .5, ylim=None,
                 main=np.mean,
                 spread='box', x_jitter=False,
                 datalabels=None,
                 # labelling
                 title=None, ylabel=True, xlabel=True,
                 titlekwargs=defaults['title_kwargs'],
                 ):
        """
        Create an empty template figure for a plot subsuming several 
        :func:`timeplot`s. Add timeplots using the plot method.
        
        :arg ylim: (bottom, top) tuple of scalars; if left at default (None),
            ylim depend on the data plotted.
         
        """
        self._ylim = ylim
        # ylabel
        if ylabel is True:
            self._ylabel = True
            ylabel = False
        else:
            self._ylabel = False
        # xlabel
        if xlabel is True:
            self._xlabel = True
            xlabel = False
        else:
            self._xlabel = False
        
        # transform to 3 kwargs:
        # - local_plot ('bar' or 'box')
        # - line_plot (function for values to connect)
        # - spread
        if main=='bar':
            assert spread != 'box'
            local_plot = 'bar'
            line_plot = None
        else:
            line_plot = main
            if spread=='box':
                local_plot = 'box'
                spread = None
            else:
                local_plot = None
        del main
        self._local_plot = local_plot
        self._line_plot = line_plot
        self._spread = spread
        self._x_jitter = x_jitter
        
        
        self._tstart = None
        self._tend = None
        self._tpad = tpad
        
        self._xticks = []
        self._xticklabels = []
        
        self._headings = [] # collect text objects for headings to adjust y
        # [(forced_y, line, text), ...]
        self._heading_y = None # used heading y
        self._y_unit = 0
        
        # get axes     
        self.fig = _simple_fig(title, xlabel, ylabel, titlekwargs, 
                               figsize=figsize)
        
    def plot(self, Y, categories, time, match=None, sub=None, 
             tskip = 1,
             heading=None, headingy=None,
             colors=True, hatch = False, markers=True):
        """
        Main Args
        ---------
        Y: variable to plot
        categories: factor indicating different categories to plot
        time: variable indicating time
        match: factor which indicates dependent measures (e.g. subject)
        sub: subset
        
        heading: heading for this set (if None, no heading is added)
        headingy: y coordinate on which to plot the heading
         
        kwargs
        ------
        
        spread: 'box' - boxplots
                for lineplots:
                'Xsem' X standard error of the means
                'Xstd' X standard deviations
                None -  without 
                
        main: draw lines to connect values across time (default: np.mean)  
              can be 'bar' for barplots or False
        
        datalabels = float (in std) : label outlier data
        
        diff=Value   Use value as baseline for plotting; test other conditions
             agaist baseline (instead of pairwise)
        
        legend: bool or 'fig' to plot figlegend. The kwarg 'loc' is the legend kwarg.
        
        """
        categories = asfactor(categories)
        
        ax = self.fig.ax
        local_plot = self._local_plot
        line_plot = self._line_plot
        spread = self._spread
        
        #labels
        if self._ylabel is True:
            if hasattr(Y, 'name'):
                ax.set_ylabel(textab.texify(Y.name))
                self._ylabel = False
        if self._xlabel is True:
            ax.set_xlabel(textab.texify(time.name))
            self._xlabel = False
        
        ### same as timeplot() #####  #####  #####  #####  #####  #####
        # hatch/marker
        if hatch == True:
            hatch = defaults['hatch']
        if markers == True:
            if defaults['mono']:
                markers = defaults['cm']['markers']
            else:
                markers = defaults['c']['markers']
        
        # colors: {category index -> color, ...}
        colors_arg = colors
        if defaults['mono']:
            colors = dict(zip(categories.indexes, defaults['cm']['colors']))
        else:
            colors = dict(zip(categories.indexes, defaults['c']['colors']))
        colors.update(categories.colors)
        if isinstance(colors_arg, dict):
            colors.update(colors_arg)
        elif isinstance(colors_arg, (tuple, list)):
            colors.update(dict(zip(categories.indexes, colors_arg)))
        
        for c in categories.cells.keys():
            if c not in colors:
                colors[c] = '.5'
        
        color_list  = [colors[i] for i in sorted(colors.keys())]
        
    
        # sub
        if sub is not None:
            Y = Y[sub]
            categories = categories[sub]
            time = time[sub]
            match = match[sub]
        
        # categories
        n_cat = len(categories.cells)
        
        # find time points
        if isvar(time):
            time_points = np.unique(time.x)
        ### NOT same as timeplot() #####  #####  #####  #####  #####  #####
            if self._tend is None:
                t_add = 0
                self._tstart = time_points[0]
                self._tend = time_points[-1]
            else:
                t_add = self._tend + tskip - time_points[0]
                self._tend = t_add + time_points[-1]
        ### same as timeplot()     #####  #####  #####  #####  #####  #####            
            n_time_points = len(time_points)
            time_step = min(np.diff(time_points))
            if local_plot in ['box', 'bar']:
                within_spacing = time_step / (2 * n_cat)
            else:
                within_spacing = time_step / (8 * n_cat)
            
            rel_pos = np.arange(0, n_cat*within_spacing, within_spacing)
            rel_pos -= np.mean(rel_pos)
            
        ### NOT same as timeplot() #####  #####  #####  #####  #####  #####
            t_min = self._tstart - self._tpad
            t_max = self._tend + self._tpad
        ### same as timeplot()     #####  #####  #####  #####  #####  #####            
        
        else:
            raise NotImplementedError("time needs to be var object")
        
        # prepare array for timelines
        if line_plot: 
            line_values = np.empty((n_cat, n_time_points))
        if spread  and  local_plot!='bar':
            yerr = np.empty((n_cat, n_time_points))
        
        # loop through time points
        ymax = None; ymin = None
        for i_t, t in enumerate(time_points):
            ct = celltable(Y, categories, match=match, sub=(time==t))
            if line_plot:
                line_values[:,i_t] = ct.get_statistic(line_plot, out=list)
            
            pos = rel_pos + t
            if local_plot == 'box':
                # boxplot
                data = ct.get_data(out=list)
                bp = ax.boxplot(data, positions=pos, widths=within_spacing)
                
                ymax_loc = np.max(data)
                ymin_loc = np.min(data)
                
                # Now fill the boxes with desired colors
                for i, cat in enumerate(ct.indexes):
                    box = bp['boxes'][i]
                    boxX = box.get_xdata()[:5]
                    boxY = box.get_ydata()[:5]
                    boxCoords = zip(boxX, boxY)
                    
                    c = colors[cat]
                    try:
                        h = hatch[i]
                    except:
                        h = '' 
                    boxPolygon = mpl.patches.Polygon(boxCoords, facecolor=c, hatch=h, zorder=-999)
                    ax.add_patch(boxPolygon)
                
                if True: #defaults['mono']:
                    for itemname in bp:
                        P.setp(bp[itemname], color='black')
            elif local_plot == 'bar':
                lim = _barplot(ax, ct, test=False, err=spread, #ec=ec,
                               # bar settings:
                               hatch=hatch, colors=color_list, 
                               bottom=0, left=pos, width=within_spacing)
                ymax_loc = lim[1]
                ymin_loc = lim[0]
            elif spread:
                yerr_loc = ct.get_statistic(spread, out=np.array)
                yerr[:,i_t] = yerr_loc
                y_loc = ct.get_statistic(np.mean, out=np.array)
                ymax_loc = max(y_loc + yerr_loc)
                ymin_loc = min(y_loc - yerr_loc)
            
            if ymax is None:
                ymax = ymax_loc
                ymin = ymin_loc
            else:
                ymax = max(ymax, ymax_loc)
                ymin = min(ymin, ymin_loc)
        
        if line_plot:
            # plot means
            x = time_points + t_add
            for i, cat in enumerate(sorted(categories.cells.keys())):
                y = line_values[i]
                name = categories.cells[cat]
        
                color = colors[cat]
                
                if hatch:
                    ls = defaults['linestyle'][i]
                    if color=='1.':
                        color = '0.'
                else:
                    ls='-'
                
                if ls == '-':
                    mfc = color
                else:
                    mfc = '1.'
                
                try:
                    marker = markers[i]
                except:
                    marker = None
                
        ### NOT same as timeplot() #####  #####  #####  #####  #####  #####
                if self.fig.legend_has_label(name):
                    label = None
                else:
                    label = name
                handles = ax.plot(x, y, color=color, linestyle=ls, label=label,
                                  zorder=6, marker=marker, mfc=mfc)
        ### same as timeplot()     #####  #####  #####  #####  #####  #####            
                self.fig.add_legend_handles(*handles)
                
                if spread:
                    if self._x_jitter:
                        x_errbars = x + rel_pos[i]
                    else:
                        x_errbars = x
                    ax.errorbar(x_errbars, y, yerr=yerr[i], fmt=None, zorder=5,
                                ecolor=color, linestyle=ls, label=name)
        
        ### NOT same as timeplot() #####  #####  #####  #####  #####  #####
        # heading
        y_unit = (ymax - ymin) / 10
        if y_unit > self._y_unit:
            for forced_y, ln, hd in self._headings:
                if forced_y is not None:
                    hd.set_y(forced_y + self._y_unit/2)
            self._y_unit = y_unit
        
        if heading:
            x0 = time_points[ 0] + t_add - tskip/4
            x1 = time_points[-1] + t_add + tskip/4
            x = (x0 + x1) / 2
            if headingy is None:
                y = ymax + self._y_unit
                y_text = y + self._y_unit/2
                if self._heading_y is None:
                    self._heading_y = y
                elif y > self._heading_y:
                    self._heading_y = y
                    for forced_y, ln, hd in self._headings:
                        if forced_y is None:
                            hd.set_y(y_text)
                            ln.set_ydata([y, y])
                        # adjust y
                elif y < self._heading_y:
                    y      = self._heading_y
                    y_text = self._heading_y + self._y_unit/2
            else:
                y = headingy
                y_text = y + self._y_unit/2
            
            hd = ax.text(x, y_text, heading, va='bottom', ha='center')
            ln = ax.plot([x0, x1], [y, y], c='k')[0]
            
            self._headings.append((headingy, ln, hd))
            if not self._ylim:
                ax.set_ylim(top=(y + 3*y_unit))
        
        # finalize
        ax.set_xlim(t_min, t_max)
        for t in time_points:
            self._xticks.append(t + t_add)
            self._xticklabels.append('%g'%t)
        
        if self._ylim:
            ax.set_ylim(self._ylim)
        
        ax.set_xticks(self._xticks)
        ax.set_xticklabels(self._xticklabels)
        
        self.fig.finish()
    def add_legend(self, fig=False, loc=0, zorder=-1, **kwargs):
        if fig:
            self.fig.figlegend(loc, **kwargs)
        else:
#            l = P.legend(loc=loc, **kwargs)        
            l = self.fig.ax.legend(loc=loc, **kwargs)        
            l.set_zorder(zorder)
        
        self.fig.finish()



def _reg_line(Y, reg):
    coeff = np.hstack([np.ones((len(reg),1)), reg[:,None]]) 
    (a,b), residues, rank, s = np.linalg.lstsq(coeff, Y)
    regline_x = np.array([min(reg), max(reg)])
    regline_y = a + b * regline_x
    return regline_x, regline_y



def corrplot(Y, X, cat=None, ax=None, title=None, c=['b','r','k','c','p','y','g'], 
             lloc='lower center', lncol=2, figlegend=True, texify=True,
             sub=None,
             xlabel=True, ylabel=True, rinxlabel=True):
    """
    cat: categories
    rinxlabel: print the correlation in the xlabel
    """
    # LABELS
    if xlabel is True:
        xlabel = X.name
        if texify:
            xlabel = textab.texify(xlabel)
    if ylabel is True:
        ylabel = Y.name
        if texify:
            ylabel = textab.texify(ylabel)
    if rinxlabel:
        temp = "\n(r={r:.3f}{s}, p={p:.4f}, n={n})"
        if cat is None:
            r, p, n = test._corr(Y, X, sub)
            s = test.star(p)
            xlabel += temp.format(r=r, s=s, p=p, n=n)
        else:
            pass
    #
    categories = cat
    if ax is None:
        if cat is None:
            fig = P.figure(figsize=(3.5,3.5))
            ax = P.axes([.2, .15,
                         .75, .95-.1*bool(title)-.15*figlegend])
        else:
            fig = P.figure(figsize=(3.5,4))
            ax = P.axes([.2, .12+.15*figlegend,
                         .75, .85-.06*bool(title)-.15*figlegend])
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    
    # SUB
    if sub is not None:
        Y = Y[sub]
        X = X[sub]
        if isfactor(categories) or ismodel(categories):
            categories = categories[sub]
    
    if isfactor(categories) or ismodel(categories):
        if ismodel(categories):
            categories = multifactor(categories.factors)
        labels = []; handles = []
        for col,i in zip(c, np.unique(categories.x)):
            Xi = X[categories==i]    
            Yi = Y[categories==i]
            label = categories.cells[i]
            if texify: label = textab.texify(label)
            labels.append(label)
            handles.append(ax.scatter(Xi.x, Yi.x, c=col, label=label, alpha=.5))
        if figlegend:
            ax.figure.legend(handles, labels, lloc, ncol=lncol)
        else:
            ax.legend(lloc, ncol=lncol)
    else:
        if categories is None:
            ax.scatter(X.x, Y.x, alpha=.5)
        else:
            ax.scatter(X[categories].x, Y[categories].x, alpha=.5)
    return ax


def regplot(Y, regressor, categories=None, match=None, sub=None,
            ax=None, ylabel=True, title=None, alpha=.2, legend=True,
            c=['#009CFF','#FF7D26','#54AF3A','#FE58C6','#20F2C3']):
    """
    parameters
    ----------
    alpha: alpha for individual data points (to control visualization of 
           overlap)
    legend: applies if categories != None: possible values [True, False] or
            mpl ax.legend() loc kwarg 
            http://matplotlib.sourceforge.net/api/axes_api.html#matplotlib.axes.Axes.legend
            
    """
    # data types
    Y = asvar(Y)
    if isfactor(regressor):
        assert len(regressor.cells) == 2
    else:
        regressor = asvar(regressor)
    
    if ylabel is True:
        ylabel = Y.name
    
    if sub != None:
        Y = Y[sub]
        regressor = regressor[sub]
        if categories != None:
            categories = categories[sub]
        if match != None:
            match = match[sub]
    # match 
    if match != None:
#        Y = Y[match]
#        regressor = regressor[match]
#        if categories != None:
        raise NotImplementedError("match kwarg")
    # get axes
    if ax==None:
        if np.min(Y.x) < 0:
            ylabel_space = .07 * bool(ylabel)
        else:
            ylabel_space = .04 * bool(ylabel)
        fig = P.figure(figsize=(3,3))
        ax = P.axes([.1 + ylabel_space*bool(ylabel),
                     .125,
                     .85 - ylabel_space/2*bool(ylabel),
                     .85 - .06*bool(title) - .025])
    # labels
    if ylabel:
        ax.set_ylabel(ylabel)
    ax.set_xlabel(regressor.name)
    if title:
        ax.set_title(title, **defaults['title_kwargs'])
    # regplot
    scatter_kwargs = {'s': 100,
                      'alpha': alpha,
                       'marker': 'o',
                       'label': '_nolegend_'}
    if categories == None:
        if type(c) in [list, tuple]:
            color = c[0]
        else:
            color = c
        y = Y.x
        reg = regressor.x
        ax.scatter(reg, y, edgecolor=color, facecolor=color, **scatter_kwargs)
        x, y = _reg_line(y, reg)
        ax.plot(x, y, c=color)
    else:
        categories = asmodel(categories)
        categories = multifactor(categories.effects)
        for i, (name, indexes) in enumerate(categories.iter_n_i()):
            # scatter
            y = Y.x[indexes]
            reg = regressor.x[indexes]
            color = c[i % len(c)]
            ax.scatter(reg, y, edgecolor=color, facecolor=color, **scatter_kwargs)
            # regression line
            x, y = _reg_line(y, reg)
            ax.plot(x, y, c=color, label=name)
        if legend == True:
            ax.legend()
        elif legend != False:
            ax.legend(loc=legend)


# MARK: Requirements for Statistical Tests

def _difference(data, names):
    "data condition x subject"
    data_differences = []; diffnames = []; diffnames_2lines = []
    for i, (name1, data1) in enumerate(zip(names, data)):
        for name2, data2 in zip(names[i+1:], data[i+1:]):
            data_differences.append(data1 - data2)
            diffnames.append('-'.join([name1, name2]))
            diffnames_2lines.append('-\n'.join([name1, name2]))
    return data_differences, diffnames, diffnames_2lines




def _normality_plot(ax, data, **kwargs):
    """helper fubction for creating normality test figure"""
    n, bins, patches = ax.hist(data, normed=True, **kwargs)
    data = np.ravel(data)
    
    # normal line
    mu  = np.mean(data)
    sigma = np.std(data)
    y = mpl.mlab.normpdf(bins, mu, sigma)
    ax.plot(bins, y, 'r--', linewidth=1)
    
    # TESTS
    # test Anderson
    A2, thresh, sig = sp.stats.morestats.anderson(data)
    index = sum(A2 >= thresh)
    if index > 0:
        ax.text(.95, .95, '$^{*}%s$'%str(sig[index-1]/100), color='r', size=11,
                horizontalalignment='right', 
                verticalalignment='top',
                transform=ax.transAxes, )
    logging.debug(" Anderson: %s, %s, %s"%(A2, thresh, sig))
    # test Lilliefors
    n_test = test.lilliefors(data)
    ax.set_xlabel(r"$D=%.3f$, $p_{est}=%.2f$"%n_test) # \chi ^{2}
    # make sure ticks display int values
    #ax.yaxis.set_major_formatter(ticker.MaxNLocator(nbins=8, integer=True))
    ticks, labels = P.yticks()
    labels = ticks = [int(l) for l in ticks]
    P.yticks(ticks, labels)


def normality(*args, **kwargs):
    raise ValueError("Deprecated. Use histogram command")

def histogram(Y, X=None, match=None, sub=None, 
              matrix=True, pooled=True, trend=".",
              
              datalabels=None,
              title=None, ylabel=True, 
              titlekwargs=defaults['title_kwargs'],
              # layout
              ncols=3, ax_size=2.5
              ):
    """
    kwargs
    ------
    matrix: distribution of categories, or of differences if within subject data is provided
    pooled: one plot with all values/differences pooled
    
    datalabels = float (in std) : label outlier data
    
    """
    assert isvar(Y)
    
    # ylabel
    if ylabel is True:
        if hasattr(Y, 'name'):
            ylabel = textab.texify(Y.name)
        else:
            ylabel = False
    
    if X is None:
        fig = _simple_fig(title=title, ylabel=ylabel)
        _normality_plot(fig.ax, Y.x)
#        fig.ax.hist(Y.x)
        fig.finish()
        return
    
    ct = celltable(Y, X, match=match, sub=sub)
    
    if ct.all_within:
        # TODO: use celltable
        data, _datalabels, names, within = _split_Y(Y, X, match=match, sub=sub)
    
        P.figure(figsize=(7, 7))
        P.subplots_adjust(hspace=.5)
        
        P.suptitle("Tests for Normality of the Differences", **titlekwargs)
        nPlots = len(data) - 1
        pooled = []
        # i: row
        # j: -column
        for i in range(0, nPlots+1):
            for j in range(i+1, nPlots+1):
                difference = data[i] - data[j]
                pooled.append(sp.stats.zscore(difference)) # z transform?? (sp.stats.zs())
                ax=P.subplot(nPlots, nPlots, nPlots*i + (nPlots+1-j))
                _normality_plot(ax, difference)
                if i==0:
                    ax.set_title(names[j], size=12)
                if j==nPlots:
                    ax.set_ylabel(names[i], size=12)
        # pooled diffs
        if len(names) > 2:
            ax = P.subplot(nPlots, nPlots, nPlots**2)
            _normality_plot(ax, pooled, facecolor='g')
            P.title("Pooled Differences (n=%s)"%len(pooled), weight='bold')
            P.figtext(.99, .01,
                      "$^{*}$ Anderson and Darling test thresholded at $[ .15,   .10,    .05,    .025,   .01 ]$.",
                      color='r', 
                      verticalalignment='bottom', 
                      horizontalalignment='right')
    else: # independent measures
        k = len(ct.indexes)
        if ncols >= k:
            ncols = k
            nrows = 1
        else:
            nrows = k // ncols + (k % ncols > 0)
        
        # find bins
        unique = np.unique(Y.x)
        
        
#        fig = mpl.figure.Figure(figsize=(ax_size*ncols, ax_size*nrows))
        fig = P.figure(figsize=(ax_size*ncols, ax_size*nrows))
        if title:
            P.suptitle(title, size=13, weight='bold')
        P.subplots_adjust(hspace=.5, left=.1, right=.9, bottom=.1, top=.8)
        
        for i, index in enumerate(ct.indexes):
            ax = fig.add_subplot(nrows, ncols, i+1)
            ax.set_title(ct.cells[index])
            _normality_plot(ax, ct.data[index])
            
        
#        TODO: normality for independent data
        #### NON FUNCTIONAL #############
#        print "\n__Test for Normality:".ljust(70, '_')
#        u = np.sqrt(len(names))
#        P.suptitle("Test for Normality")
#        for i,(name,d) in enumerate(zip(names, dataC)):
#            test=sp.stats.normaltest(d)
#            print "%s: Chi^2=%.3f, p=%.3f (2-tailed)"%((name,)+test)
#            P.subplot(u,u,i+1); P.title(name)
#            P.hist(d)
#            P.xlabel("Chi^2=%.3f, p=%.3f"%test)
        #################################
#    if save:
#        P.savefig(save+'normality_test.'+figformat)


def boxcox_explore(x, params=[-1, -.5, 0, .5, 1], crange=False, ax=None, box=True):
    """
    crange: correct range of transformed data
    ax: ax to plot to
    box: use Box-Cox family
    """
    if hasattr(x, 'x'):
        x = x.x
    x = np.ravel(x)
    y = []
    for p in params:
        if p == 0:
            if box:
                xi = np.log(x)
            else:
                xi = np.log10(x)
                #xi = np.log1p(x)
        else:
            if box:
                xi = (x**p - 1) / p
            else:
                xi = x**p
        if crange:
            xi -= min(xi)
            xi /= max(xi)
        y.append(xi)
    if not ax:
        P.figure()
        ax = P.subplot(111)
    ax.boxplot(y)
    ax.set_xticks(range(1, 1+len(params)))
    ax.set_xticklabels(params)
    ax.set_xlabel("p")
    if crange:
        ax.set_ylabel("Value (Range Corrected)")
