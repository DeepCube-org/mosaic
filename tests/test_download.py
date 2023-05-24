import datetime
import rasterio
import matplotlib.pyplot as plt

import mosaic.sentinel2
import mosaic.sentinel1

bbox = (
    46.00, 
    -16.15,
    46.02, 
    -16.01,
)

start = datetime.datetime(2021, 10, 5)
end = datetime.datetime(2021, 12, 7)
n = 3

def test_sentinel2():

    mosaic.sentinel2.mosaic(bbox = bbox, start = start, end = end, n = n, output = './mosaic_sentinel2.tiff', split_shape = (4,4), mask_clouds = True)
    
    with rasterio.open('./mosaic_sentinel2.tiff', 'r') as file:
        bands = file.read()
        plt.imshow(bands[[3, 2, 1], :, :].transpose((1,2,0)).clip(0, 3000)/3000, vmin=0, vmax=1)
        plt.savefig('./mosaic_sentinel2.png')

    assert bands.shape[0] == 13, 'Sentinel-2 must contain 13 bands'


def test_sentinel1():
    
    mosaic.sentinel1.mosaic(bbox = bbox, start = start, end = end, n = n, output = './mosaic_sentinel1.tiff', split_shape = (4,4), mask_clouds = True)
    
    with rasterio.open('./mosaic_sentinel1.tiff', 'r') as file:
        bands = file.read()
        plt.imshow(bands[[3, 2, 1], :, :].transpose((1,2,0)).clip(0, 3000)/3000, vmin=0, vmax=1)
        plt.savefig('./mosaic_sentinel1.png')
    
    assert bands.shape[0] == 13, 'Sentinel-2 must contain 13 bands'
