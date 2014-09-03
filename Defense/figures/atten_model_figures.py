import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np
import quantities as pq
import os.path

from disser.experiments import load_model_experiments, process_all_atten, regress_stats
from disser.atten import calc_specific_atten
import disser.plots.defaults as defaults
from disser.plots.basic import LabelGenerator
from disser import plots, datatypes, atten

class StatsFile(object):
    class Table(object):
        def __init__(self, fp, exp, lam):
            self.fp = fp
            self.exp = exp
            self.lam = lam
            self.pol = None

        def __enter__(self):
            self.start_table()
            return self

        def __exit__(self, type, value, traceback):
            self.end_table()

        def write_stats(self, pol, alg, bias, mse, r_sq):
            if pol is None:
                pol = 'Differential'
            elif pol == 'H':
                pol = 'Horizontal'
            else:
                pol = 'Vertical'
            self.write_pol(pol)
            self.fp.write('        %s & %.4f & %.4f & %.4f\\\\\n' % (alg, bias, mse, r_sq))

        def write_pol(self, pol):
            if pol == self.pol:
                return
            self.pol = pol
            self.fp.write('        \\hline\n')
            self.fp.write('        \\multicolumn{4}{|c|}{%s}\\\\\n' % pol)
            self.fp.write('        \\hline\n')

        def start_table(self):
            self.fp.write(r'''\begin{table}
    \centering
    \begin{tabular}{| c | c | c | c |}
        \hline
        Algorithm & Bias (\si{dB\per \kilo\meter}) & MSE (\si{dB\squared \per \kilo\meter \squared}) & $r^2$ \\
        \hline
''')

        def end_table(self):
            if self.exp == 'Control':
                caption = '''    \\caption{{Bias, mean squared-error, and $r^2$ for the specific attenuation
    results for the {exp} experiment at {lam}-band.}}'''
            else:
                caption = '''    \\caption{{As in Table~\\ref{{tab:{lam}-stats-Control}}, but for
    the {exp} experiment.}}'''
            self.fp.write(('''\\hline
    \\end{{tabular}}
''' + caption + '''
    \\label{{tab:{lam}-stats-{exp}}}
\\end{{table}}
''').format(exp=self.exp, lam=self.lam))

    def __init__(self, fname):
        self.fp = open(fname, 'w')

    def table(self, lam, exp):
        return self.Table(self.fp, exp, lam)

def setupDefaults(grid):
    ax = grid[0]
    ax.xaxis.set_major_locator(plt.MultipleLocator(10))
    ax.set_xlim(-15, 15)
    ax.set_ylim(0, 50)

def algLabelsNoSrc(dt, units):
    abbr, src_str = dt.string_parts()
    return '%s (%s)' % (abbr, units)

def exp_order(mom):
    return {'calc':0, 'Linear':1, 'ZPHI':2, 'SC':3, 'MSC':4}[mom.source]

def make_figs(data_cache, out_dir='.'):
    wavelengths,exps = data_cache.sub_keys()
    process_all_atten(data_cache)
    plt.rcParams['savefig.dpi'] = 200
    plt.rcParams['font.size'] = 10
    plots.defaults.axisDefaults.setup = setupDefaults
    for lam_text in wavelengths:
        for exp in exps:
            data = data_cache[lam_text, exp]
            with datatypes.PlotInfoContext(wavelength=data.wavelength):
                with defaults.colorbarLabeller(algLabelsNoSrc):
                    for pol,mom in [('H', datatypes.Attenuation),
                                    ('V', datatypes.Attenuation),
                                    (None, datatypes.DiffAtten)]:
                        fig = plt.figure(figsize=(6, 4))
                        moments = data.fields.grabAll(mom, filt=lambda f: f.pol==pol and f.source not in ('average', 'ts'))
                        moments = sorted(moments, key=exp_order)
                        grid = defaults.multipanel_cbar_row(fig, (1, len(moments)), moments, data,
                                                            rect=[0.08, 0.10, 0.91, 0.91])
                        for ax,m in zip(grid, moments):
                            src = m.source
                            l = ax.set_title('Truth' if src == 'calc' else src)
                            l.set_verticalalignment('bottom')
                        fig.suptitle('%s - %s' % (exp, mom.name), fontsize=14)
                        if pol is None:
                            fname = '%s_%s_%s.png' % (lam_text, exp.replace(' ', ''), mom.name.replace(' ', '_'))
                        else:
                            fname = '%s_%s_%s_%s.png' % (lam_text, exp.replace(' ', ''), mom.name.replace(' ', '_'), pol)
                        fig.savefig(os.path.join(out_dir, fname), bbox_inches='tight')
                        plt.close(fig)

    def calc_differences_algs(data, dt=datatypes.Attenuation, pol='H'):
        destMap = {datatypes.Attenuation:datatypes.AttenDelta,
                datatypes.DiffAtten:datatypes.DiffAttenDelta,
                datatypes.SpecAttenuation:datatypes.SpecAttenDelta,
                datatypes.SpecDiffAtten:datatypes.SpecDiffAttenDelta}
        ref_field = data.fields.grabData(dt, pol=pol, source='calc')
        fields = data.fields.grabAll(dt, filt=lambda f: f.pol == pol and f.source not in ('calc', 'average', 'ts'))

        for f in fields:
            data.addField(data.fields[f] - ref_field, destMap[dt], pol=f.pol, source=f.source)

    for d in data_cache.values():
        calc_differences_algs(d, dt=datatypes.Attenuation, pol='H')
        calc_differences_algs(d, dt=datatypes.Attenuation, pol='V')
        #calc_differences_algs(d, dt=datatypes.SpecAttenuation, pol='H')
        calc_differences_algs(d, dt=datatypes.DiffAtten, pol=None)
        #calc_differences_algs(d, dt=datatypes.SpecDiffAtten, pol=None)

    for lam_text in wavelengths:
        for exp in exps:
            data = data_cache[lam_text, exp]
            with datatypes.PlotInfoContext(wavelength=data.wavelength):
                with defaults.colorbarLabeller(algLabelsNoSrc):
                    for pol,mom in [('H', datatypes.AttenDelta),
                                    ('V', datatypes.AttenDelta),
                                    (None, datatypes.DiffAttenDelta)]:
                        fig = plt.figure(figsize=(6, 4))
                        moments = data.fields.grabAll(mom, filt=lambda f: f.pol==pol and f.source not in ('average', 'ts'))
                        moments = sorted(moments, key=exp_order)
                        grid = defaults.multipanel_cbar_row(fig, (1, len(moments)), moments, data,
                                                            rect=[0.08, 0.05, 0.91, 0.85])
                        for ax,m in zip(grid, moments):
                            l = ax.set_title(m.source)
                            l.set_verticalalignment('bottom')
                        fig.suptitle('%s - %s' % (exp, mom.name), fontsize=14)
                        if pol is None:
                            fname = '%s_%s_%s.png' % (lam_text, exp.replace(' ', ''), mom.name.replace(' ', '_'))
                        else:
                            fname = '%s_%s_%s_%s.png' % (lam_text, exp.replace(' ', ''), mom.name.replace(' ', '_'), pol)
                        fig.savefig(os.path.join(out_dir, fname), bbox_inches='tight')
                        plt.close(fig)

    limits = {('C', 'H'):2.0, ('C', 'V'):2.0, ('C', None):0.75,
            ('X', 'H'):8.0, ('X', 'V'):8.0, ('X', None):1.0}
    stats = StatsFile(os.path.join(out_dir, 'spec_atten_stats.tex'))
    for lam_text in wavelengths:
        for exp in exps:
            with stats.table(lam_text, exp) as tab:
                data = data_cache[lam_text, exp]
                with datatypes.PlotInfoContext(wavelength=data.wavelength):
                    with defaults.colorbarLabeller(algLabelsNoSrc):
                        for pol,mom in [('H', datatypes.SpecAttenuation),
                                ('V', datatypes.SpecAttenuation),
                                (None, datatypes.SpecDiffAtten)]:
                            ref_mom = data.fields.grab(mom, pol=pol, source='calc')
                            ref_field = data.fields[ref_mom]
                            moments = data.fields.grabAll(mom,
                                    filt=lambda f: f.pol == pol and f.source not in ('calc', 'average', 'ts', 'sweep'))
                            moments = sorted(moments, key=exp_order)

                            nrows = 2
                            ncols = len(moments) // nrows
                            fig, axes = plt.subplots(nrows, ncols, sharex=True,
                                    sharey=True, figsize=(6, 4))
                            fig.subplots_adjust(left=0.10, top=0.85, bottom=0.12,
                                    hspace=0.45)
                            xlim = limits[lam_text, pol]
                            for ind, (m, ax, panel_label) in enumerate(zip(moments,
                                    axes.flatten(), LabelGenerator('a'))):
                                alg_field = data.fields[m]
                                mom_abbr = m.string_parts()[0]
                                mask = (ref_field > 0.02) & (alg_field > 0.02)
                                norm = datatypes.TypePlotInfo[ref_mom.type]['norm']
                                hist, xedge, yedge = np.histogram2d(ref_field[mask], alg_field[mask], bins=50,
                                        range=[[norm.vmin, norm.vmax], [norm.vmin, norm.vmax]])
                                ax.pcolormesh(xedge, yedge, hist.T, norm=LogNorm())
                                ax.plot([0.0, xlim], [0.0, xlim], 'k--')
                                ax.grid(True)
                                panel_label.patch.set_boxstyle("round, pad=0., rounding_size=0.2")
                                ax.add_artist(panel_label)
                                l = ax.set_title(m.source)
                                l.set_verticalalignment('bottom')
                                if ind % nrows == 0:
                                    ax.set_ylabel(mom_abbr)
                                ax.set_xlabel('True ' + mom_abbr)

                                tab.write_stats(pol, m.source,
                                        *regress_stats(ref_field[mask], alg_field[mask]))

                            axes[0,0].set_xlim(0.0, xlim)
                            axes[0,0].set_ylim(0.0, xlim)
                            axes[0,0].xaxis.set_major_locator(plt.MaxNLocator(nbins=5))
                            axes[0,0].yaxis.set_major_locator(plt.MaxNLocator(nbins=5))

                            fig.suptitle('%s - %s' % (exp, mom.name), fontsize=14)
                            if pol is None:
                                fname = '%s_%s_%s_scatter.png' % (lam_text, exp.replace(' ', ''), mom.name.replace(' ', '_'))
                            else:
                                fname = '%s_%s_%s_%s_scatter.png' % (lam_text, exp.replace(' ', ''), mom.name.replace(' ', '_'), pol)

                            fig.savefig(os.path.join(out_dir, fname), bbox_inches='tight')
                            plt.close(fig)

if __name__ == '__main__':
    data_cache = load_model_experiments('ref_runs/')
    make_figs(data_cache)
