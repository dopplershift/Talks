# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

# <codecell>

import numpy as np
import matplotlib.pyplot as plt
import scipy.optimize as so
import scipy.linalg as sl
import quantities as pq
import disser.scatter
import disser.units
import dsd

# <codecell>

from functools import partial
get_gamma = partial(dsd.gamma_from_moments, shape=1.81028329387715)

# <codecell>

# Model distribution parameters
try:
    locals().update(np.load('model_dsd.npz'))
    qr = pq.Quantity(qr, 'g/m**3')
    nr = pq.Quantity(nr, 'm**-3')
    print 'Model data loaded from file.'
except IOError:
#    num = 1000
#    ind = 1453433
    from disser import io
    data = io.ModelData('/Users/rmay/repos/RadarSim/data/commas_wz_3600.nc')
    mask = (data.qr > 1e-5) & (data.nr > 1e-2)
    qr = data.qr[mask][::100]
    qr = qr.rescale('g/m**3')
    nr = data.nr[mask][::100]
    np.savez('model_dsd.npz', qr=qr, nr=nr)
    print 'Model data recalculated.'

# <codecell>

def calc_scatter(qr, nr, dist_func, lam, temp):
    try:
        len(temp)
    except TypeError:
        temp = np.array([temp])
    d = np.linspace(0.01, 8., 100).reshape(-1, 1) * pq.millimeter
    dist = dist_func(d, nr, qr)
    z = np.empty((len(temp),) + qr.shape, dtype=d.dtype)
    kdp = np.empty_like(z)
    zdr = np.empty_like(z)
    atten = np.empty_like(z)
    diff_atten = np.empty_like(z)
    temps = np.empty_like(z)
    for i,t in enumerate(temp):
        scat = disser.scatter.bulk_scatter(lam, t, dist, d)
        kdp[i] = scat.kdp.rescale('deg/km').magnitude
        zdr[i] = disser.units.to_linear(scat.zdr)
        z[i] = disser.units.to_linear(scat.z)
        atten[i] = scat.atten.rescale('dB/km').magnitude
        diff_atten[i] = scat.diff_atten.rescale('dB/km').magnitude
        temps[i].fill(t)
    return z.flatten(), zdr.flatten(), kdp.flatten(), atten.flatten(), diff_atten.flatten(), temps.flatten()

# <codecell>

def linear_fit_no_intercept(x, y, weights=None, mask=None):
    full_x = x
    if weights is None:
        weights = np.ones_like(y).reshape(-1, 1)
    if mask is not None:
        weights = weights[mask]
        x = x[mask]
        y = y[mask]
    coeffs,resid,rank,sigma = sl.lstsq(weights * x, y)
    coeffs = coeffs.squeeze()
    print np.sqrt(resid / (weights * weights).sum())
    print coeffs
    fit = coeffs * x
    return coeffs, fit

def power_law_fit(x_vars, y_var, weights=None, mask=None):
    full_x = x_vars
    if weights is None:
        weights = np.ones_like(y_var).reshape(-1, 1)
    if mask is not None:
        weights = weights[mask]
        x_vars = x_vars[mask]
        y_var = y_var[mask]
    intercept = np.empty_like(y_var).reshape(-1, 1)
    intercept.fill(np.e)
    x = np.concatenate((intercept.reshape(-1, 1),
                        x_vars), 1)
    y = weights * np.log(y_var).reshape(-1, 1)
    coeffs,resid,rank,sigma = sl.lstsq(weights * np.log(x), y)
    coeffs = coeffs.squeeze()
    coeffs[0] = np.exp(coeffs[0])
    print np.sqrt(resid / (weights * weights).sum())
    print coeffs
    intercept,pows = coeffs[0], coeffs[1:]
    fit = intercept * np.prod(full_x**pows, axis=-1)
    return coeffs, fit

# <codecell>

def fit_plot(x_vars, y_fit, y_truth, ylabel):
    xvar,xlabel = x_vars[0]
    fig,(ax, ax2) = plt.subplots(1, 2, sharey=False, squeeze=True)
    fig.set_size_inches(10, 6)
    fig.subplots_adjust(wspace=0.3)

    ax.plot(xvar, y_truth, 'ro', linestyle='none', alpha=0.1, label='Raw Calculation')
    ax.plot(xvar, y_fit, 'bs', linestyle='none', alpha=0.1, label='Fit')
    ax.grid()
    ax.legend(loc='upper left')
    ax.set_xlabel(xlabel + '(%s)' % xvar.dimensionality.latex)
    ax.set_ylabel(ylabel)
    #fig.tight_layout()

    ax2.plot(y_truth, y_fit - y_truth, 'bo', linestyle='none', alpha=0.1)
    ax2.grid()
    ax2.set_xlabel('True ' + ylabel)
    ax2.set_ylabel('Error')
    return fig, [ax, ax2]

# <headingcell level=2>

# Scattering Calculations

# <codecell>

lam = (pq.c / (5.4 * pq.GHz)).simplified
#temp = np.arange(0, 30, 5, dtype=np.float32)
temp = 20
z,zdr,kdp,atten,diff_atten, temps = calc_scatter(qr, nr, get_gamma, lam, temp)

# <headingcell level=2>

# Attenuation vs. Z

# <codecell>

scatter_vars = [(disser.units.to_dBz(z * disser.units.zUnit), r'$Z_H$')]

# <headingcell level=3>

# Attenuation

# <codecell>

coeffs,fit = power_law_fit(z.reshape(-1, 1), atten)
fig,ax = fit_plot(scatter_vars, fit, atten, r'$A_H$')

plt.savefig("basic_power_law.png", dpi=200)
# <codecell>

weights = (atten * atten).reshape(-1, 1)
coeffs,fit = power_law_fit(z.reshape(-1, 1), atten, weights)
fig,ax = fit_plot(scatter_vars, fit, atten, r'$A_H$')

plt.savefig("weighted_power_law.png", dpi=200)
