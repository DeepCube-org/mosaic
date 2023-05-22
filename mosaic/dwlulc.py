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
from mosaic.utils import split_interval

NO_DATA = 240



def mosaic(bbox, start, end, output, n, max_retry = 10, split_shape=(10, 10), mask_clouds = True):
    slots = split_interval(start, end, n)
    
    landcover = LULCDetection(all_bands=True)
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

            cloud_prob = clouddetection.predict(bands.astype(np.float32)/10000.0)
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
    
    import datetime
    import rasterio
    import matplotlib.pyplot as plt
    import datetime

    bbox = (
    46.00, 
    -16.10,
    46.12, 
    -16.25,
    )
    
    start = datetime.datetime(2021, 10, 5)
    end = datetime.datetime(2021, 10, 25)
    n = 5
    
    mosaic(bbox = bbox, start = start, end = end, n = n, output = './mosaic.tiff', split_shape = (2,2), mask_clouds = False)