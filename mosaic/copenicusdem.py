"""
Extraction of the Copernicus DEM.
https://spacedata.copernicus.eu/collections/copernicus-digital-elevation-model
"""

from sentinelhub import SHConfig, CRS, BBox, MimeType, SentinelHubRequest, DataCollection, bbox_to_dimensions, BBoxSplitter, SentinelHubDownloadClient, MosaickingOrder
import sentinelhub
from pathlib import Path
from mosaic import evalscripts
import rasterio
import numpy as np
import datetime
from mosaic.utils import shretry, gdal_merge

NO_DATA = -9999
RESOLUTION = 10
CRS = sentinelhub.CRS.WGS84

def download(bbox, time_interval, output):

    def get_image(bbox, resolution):
        size = bbox_to_dimensions(bbox, resolution=resolution)
        request = SentinelHubRequest(
            data_folder="test_dir",
            evalscript=evalscripts.DEM_COPERNICUS_30,
            input_data=[
                SentinelHubRequest.input_data(
                    data_collection=DataCollection.DEM_COPERNICUS_30,
                    time_interval=time_interval,
                    mosaicking_order=MosaickingOrder.MOST_RECENT
                )
            ],
            responses=[SentinelHubRequest.output_response("default", MimeType.TIFF)],
            bbox=bbox,
            size=size,
            config=None,
        )
        return(request)
    

    bbox_splitter = BBoxSplitter(
        [ BBox(bbox, crs=CRS) ], crs = CRS, split_shape = (10, 10)
    )  # bounding box will be split into grid of 5x4 bounding boxes

    bbox_list = bbox_splitter.get_bbox_list()
    sh_requests = [get_image(bbox, RESOLUTION) for bbox in bbox_list]
    dl_requests = [request.download_list[0] for request in sh_requests]
    _ = SentinelHubDownloadClient(config=None).download(dl_requests, max_threads=5)

    data_folder = sh_requests[0].data_folder
    tiffs = [Path(data_folder) / req.get_filename_list()[0] for req in sh_requests]
    str_tiffs = [str(tiff) for tiff in tiffs]
    gdal_merge(str_tiffs, bbox, output=output, dstnodata=NO_DATA)


def mosaic(bbox, start, end, output, max_retry = 10):

    shretry(max_retry, download, bbox = bbox, time_interval=(start, end), output = output)

    with rasterio.open(output, 'r') as file:
        bands = file.read()
        mask  = bands[-1,  :, :]
        bands = bands[:-1, :, :]
        profile = file.profile

    profile.update(count = bands.shape[0])
    with rasterio.open(output, 'w', **profile) as file:

        bands = np.array(bands).transpose((1,2,0))
        bands[mask==0] = NO_DATA
        bands = np.array(bands).transpose((2,0,1))

        file.nodata = NO_DATA
        file.write(bands)




if(__name__=='__main__'):
    
    import datetime
    bbox = (
        46.16, 
        -16.15, 
        46.51, 
        -15.58
    )

    start = datetime.datetime(2019, 3, 1)
    end = datetime.datetime(2019, 12, 31)
    

    mosaic(bbox = bbox, start = start, end = end, output = './mosaic.tiff')