# -*- coding: utf-8 -*-

__version__ = '0.1.0'

import os

import yaml

configs = dict(root_path='/media/Datasets',
               images_dir='images',
               labelmaps_dir='labelmaps',
               native_images_dir='native',
               subsampled_images_dir_prefix='subsampled',
               images_crop_prefix='images_crop_',
               labelmaps_crop_prefix='labelmaps_crop_')

try:
    with open(os.path.expanduser('~/.midatasets.yaml')) as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
        configs.update(data)
except:
    print('Error loading ~/.midatasets.yaml')
