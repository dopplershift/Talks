import matplotlib.pyplot as plt
import numpy as np
import quantities as pq
plt.rcParams['savefig.dpi'] = 107

from disser.io import DataCache
def sorter(k):
    # Map certain experiments to sort to front or end
    return k[0], {'Control':'@', 'Combined':'}'}.get(k[1], k[1])

def make_key(data):
    diff_count = 0
    exp_key = 'Control'
    if np.abs(data.wavelength.rescale(pq.cm) - np.round(data.wavelength.rescale(pq.cm), 0)) < 0.1:
        exp_key = 'Wavelength'
        diff_count += 1
    if np.isnan(data.runinfo.FixedTemp):
        exp_key = 'Temperature'
        diff_count += 1
    if data.runinfo.CantingWidth > 10.0:
        exp_key = 'Canting'
        diff_count += 1
    if data.runinfo.AxisRatioCalc != 'Brandes':
        exp_key = 'Shape'
        diff_count += 1
    if diff_count > 1:
        exp_key = 'Combined'
    return data.waveBand, exp_key

data_cache = DataCache('ref_runs', make_key, ('band', 'exp'))
del data_cache['C', 'Canting']
del data_cache['X', 'Canting']
data_cache.key_sorter = sorter
wavelengths,exps = data_cache.sub_keys()

# <codecell>

import disser.plots.defaults as defaults
from disser import plots, datatypes, atten

# <codecell>

AttenDelta = datatypes.DataType('Attenuation Difference', r'$\Delta A$')
SpecAttenDelta = datatypes.DataType('Specific Attenuation Difference', r'$\Delta \alpha$')
DiffAttenDelta = datatypes.DataType('Differential Attenuation Difference', r'$\Delta A_D$')
SpecDiffAttenDelta = datatypes.DataType('Specific Differential Attenuation Difference', r'$\Delta \alpha_D$')
PhiDelta = datatypes.DataType('Differential Phase Difference', r'$\Delta \Phi_{DP}$')

# <codecell>

#bidi_cmap = plt.get_cmap('Spectral')
bidi_cmap = plots.get_cmap('Carbone42')
datatypes.TypePlotInfo[AttenDelta].update(norm=plt.Normalize(-10, 10), cmap=bidi_cmap)
datatypes.TypePlotInfo[SpecAttenDelta].update(norm=plt.Normalize(-1, 1), cmap=bidi_cmap)
datatypes.TypePlotInfo[DiffAttenDelta].update(norm=plt.Normalize(-2, 2), cmap=bidi_cmap)
datatypes.TypePlotInfo[SpecDiffAttenDelta].update(norm=plt.Normalize(-0.5, 0.5), cmap=bidi_cmap)
datatypes.TypePlotInfo[PhiDelta].update(norm=plt.Normalize(-50, 50), cmap=bidi_cmap)

# <headingcell level=2>

# Attenuation Algorithm Results

# <codecell>

def run_attenuation_algs(data):
    from disser.atten import attenAlgs
    attenAlgs.runAll(data, var='H')
    attenAlgs.runAll(data, var='diff')

# <codecell>

def calc_specific_atten(data, dt=datatypes.Attenuation, pol='H'):
    destMap = {datatypes.Attenuation:datatypes.SpecAttenuation, datatypes.DiffAtten:datatypes.SpecDiffAtten}
    fields = data.fields.grabAll(dt, filt=lambda f: f.pol==pol)
    for f in fields:
        d = data.fields[f]
        spec = np.gradient(d, 1, data.gate_length)[1].rescale('dB/km')
        data.addField(spec, destMap[dt], pol=f.pol, source=f.source)

# <codecell>

for d in data_cache.values():
    d.fields.default_keys['source'] = 'average'
    run_attenuation_algs(d)
    calc_specific_atten(d, datatypes.Attenuation, pol='H')
    calc_specific_atten(d, datatypes.DiffAtten, pol=None)

# <codecell>

def setupDefaults(grid):
    ax = grid[0]
    ax.xaxis.set_major_locator(plt.MultipleLocator(10))
    ax.set_xlim(-15, 15)
    ax.set_ylim(0, 50)
    
def algLabelsNoSrc(dt, units):
    abbr, src_str = dt.string_parts()
    return '%s (%s)' % (abbr, units)

plt.rcParams['font.size'] = 12
plots.defaults.axisDefaults.setup = setupDefaults

def exp_order(mom):
    return {'calc':0, 'Linear':1, 'ZPHI':2, 'SC':3}[mom.source]

# <codecell>

for lam_text in wavelengths:
    for exp in exps:
        data = data_cache[lam_text, exp]
        with datatypes.PlotInfoContext(wavelength=data.wavelength):
            with defaults.colorbarLabeller(algLabelsNoSrc):
                for pol,mom in [('H', datatypes.Attenuation), ('H', datatypes.SpecAttenuation),
                                (None, datatypes.DiffAtten), (None, datatypes.SpecDiffAtten)]:
                    fig = plt.figure(figsize=(8, 6))
                    moments = data.fields.grabAll(mom, filt=lambda f: f.pol==pol and f.source not in ('average', 'ts'))
                    grid = defaults.multipanel_cbar_row(fig, (1, len(moments)), moments, data,
                                                        rect=[0.07, 0.17, 0.95, 0.91])
                    for ax,m in zip(grid, sorted(moments, key=exp_order)):
                        src = m.source
                        l = ax.set_title('Truth' if src == 'calc' else src)
                        l.set_verticalalignment('bottom')
                    fig.suptitle(exp, fontsize=18)
                    fig.savefig('%s_%s_%s.png' % (lam_text, exp, mom.name.replace(' ', '_')))

import sys;sys.exit()
# <headingcell level=2>

# Algorithm Difference Between Runs

# <codecell>

def calc_differences_algs(data, dt=datatypes.Attenuation, pol='H'):
    destMap = {datatypes.Attenuation:AttenDelta, datatypes.DiffAtten:DiffAttenDelta,
        datatypes.SpecAttenuation:SpecAttenDelta, datatypes.SpecDiffAtten:SpecDiffAttenDelta}
    ref_field = data.fields.grabData(dt, pol=pol, source='calc')
    fields = data.fields.grabAll(dt, filt=lambda f: f.pol == pol and f.source not in ('calc', 'average', 'ts'))

    for f in fields:
        data.addField(data.fields[f] - ref_field, destMap[dt], pol=f.pol, source=f.source)

# <codecell>

for d in data_cache.values():
    calc_differences_algs(d, dt=datatypes.Attenuation, pol='H')
    calc_differences_algs(d, dt=datatypes.SpecAttenuation, pol='H')
    calc_differences_algs(d, dt=datatypes.DiffAtten, pol=None)
    calc_differences_algs(d, dt=datatypes.SpecDiffAtten, pol=None)

# <codecell>

def plot_differences_algs(data, dt, pol):
    rect=[0, 0, 1, 0.92]
    ncols = len(data)

    data_list = list()
    moments = list()
    for d in data:
        moms = d.fields.grabAll(dt, filt=lambda f: f.pol == pol and f.source not in ('calc', 'average', 'ts', 'sweep'))
        moments.extend(moms)
        data_list.extend([d]*len(moms))

    nrows = len(moms)
    fig = plt.figure(figsize=(8, 6))

    with defaults.colorbarLabeller(defaults.algLabels):
        grid = defaults.multipanel_cbar_row(fig, (nrows, ncols), moments, data_list, rect=rect)
    return fig, grid    

# <codecell>

for lam_text in wavelengths:
    data_list = data_cache.query(band=lam_text)
    with datatypes.PlotInfoContext(wavelength=data_list[0].wavelength):
        for pol,mom in [('H', AttenDelta), ('H', SpecAttenDelta),
                        (None, DiffAttenDelta), (None, SpecDiffAttenDelta)]:
            fig, grid = plot_differences_algs(data_list, mom, pol=pol)
            polStr = 'Diff' if pol is None else pol
            title = fig.suptitle('%s-band %s' % (lam_text, polStr), fontsize=11)
            for ind,exp in enumerate(exps):
                grid.axes_row[0][ind].set_title(exp)

# <codecell>

def plot_scatter_algs(data, dt, pol):
    from matplotlib.colors import LogNorm
    data_list = list()
    moments = list()

    # Assume all data have the same available moments
    moms = [f.source for f in data[0].fields.grabAll(dt,
            filt=lambda f: f.pol == pol and f.source not in ('calc', 'average', 'ts', 'sweep'))]
    
    fig, axes = plt.subplots(len(moms), len(data), sharex=True, sharey=True)
    for rowInd, (mom, row) in enumerate(zip(moms, axes)):
        for colInd, (d, ax) in enumerate(zip(data, row)):
            ref_mom = d.fields.grab(dt, pol=pol, source='calc')
            ref_field = d.fields[ref_mom]
            alg_field = d.fields.grabData(dt, pol=pol, source=mom)
            mask = (ref_field > 0.02) & (alg_field > 0.02)
            with datatypes.PlotInfoContext(wavelength=d.wavelength):
                norm = datatypes.TypePlotInfo[ref_mom.type]['norm']
            hist, xedge, yedge = np.histogram2d(ref_field[mask], alg_field[mask], bins=50,
                    range=[[norm.vmin, norm.vmax], [norm.vmin, norm.vmax]])
            ax.pcolormesh(xedge, yedge, hist.T, norm=LogNorm())
            ax.plot([0.0, 1.0], [0.0, 1.0], 'k--', transform=ax.transAxes)
            ax.grid(True)
            if colInd == 0:
                ax.set_ylabel(mom)
            if rowInd == len(moms) - 1:
                ax.set_xlabel(ref_mom)
    ax.set_xlim(0.0, None)
    ax.set_ylim(0.0, None)
    ax.xaxis.set_major_locator(plt.MaxNLocator(nbins=5))
    ax.yaxis.set_major_locator(plt.MaxNLocator(nbins=5))
    return fig, axes    

# <codecell>

for lam_text in wavelengths:
    data_list = data_cache.query(band=lam_text)
    with datatypes.PlotInfoContext(wavelength=data_list[0].wavelength):
        for pol,mom in [('H', datatypes.SpecAttenuation), (None, datatypes.SpecDiffAtten)]:
            fig, grid = plot_scatter_algs(data_list, mom, pol=pol)
            polStr = 'Diff' if pol is None else pol
            title = fig.suptitle('%s-band %s' % (lam_text, polStr), fontsize=11)
            for ind,exp in enumerate(exps):
                grid[0, ind].set_title(exp)
            fig.tight_layout()

