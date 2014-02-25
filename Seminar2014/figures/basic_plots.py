import matplotlib.pyplot as plt
from disser.io import DataCache
from disser import datatypes
import disser.plots.defaults as defaults
import quantities as pq
import numpy as np
from disser import plots, datatypes, atten
#plt.rcParams['savefig.dpi'] = 107

def sorter(k):
    # Map certain experiments to sort to front or end
    return k[0], {'Control':'@', 'Combined':'}'}.get(k[1], k[1])

def make_key(data):
    diff_count = 0
    exp_key = 'Control'
    if np.abs(data.wavelength.rescale(pq.cm) -
              np.round(data.wavelength.rescale(pq.cm), 0)) < 0.1:
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

def setupDefaults(grid):
    ax = grid[0]
    ax.xaxis.set_major_locator(plt.MultipleLocator(5))
    ax.set_xlim(-15, 15)
    ax.set_ylim(0, 50)

plt.rcParams['font.size'] = 12
plots.defaults.axisDefaults.setup = setupDefaults
data_cache = DataCache('ref_runs', make_key, ('band', 'exp'))
data_cache.key_sorter = sorter
wavelengths,exps = data_cache.sub_keys()

for lam_text, exp_text in [('C', 'Control'), ('X', 'Control')]:
    data = data_cache[lam_text, exp_text]
    with datatypes.PlotInfoContext(wavelength=data.wavelength):
        for desc,moms in [('Single', (datatypes.Reflectivity, datatypes.DopplerVelocity, datatypes.SpectrumWidth)),
                          ('Dual', (datatypes.ZDR, datatypes.RhoHV, datatypes.PhiDP)),
                          ('Attenuation', (datatypes.Attenuation, datatypes.DiffAtten))]:
            source = 'calc' if desc=='Attenuation' else 'ts'
            moments = [data.fields.grab(moment, pol='H', source=source) for moment in moms] 

            fig = plt.figure(figsize=(11, 6), dpi=200)
            if len(moments) == 3:
                rect = [0.07, 0.05, 0.88, 0.95]
            else:
                rect = [0.07, 0.05, 0.88, 0.82]

            grid = defaults.multipanel_cbar_each(fig, (1, len(moments)), moments, data,
                                                 rect=rect)
            for ax in grid:
                ax.title.set_verticalalignment('bottom')
            text = '%s-Band %s' % (lam_text, desc)
            title = grid[0].figure.suptitle(text, fontsize=18)
            fig.savefig('%s_%s.png' % (lam_text, desc), bbox_inches='tight',
                        dpi=200)
