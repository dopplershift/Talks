from disser.experiments import load_spatial_experiments
from atten_model_figures import make_figs

if __name__ == '__main__':
    data_cache = load_spatial_experiments('spatial_runs/')
    make_figs(data_cache, out_dir='spatial')
