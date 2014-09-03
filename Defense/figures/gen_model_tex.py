bands = ['C', 'X']
exps = ['Control', 'Canting', 'Shape', 'Temperature', 'Wavelength', 'Combined']

figs = ['Attenuation_H', 'Attenuation_Difference_H',
        'Specific_Attenuation_H_scatter',
        'Differential_Attenuation', 'Differential_Attenuation_Difference',
        'Specific_Differential_Attenuation_scatter']

figs_v = ['Attenuation_V', 'Attenuation_Difference_V', 'Specific_Attenuation_V_scatter']

template = r'''\begin{{frame}}
    \begin{{center}}
        \includegraphics<1>[scale=0.45]{{figures/{0}_{1}_{2}}}
        \includegraphics<2>[scale=0.45]{{figures/{0}_Control_{2}}}
    \end{{center}}
\end{{frame}}
'''

with open('gentex.tex', 'w') as outp:
    for exp in exps:
        #outp.write('\section{{{0}}}\n\n'.format(exp))
        for band in bands:
            #outp.write('\FloatBarrier\n\subsection{{{0} band}}\n\n'.format(band))
            for f in figs:
                outp.write(template.format(band, exp, f) + '\n')
    for exp in exps:
        #outp.write('\section{{{0}}}\n\n'.format(exp))
        for band in bands:
            #outp.write('\FloatBarrier\n\subsection{{{0} band}}\n\n'.format(band))
            for f in figs_v:
                outp.write(template.format(band, exp, f) + '\n')
