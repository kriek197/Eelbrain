"""
statistical tests for data objects

"""
from __future__ import division

import random, itertools

import numpy as np
import scipy as sp
from matplotlib import pyplot as P

import eelbrain.fmtxt as textab

from eelbrain.vessels.data import var, isvar, asvar, isfactor, asfactor, ismodel
from eelbrain.vessels.data import _split_Y, multifactor
from eelbrain.vessels.structure import celltable


__hide__ = ['division', 'random', 'itertools', 'scipy',
            'textab', 'texstr',
            'var', 'isvar', 'asvar', 'isfactor', 'asfactor', 'ismodel', 'celltable',
            'multifactor', 
            ]


def lilliefors(data, formatted=False, **kwargs):
    """ 
    Returns the D-value of the Kolmogorov-Smirnov Test and p approximated 
    according to Dallal and Wilkinson (1986). Requires minimal sample size of 5.
    p is reasonably accurate only when it is <= .1 (cf. Dallal and Wilkens).
    
    The Lilliefors test is an adaptation of the Kolmogorov-Smirnov test. It 
    is used to test the null hypothesis that data come from a normally
    distributed population, when the null hypothesis does not specify which 
    normal distribution, i.e. does not specify the expected value and variance.
    
    Uses the scipy.stats.kstest implementation of the Kolmogorov-Smirnov test.
    
    
    kwargs:
    
        all kwargs are forwarded to scipy.stats.kstest
    
    
    NOTE:
    p values agree with R lillie.test (nortest package) on low values of p. 
    lillie.test adjusts something at p>.1
    http://pbil.univ-lyon1.fr/library/nortest/R/nortest
    
    References:
    
        Dallal, G. E. and Wilkinson, L. (1986). An Analytic Approximation to the 
                Distribution of Lilliefors's Test Statistic for Normality. The 
                American Statistician, 40(4), 294--296.
        Lilliefors, H. W. (1967). On the Kolmogorov-Smirnov Test for Normality 
                with Mean and Variance Unknown. Journal of the American 
                Statistical Association, 62(318), 399--402.

    
    """
    N = len(data) #data.shape[-1] #axis]
    assert N>=5, "sample size must be greater than 4"
    # perform Kolmogorov-Smirnov with estimated mean and std
    m = np.mean(data)#, axis=axis)
    s = np.std(data, ddof=1)#, axis=axis)
    D, ks_p = sp.stats.kstest(data, 'norm', args=(m,s), **kwargs)
    # approximate p (Dallal)
    if N > 100:
        D *= (N/100)**.49
        N = 100
    p_estimate = np.exp(-7.01256 * D**2 * (N + 2.78019)             \
                     + 2.99587 * D * (N + 2.78019)**.5 - .122119    \
                     + .974598/(N**.5) + 1.67997/N)
    # approximate P (Molin & Abdi)
    L = D # ???
    b2 = 0.08861783849346 
    b1 = 1.30748185078790 
    b0 = 0.37872256037043
    A = (-(b1 + N) + np.sqrt((b1 + N)**2 - 4*b2*(b0 - L**-2))) / 2*b2
    Pr = -  .37782822932809         \
         + 1.67819837908004 * A     \
         - 3.02959249450445 * A**2  \
         + 2.80015798142101 * A**3  \
         - 1.39874347510845 * A**4  \
         + 0.40466213484419 * A**5  \
         - 0.06353440854207 * A**6  \
         + 0.00287462087623 * A**7  \
         + 0.00069650013110 * A**8  \
         - 0.00011872227037 * A**9  \
         + 0.00000575586834 * A**10 
    #
    if formatted:
        txt = "D={0:.4f}, Dallal p={1:.4f}, Molin&Abdi p={2:.4f}"
        return txt.format(D, p_estimate, Pr)
    else:
        return D, p_estimate



## MARK: stars, with correction

def _hochberg_threshold(N, alpha=.05):
    j = np.arange(N)
    threshold = alpha / (N-j)
    return threshold


def mcp_adjust(ps, method='Hochberg'):
    """
    http://www.technion.ac.il/docs/sas/stat/chap43/sect14.htm
    
    """
    n = len(ps)
    if method == 'Bonferroni':
        return ps / n
    elif method in ['Hochberg', 'Holm']:
        ascsort = np.argsort(ps)
        ps_asc = np.array(ps)[ascsort]
        iout_asc = np.arange(n)[ascsort]
        ps_adjusted = np.empty(n)
        p_buffer = 1
        if method == 'Holm':
            for i in range(n):
                p = ps_asc[i]
                p_adj = (n-i) * p
                p_buffer = max(p_buffer, p_adj)
                ps_adjusted[iout_asc[i]] = p_buffer
        elif method == 'Hochberg':
            for i in range(1, n+1):
                p = ps_asc[-i]
                p_adj = (i) * p
                p_buffer = min(p_adj, p_buffer)
                ps_adjusted[iout_asc[-i]] = p_buffer
        return ps_adjusted
    else:
        raise NotImplementedError


def _get_correction_caption(corr, n):
    if corr=='Hochberg':
        return "(* Corrected after Hochberg, 1988)"
    elif corr=='Bonferroni':
        return "(* Bonferroni corrected for %i tests)"%n
    elif corr=='Holm':
        return "(* Corrected after Holm)"
    else:
        return "(* Uncorrected)"
    


def star(p_list, out=str, levels=True, trend=False, corr='Hochberg',
         eq_strlen=False):
    """
    
    out=str: convert n stars into string containing '**'
       =int: leave n stars as integer
       
    corr: "Bonferroni"
          "Hochberg"
    
    levels: {p: string, ...} dictionary. Default (levels=True) creates the 
            levels {.05 : '*',    . trend=True adds {.1: "'"}.
                    .01 : '**',
                    .001: '***'}
    
    eq_strlen: ("equalize string lengths") when strings are returned make sure
               they all have the same length (False by default).
    
    """
    # set default levels
    if levels is True:
        levels = {.05 : '*',
                  .01 : '**',
                  .001: '***'}
        if trend is True:
            levels[.1] = "'" # "`"
        elif textab.isstr(trend):
            levels[.1] = trend
    elif trend:
        raise AssertionError("'trend' kwarg only meaningful when levels==True")
    
    a_levels = sorted(levels.keys(), reverse=True)
    symbols = [''] + [levels[p] for p in a_levels]
    
    # allow input (p_list) to contain single p-value
    if np.iterable(p_list):
        int_out = False
    else:
        int_out = True
        p_list = [p_list]
    
    N = len(p_list)
    p_list = np.asarray(p_list)
    nstars = np.zeros(N, dtype=int)
    if corr:
        p_list = mcp_adjust(p_list, corr)
    for a in a_levels:
        nstars += (p_list <= a)
    
    # out
    if out == str:
        if eq_strlen:
            maxlen = max([len(s) for s in symbols])
            out = [(symbols[n]).ljust(maxlen) for n in nstars]
        else:
            out = [symbols[n] for n in nstars]
    else:
        out = nstars
    # out format to in format
    if int_out:
        return out[0]
    else:
        return out



def oneway(Y, X, match=None, sub=None, par=True, title=None):
    "data: for should iter over groups/treatments"
    data, datalabels, names, within = _split_Y(Y, X, match=match, sub=sub)
    test = _oneway(data, parametric=par, within=within)
    template = "{test}: {statistic}={value}{stars}, p={p}"
    out = template.format(**test)
    return out


def _oneway(data, parametric=True, within=False):
    """
    Parameters
    ----------
    data:       list of groups/treatments
    parametric: bool
    within:     bool
    
    
    Returns
    -------
    dictionary with results:
    'test':      test name
    'statistic': statistic letter
    statistic:   statistic value
    'value':     "
    'p':         p value
    'stars':     stars as str
    
    """
    args = list(data)
    if parametric:
        if within:
            test = {'test': "NOTIMPLMENTED",
                    'statistic': 'NONE',
                    'NONE':0, 'p':0}
        else:
            test = {'test': "One-Way ANOVA",
                    'statistic': 'F'}
            test['F'], test['p'] = sp.stats.f_oneway(*args)
    elif within:
        test = {'test': "Friedman Chi-Square",
                'statistic': 'Q'}
        test['Q'], test['p'] = sp.stats.friedmanchisquare(*args)
    else:
        test = {'test': "Kruskal Wallis",
                'statistic': 'H'}
        test['H'], test['p'] = sp.stats.kruskal(*args)
    test['value'] = test[test['statistic']]
    test['stars'] = test.star(test['p'])
    return test



def test(Y, X=None, against=0, match=None, sub=None, 
         par=True, corr='Hochberg',
         title='{desc}'):
    """
    One-sample tests.
    
    kwargs
    ------
    X: perform tests separately for all categories in X. 
    Against: can be 
             - value
             - string (category in X)
    
    """
    ct = celltable(Y, X, match, sub)
     
    if par:
        title_desc = "t-tests against %s"%against
        statistic_name = 't'
    else:
        raise NotImplementedError
    
    names=[]; ts=[]; dfs=[]; ps=[]
    
    if isinstance(against, str):
        k = len(ct.indexes) - 1
        assert against in ct.cells.values()
        for id in ct.indexes:
            label = ct.cells[id]
            if against == label:
                baseline_id = id
                baseline = ct.data[id]
        
        for id in ct.indexes:
            if id == baseline_id:
                continue
            names.append(ct.cells[id])
            if (ct.within is not False) and ct.within[id, baseline_id]:
                t, p = sp.stats.ttest_rel(baseline, ct.data[id])
                df = len(baseline)-1
            else:
                data = ct.data[id]
                t, p = sp.stats.ttest_ind(baseline, data)
                df = len(baseline) + len(data) - 2
            ts.append(t)
            dfs.append(df)
            ps.append(p)
        
    elif np.isscalar(against):
        k = len(ct.cells)
        
        for id in ct.indexes:
            label = ct.cells[id]
            data = ct.data[id]
            t, p = sp.stats.ttest_1samp(data, against)
            df = len(data) - 1
            names.append(label); ts.append(t); dfs.append(df); ps.append(p)        
    
    if corr:
        ps_adjusted = mcp_adjust(ps, corr)
    else:
        ps_adjusted = np.zeros(len(ps))
    stars = star(ps, out=str)#, levels=levels, trend=trend, corr=corr
    if len(np.unique(dfs)) == 1:
        df_in_header = True
    else:
        df_in_header = False
    
    table = textab.Table('l' + 'r'*(3-df_in_header+bool(corr)))
    table.title(title.format(desc=title_desc))
    if corr:
        table.caption(_get_correction_caption(corr, k))
    
    # header
    table.cell("Effect")
    if df_in_header:
        table.cell([statistic_name,
                    textab.texstr(dfs[0], property='_'),
                    ], mat=True)
    else:
        table.cell(statistic_name, mat=True)
        table.cell('df', mat=True)
    table.cell('p', mat=True)
    if corr:
        table.cell(textab.symbol('p', df=corr))
    table.midrule()
    
    # body
    for name, t, mark, df, p, p_adj in zip(names, ts, stars, dfs, ps, ps_adjusted):
        table.cell(name)
        tex_stars = textab.Stars(mark, of=3)
        tex_t = textab.texstr(t, fmt='%.2f')
        table.cell([tex_t, tex_stars])
        if not df_in_header:
            table.cell(df)
        
        table.cell(textab.p(p))
        if corr:
            table.cell(textab.p(p_adj))
    return table


def pairwise(Y, X, match=None, sub=None,            # data in
             par=True, corr='Hochberg', trend=True, # stats
             title='{desc}', mirror=False,        # layout
             ):
    """
    pairwise comparison according to factor structure
    
    """
#    ct = celltable(Y, X, match=match, sub=sub)
    # test
    data, datalabels, names, within = _split_Y(Y, X, match=match, sub=sub)
    test = _pairwise(data, within=within, parametric=par, corr=corr, #levels=levels, 
                     trend=trend)
    # extract test results
    k = len(data)
    indexes = test['pw_indexes']
    statistic = test['statistic']
    _K = test[statistic]
    _P = test['p']
    if corr:
        _Pc = mcp_adjust(_P, corr)
    _df = test['df']
    _NStars = test['stars']
    symbols = test['symbols']
    
    # create TABLE
    table = textab.Table('l'+'l'*(k-1+mirror))
    title_desc = "Pairwise {0}".format(test['test'])
    table.title(title.format(desc=title_desc))
    table.caption(test['caption'])
    
    # headings
    table.cell()
    for name in names[1-mirror:]:
        table.cell(name)
    table.midrule()
    
    tex_peq = textab.texstr("p=")
    #tex_df = textab.Element(df, "_", digits=0)
    if corr and not mirror:
        subrows = range(3)
    else:
        subrows = range(2)
    
    for row in range(0, k-1+mirror):
        for subrow in subrows: # contains t/p
            # names column
            if subrow is 0:
                table.cell(names[row], r"\textbf")
            else:
                table.cell()
            # rows
            for col in range(1-mirror, k):
                if row == col:
                    table.cell()
                elif col > row:
                    index = indexes[(row, col)]
                    #(col-1) + ((k-2)*row) sum(range(k-1, k-1-row, -1))
                    K = _K[index]
                    p = _P[index]
                    df = _df[index]
#                    nstars = _NStars[index]
                    if subrow is 0:
                        tex_cell = textab.eq(statistic, K, df=df, 
                                             stars=symbols[index],   
                                             of=3+trend)
                    elif subrow is 1:
                        tex_cell = textab.texstr([tex_peq, texstr(p, fmt='%.3f')], 
                                                 mat=True)
                    elif subrow is 2:
                        tex_cell = textab.eq('p', _Pc[index], df='c', 
                                             fmt='%.3f', drop0=True)
                    table.cell(tex_cell)
                else:
                    if mirror and corr and subrow==0:
                        index = indexes[(col, row)]
                        p = _Pc[index]
                        table.cell(p, fmt='%.3f', drop0=True)
                    else:
                        table.cell()
    return table


def _pairwise(data, within=True, parametric=True, corr='Hochberg', 
              levels=True, trend=True):
    """
    data:   list of groups/treatments
    
    corr:   'Hochberg'
            'Holm'
            'Bonferroni'
    
    
    Returns
    -------
    dictionary with results, containing:
    
    'test': test name
    'caption': information about correction
    'statistic': abbreviation used for the staistic (e.g. 'Q')
    statistic: list of values
    'df': df
    'p': list of corresponding pa values
    'stars': list of n stars (ints)
    'pw_indexes': dict linking table index (i,j) to the list index for p etc.
    
    
    
    """
    # find test
    k = len(data)
    if k < 3: # need no correction for single test
        corr = None
    if parametric:
        test_name = "t-Tests ({0} samples)" 
        statistic = "t"
        if within:
            test_func = sp.stats.ttest_rel
            test_name = test_name.format('paired')
        else:
            test_func = sp.stats.ttest_ind
            test_name = test_name.format('independent')            
    elif within:
        test_name = "Wilcoxon Signed-Rank Test"
        test_func = sp.stats.wilcoxon
        statistic = "z"
    else:
        test_name = "Mann-Whitney U Test"
        raise NotImplementedError("mannwhitneyu returns one-sided p")
        test_func = sp.stats.mannwhitneyu
        statistic = "u"
    # perform test
    _K = [] # kennwerte
    _P = []
    _df = []
    i=0
    indexes = {}
    for x in range(k):
        for y in range(x+1, k):
            Y1, Y2 = data[x], data[y]
            t, p = test_func(Y1, Y2)
            _K.append(t)
            if within:
                _df.append(len(Y1)-1)
            else:
                _df.append(len(Y1)+len(Y2)-2)
                
            _P.append(p)
            indexes[(x,y)] = indexes[(y,x)] = i
            i += 1
    # add stars
    _NStars = star(_P, out=int, levels=levels, trend=trend, corr=corr)
    _str_Stars = star(_P, out=str, levels=levels, trend=trend, corr=corr)
    caption = _get_correction_caption(corr, len(_P))
    # prepare output
    out = {'test': test_name,
           'caption': caption,
           'statistic': statistic,
           statistic: _K,
           'df': _df,
           'p': _P,
           'stars': _NStars,
           'symbols': _str_Stars,
           'pw_indexes': indexes}
    return out



def correlations(Y, Xs, cat=None, levels=[.05, .01, .001], diff=None, sub=None,
         pmax=None, nan=True):#, match=None):
    """
    :arg var Y: first variable
    :arg var X: second variable (or list of variables)
    :arg cat: show correlations separately for different groups in the 
        data. Can be a ``factor`` (the correlation for each level is shown 
        separately) or an array of ``bool`` values (e.g. from a comparison like
        ``Stim==1``)
    :arg list levels: significance levels to mark
    :arg diff: (factor, cat_1, cat_2)
    :arg sub: use only a subset of the data
    :arg pmax: (None) don't show correlations with p>pmax
    :arg nan: ``True``: display correlation which yield NAN;  
        ``False``: hide NANs but mention occurrence in summary (not 
        implemented);  
        ``None``: don't mention NANs
    :rtype: Table
     
    """
    levels = np.array(levels)

    if isvar(Xs):
        Xs = [Xs]

    # SUB
    if sub is not None:
        Y = Y[sub]
        Xs = [X[sub] for X in Xs]
        if ismodel(cat) or isfactor(cat):
            cat = cat[sub]
    
    if diff is not None:
        raise NotImplementedError
    
    if ismodel(cat) or isfactor(cat):
        table = textab.Table('l'*5)
        table.cells('Variable', 'Category', 'r', 'p', 'n')
        if ismodel(cat):
            cat = multifactor(cat.factors)
    else:
        table = textab.Table('l'*4)
        table.cells('Variable', 'r', 'p', 'n')
    
    table.midrule()
    table.title("Correlations with %s"%(Y.name))
    
    table._my_nan_count = 0
    
    for X in Xs:
        if isfactor(cat) or type(cat) is multifactor:
            printXname = True
            for i in np.unique(cat.x):
                tlen = len(table)
                
                _corr_to_table(table, Y, X, cat==i, levels, pmax=pmax, nan=nan,
                               printXname=printXname, label=cat.cells[i])
                
                if len(table) > tlen: #
                    printXname = False
        else:
            _corr_to_table(table, Y, X, cat, levels, pmax=pmax, nan=nan)

    # last row
    if pmax is None:
        p_text = ''
    else:
        p_text = 'all other p>{p}'.format(p=pmax)
    if nan is False and table._my_nan_count > 0:
        nan_text = '%s NANs'%table._my_nan_count
    else:
        nan_text = ''
    if p_text or nan_text:
        if p_text and nan_text:
            text = ', '.join([p_text, nan_text])
        else:
            text = ''.join([p_text, nan_text])
        table.cell("(%s)"%text)
    return table


def _corr(Y, X, index):
    """
    index has to be bool array; returns r, p, n
    
    """
    if index is not None:
        Y = Y[index]
        X = X[index]
    n = Y.N
    assert n == X.N
    df = n - 2
    r = np.corrcoef(Y.x, X.x)[0,1]
    t = r / np.sqrt((1-r**2) / df)
    p = sp.stats.t.sf(np.abs(t), df) * 2
    return r, p, n


def _corr_to_table(table, Y, X, categories, levels, printXname=True, label=False,
                   pmax=None, nan=True):
    r, p, n = _corr(X, Y, categories)
    if (pmax is None) or (p <= pmax):
        if nan or (not np.isnan(r)):
            nstars = np.sum(p <= levels)
            if printXname:
                table.cell(X.name)
            else:
                table.cell()
            if label:
                table.cell(label)
            table.cells(textab.texstr(r) + textab.Stars(nstars, of=len(levels)), p, n)
        else:
            table._my_nan_count += 1



class bootstrap_pairwise(object):
    def __init__(self, Y, X, match=None, sub=None, 
                 samples=1000, replacement=True,
                 title="Bootstrapped Pairwise Tests"):
        Y = asvar(Y, sub)
        X = asfactor(X, sub)
        assert Y.N == X.N, "dataset length mismatch"
                
        if match:
            if sub is not None:
                match = match[sub]
            assert match.N==Y.N, "dataset length mismatch"

        # prepare data container
        resampled = np.empty((samples + 1, Y.N)) # sample X subject within category
        resampled[0] = Y.x
        # fill resampled
        for i, Y_resampled in enumerate(_resample(Y, unit=match, samples=samples,
                                                  replacement=replacement)):
            resampled[i+1] = Y_resampled.x
        self.resampled = resampled
            
        X_cell_ids = sorted(X.cells.keys())
        n_groups = len(X_cell_ids)
        group_names = [X.cells[i] for i in X_cell_ids]
        
        if match:
            # if there are several values per X%match cell, take the average
            # T: indexes to transform Y.x to [X%match, value]-array
            match_cell_ids = match.cells.keys()
            group_size = len(match_cell_ids)
            T = None; i = 0
            for X_cell in X_cell_ids:
                for match_cell in match_cell_ids:
                    source_indexes = np.where((X==X_cell) * (match==match_cell))[0]
                    if T is None:
                        n_cells = n_groups * group_size
                        T = np.empty((n_cells, len(source_indexes)), dtype=int)
                    T[i,:] = source_indexes
                    i += 1
            
            if T.shape[1] == 1:
                T = T[:,0]
                ordered = resampled[:, T]
            else:
                ordered = resampled[:, T].mean(axis=2)
            self.ordered = ordered
            
            # t-tests
            n_comparisons = sum(range(n_groups))
            t = np.empty((samples + 1, n_comparisons))
            comp_names = []
            one_group = np.arange(group_size)
            groups = [one_group + i*group_size for i in range(n_groups)]
            for i, (g1, g2) in enumerate(itertools.combinations(range(n_groups), 2)):
                group_1 = groups[g1]
                group_2 = groups[g2]
                diffs = ordered[:, group_1] - ordered[:, group_2]
                t[:,i] = np.mean(diffs, axis=1) * np.sqrt(group_size) / np.std(diffs, axis=1, ddof=1)
                comp_names.append(' - '.join((group_names[g1], group_names[g2])))
            
            self.diffs = diffs
            self.t_resampled = np.max(np.abs(t[1:]), axis=1)
            self.t = t = t[0]
        else:
            raise NotImplementedError
        
        self._Y = Y
        self._X = X
        self._group_names = group_names
        self._group_data = np.array([ordered[0, g] for g in groups])
        self._group_size = group_size
        self._df = group_size - 1
        self._match = match
        self._n_samples = samples
        self._replacement = replacement
        self._comp_names = comp_names
        self._p_parametric = self.test_param(t)
        self._p_boot = self.test_boot(t)
        self.title = title
    def __repr__(self):
        out = ['bootstrap_pairwise(', self._Y.name, self._X.name]
        if self._match:
            out.append('match=%s '%self._match.name)
        out.append('saples=%i '%self._n_samples)
        out.append('replacement=%s)'%self._replacement)
        return ''.join(out)
    def __str__(self):
        return str(self.table())
    def table(self):
        table = textab.Table('lrrrr')
        table.title(self.title)
        table.caption("Results based on %i samples"%self._n_samples)
        table.cell('Comparison')
        table.cell(textab.symbol('t', df=self._df))
        table.cell(textab.symbol('p', df='param'))
        table.cell(textab.symbol('p', df='corr'))
        table.cell(textab.symbol('p', df='boot'))
        table.midrule()
        
        p_corr = mcp_adjust(self._p_parametric)
        stars_parametric = star(self._p_parametric)
        stars_boot = star(self._p_boot, corr=None)
        
        for name, t, p1, pc, s1, p2, s2 in zip(self._comp_names, self.t, 
                                           self._p_parametric, p_corr,
                                           stars_parametric, 
                                           self._p_boot, stars_boot):
            table.cell(name)
            table.cell(t, fmt='%.2f')
            table.cell(textab.p(p1))
            table.cell(textab.p(pc, stars=s1))
            table.cell(textab.p(p2, stars=s2))
        return table
    def plot_t_dist(self, ax=None):
        """
        After:
        http://stackoverflow.com/questions/4150171/how-to-create-a-density-plot-in-matplotlib
        """
        if ax is None:
            fig = P.figure()
            ax = P.axes()
        t = self.t_resampled
        density = sp.stats.gaussian_kde(t)
#        density.covariance_factor = lambda : .25
#        density._compute_covariance()
        xs = np.linspace(0, max(t), 200)
        P.plot(xs, density(xs))
    def plot_dv_dist(self, ax=None):
        if ax is None:
            fig = P.figure()
            ax = P.axes()
        
        xs = np.linspace(np.min(self._group_data), np.max(self._group_data), 200)
        for i, name in enumerate(self._group_names):
            density = sp.stats.gaussian_kde(self._group_data[i])
            P.plot(xs, density(xs), label=name)
        P.legend()
    def test_param(self, t):
        p = sp.stats.t.sf(np.abs(t), self._group_size-1) * 2
        return p
    def test_boot(self, t):
        "t: scalar or array; returns p for each t"
        test = self.t_resampled[:,None] > np.abs(t)
        p = np.sum(test, axis=0) / self.t_resampled.shape[0]
        return p




def _resample(Y, unit=None, replacement=True, samples=1000):
    """
    Generator function to resample a dependent variable (Y) multiple times
    
    unit: factor specdifying unit of measurement (e.g. subject). If unit is 
          specified, resampling proceeds by first resampling the categories of 
          unit (with or without replacement) and then shuffling the values 
          within unites (no replacement). 
    replacement: whether random samples should be drawn with replacement or 
                 without
    samples: number of samples to yield
    
    """
    if isvar(Y):
        Yout = Y.copy('_resampled')
        Y
    else:
        Y = var(Y)
        Yout = var(Y.copy(), name="Y resampled")
    
    if unit:
        ct = celltable(Y, unit)
        unit_data = ct.get_data(out=list)
        unit_indexes = ct.data_indexes.values()
        x_out = Yout.x
        
        if replacement:
            n = len(ct.indexes)
            for sample in xrange(samples):
                source_ids = np.random.randint(n, size=n)
                for index, source_index in zip(unit_indexes, source_ids):
                    data = unit_data[source_index]
                    np.random.shuffle(data)
                    x_out[index] = data
                yield Yout
            
        else:
            for sample in xrange(samples):
                random.shuffle(unit_data)
                for index, data in zip(unit_indexes, unit_data):
                    np.random.shuffle(data)
                    x_out[index] = data
                yield Yout
            
    else:
        if replacement:
            N = Y.N
            for i in xrange(samples):
                index = np.random.randint(N)
                Yout.x = Y.x[index]
                yield Yout
        else:
            for i in xrange(samples):
                np.random.shuffle(Yout.x)
                yield Yout

        
        