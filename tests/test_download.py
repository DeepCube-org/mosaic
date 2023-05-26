import datetime
import rasterio
import matplotlib.pyplot as plt

bbox = (
    46.00, 
    -16.15,
    46.06, 
    -16.01,
)

start = datetime.datetime(2020, 10, 5)
end = datetime.datetime(2021, 12, 7)
n = 3


def test_esalulc():
    import mosaic.esalulc

    mosaic.esalulc.mosaic(bbox = bbox, start = start, end = end, output = './mosaic_esalulc.tiff', split_shape = (4,4))
    with rasterio.open('./mosaic_esalulc.tiff', 'r') as file:
        bands = file.read()
        plt.imshow(bands[0, :, :], cmap='gray')
        plt.savefig('./mosaic_esalulc.png')
    assert bands.shape[0] == 1, 'ESALULC must contain 1 band'



def test_copernicusdem():
    import mosaic.copernicusdem

    mosaic.copernicusdem.mosaic(bbox = bbox, start = start, end = end, output = './mosaic_copernicusdem.tiff', split_shape = (4,4))
    with rasterio.open('./mosaic_copernicusdem.tiff', 'r') as file:
        bands = file.read()
        plt.imshow(bands[0, :, :], cmap='gray')
        plt.savefig('./mosaic_copernicusdem.png')
    assert bands.shape[0] == 1, 'COPERNICUSDEM must contain 1 band'

def test_sentinel2():
    import mosaic.sentinel2

    mosaic.sentinel2.mosaic(bbox = bbox, start = start, end = end, n = n, output = './mosaic_sentinel2.tiff', split_shape = (4,4), mask_clouds = True)
    with rasterio.open('./mosaic_sentinel2.tiff', 'r') as file:
        bands = file.read()
        plt.imshow(bands[[3, 2, 1], :, :].transpose((1,2,0)).clip(0, 3000)/3000, vmin=0, vmax=1)
        plt.savefig('./mosaic_sentinel2.png')
    assert bands.shape[0] == 13, 'Sentinel-2 must contain 13 bands'

def test_sentinel1():
    import mosaic.sentinel1

    mosaic.sentinel1.mosaic(bbox = bbox, start = start, end = end, n = n, output = './mosaic_sentinel1.tiff', split_shape = (4,4))
    with rasterio.open('./mosaic_sentinel1.tiff', 'r') as file:
        bands = file.read()
        plt.imshow(bands[0, :, :].clip(0, 0.5)/0.5, vmin=0, vmax=1, cmap='gray')
        plt.savefig('./mosaic_sentinel1.png')
    assert bands.shape[0] == 1, 'Sentinel-1 must contain 1 band'

def test_dwlulc():
    import mosaic.dwlulc

    mosaic.dwlulc.mosaic(bbox = bbox, start = start, end = end, n = n, output = './mosaic_dwlulc.tiff', split_shape = (4,4))
    with rasterio.open('./mosaic_dwlulc.tiff', 'r') as file:
        bands = file.read()
        plt.imshow(bands[0, :, :], cmap='gray')
        plt.savefig('./mosaic_dwlulc.png')
    assert bands.shape[0] == 1, 'DWLULC must contain 1 band'


