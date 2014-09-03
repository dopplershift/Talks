bands = ['C', 'X']
exps = ['Control', 'Sidelobe', 'Beamwidth', 'Radial Width', 'Range Resolution', 'Combined']

figs = ['Attenuation_H', 'Attenuation_Difference_H',
        'Attenuation_V', 'Attenuation_Difference_V',
        'Specific_Attenuation_H_scatter', 'Specific_Attenuation_V_scatter',
        'Differential_Attenuation', 'Differential_Attenuation_Difference',
        'Specific_Differential_Attenuation_scatter']

template = r'''\begin{{figure}}
    \centering
    \includegraphics[scale=0.95]{{figures/spatial/{0}_{1}_{2}}}
    \caption{{{0} {1}}}
    \label{{fig:{0}_sp_{1}_{2}}}
\end{{figure}}
'''

with open('gentex.tex', 'w') as outp:
    for exp in exps:
        outp.write('\section{{{0}}}\n\n'.format(exp))
        for band in bands:
            outp.write('\FloatBarrier\n\subsection{{{0} band}}\n\n'.format(band))
            for f in figs:
                outp.write(template.format(band, exp.replace(' ', ''), f) + '\n')
