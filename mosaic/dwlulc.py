"""
Extraction of the Dynamic World.
https://dynamicworld.app/
"""

import tensorflow as tf
import numpy as np
from mosaic.sentinel2 import download
from mosaic.utils import shretry
from mosaic.clouddetection import Inference as CloudDetection
from dynamicworld.inference import Inference as LULCDetection
import os
import shutil
import rasterio

from mosaic.utils import split_interval

NO_DATA = 240



def mosaic(bbox, start, end, output, n, max_retry = 10, split_shape=(10, 10)):
    slots = split_interval(start, end, n)
    
    landcover = LULCDetection()
    clouddetection = CloudDetection(all_bands=True)


    merged_mask = None
    merged_bands = None

    files = []
    for slot in slots:
        print(slot)
        image = './image_{start}_{end}.tiff'.format(start = slot[0], end = slot[1])
        shretry(max_retry, download, bbox = bbox, time_interval = slot, output = image, split_shape=split_shape)
        with rasterio.open(image, 'r') as file:
            bands = file.read()
            mask  = bands[-1,  :, :]
            bands = bands[:-1, :, :]

            bands = bands.transpose((1,2,0))
            s2_mask = bands==file.nodata

            bands[s2_mask] = 0

            # plt.imshow(bands[:, :, [3,2,1]].clip(0,3000)/3000)
            # plt.show()

            cloud_prob = clouddetection.predict(bands.astype(np.float32)[np.newaxis, ...]/10000.0)[0, :, :]
            bands = landcover.predict(bands)

            mask = mask>0
            mask[cloud_prob > 0.4] = 0
            mask[s2_mask.prod(-1)] = 0
            bands[mask==0] = 1.0/bands.shape[-1]

            profile = file.profile

        bands = bands.transpose((2,0,1)) #metto la predizione sulla coordinata 0



        if(merged_mask is None):
            merged_mask = mask
            merged_bands = bands
        else:
            merged_mask = merged_mask + mask
            merged_bands = merged_bands + bands
        
        files.append(image)
        if(len(files)<len(slots)):
            os.remove(image)

    
    merged_mask[merged_mask==0] = np.nan
    merged_bands = merged_bands/merged_mask

    merged_bands = merged_bands.argmax(0)

    merged_bands[np.isnan(merged_bands)] = NO_DATA
    merged_bands = np.expand_dims(merged_bands, 0)
    merged_bands = merged_bands.astype(np.int16)
    
    
    shutil.copyfile(files[-1], output)

    profile.update(count = 1, dtype = np.int16)
    with rasterio.open(output, 'w', **profile) as file:
        file.write(merged_bands)
    os.remove(files[-1])


if __name__=='__main__':
    
    import argparse
    from argparse import ArgumentParser
    import datetime
    import rasterio
    import matplotlib.pyplot as plt
    
    parser = ArgumentParser()
    
    parser.add_argument("--minlong", type=float, default=46.00, help="minimum value for longitude used to create the bounding box")
    parser.add_argument("--minlat", type=float, default=-16.15, help="minimum value for latitude used to create the bounding box")
    parser.add_argument("--maxlong", type=float, default=46.07, help="maximum value for longitude used to create the bounding box")
    parser.add_argument("--maxlat", type=float, default=-16.01, help="maximum value for latitude used to create the bounding box")
    
    parser.add_argument("--start_date", type=str, default="2021/10/5", help="start date, in format year/month/day")
    parser.add_argument("--end_date", type=str, default="2021/12/7", help="end date, in format year/month/day")
    parser.add_argument("--time_splits", type=int, default=2, help="number of periods to use")

    parser.add_argument('--no_mask_clouds', dest='no_mask_clouds', default=False, action='store_true',help="Set to not mask clouds")

    parser.add_argument("--split_shape", type=tuple, default=(2,2), help="bounding box splits in (row,columns)")
    parser.add_argument("--max_retry", type=int, default=10, help="maximimun number of requests for the same images")

    parser.add_argument("--output", type=str, default="./mosaic.tiff", help="output path")
    
    args = parser.parse_args()

    bbox = (args.minlong, args.minlat, args.maxlong, args.maxlat) 

    start = args.start_date.split("/")
    start = datetime.datetime(int(start[0]), int(start[1]), int(start[2]))
    
    end= args.end_date.split("/")
    end = datetime.datetime(int(end[0]), int(end[1]), int(end[2]))
    
    mosaic(
        bbox = bbox, 
        start = start, 
        end = end, 
        n = args.time_splits, 
        output = args.output, 
        max_retry=args.max_retry, 
        split_shape=args.split_shape,
        mask_clouds=not(args.no_mask_clouds)
    )

    with rasterio.open(args.output, 'r') as file:
        bands = file.read()
        plt.imshow(bands[0, :, :], vmin=0, vmax=10)
        png_output = args.output.replace(".tiff",".png")
        plt.savefig(png_output)