"""
Extraction of the ESA World Cover.
https://esa-worldcover.org/en
"""

from sentinelhub import SHConfig, BBox, MimeType, SentinelHubRequest, DataCollection, bbox_to_dimensions, BBoxSplitter, SentinelHubDownloadClient, MosaickingOrder
import sentinelhub
from pathlib import Path
from mosaic import evalscripts
import rasterio
import numpy as np
import datetime
from mosaic.utils import shretry, gdal_merge
import os

NO_DATA = 240
RESOLUTION = 10
CRS = sentinelhub.CRS.WGS84


def download(bbox, time_interval, output, split_shape = (10, 10)):

    def get_image(bbox, resolution):
        size = bbox_to_dimensions(bbox, resolution=resolution)
        request = SentinelHubRequest(
            data_folder="test_dir",
            evalscript=evalscripts.WORLDCOVER,
            input_data=[
                SentinelHubRequest.input_data(
                    data_collection=DataCollection.define_byoc(collection_id="0b940c63-45dd-4e6b-8019-c3660b81b884"),
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
        [ BBox(bbox, crs=CRS) ], crs = CRS, split_shape = split_shape
    )  # bounding box will be split into grid of 5x4 bounding boxes

    bbox_list = bbox_splitter.get_bbox_list()
    sh_requests = [get_image(bbox, RESOLUTION) for bbox in bbox_list]
    dl_requests = [request.download_list[0] for request in sh_requests]
    _ = SentinelHubDownloadClient(config=None).download(dl_requests, max_threads=5)

    data_folder = sh_requests[0].data_folder
    tiffs = [Path(data_folder) / req.get_filename_list()[0] for req in sh_requests]
    str_tiffs = [str(tiff) for tiff in tiffs]
    gdal_merge(str_tiffs, bbox, output=output, dstnodata=NO_DATA)
    
    for str_tiff in str_tiffs:
        os.remove(str_tiff)
    
def mosaic(bbox, start, end, output, max_retry=10, split_shape=(10, 10)):

    shretry(max_retry, download, bbox = bbox, time_interval=(start, end), output = output, split_shape = split_shape)

    with rasterio.open(output, 'r') as file:
        bands = file.read()
        mask  = bands[-1,  :, :]
        bands = bands[:-1, :, :]
        profile = file.profile


    profile.update(count = bands.shape[0])
    with rasterio.open(output, 'w', **profile) as file:
        bands = np.array(bands).transpose((1,2,0))

        bands[bands == 0] = NO_DATA
        bands[bands == 10] = 0
        bands[bands == 20] = 1
        bands[bands == 30] = 2
        bands[bands == 40] = 3
        bands[bands == 50] = 4
        bands[bands == 60] = 5
        bands[bands == 70] = 6
        bands[bands == 80] = 7
        bands[bands == 90] = 8
        bands[bands == 95] = 9
        bands[bands == 100] = 10
        bands[mask==0] = NO_DATA
        bands = np.array(bands).transpose((2,0,1))

        file.nodata = NO_DATA
        file.write(bands)