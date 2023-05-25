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

def download(bbox, time_interval, output, split_shape):

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
        [ BBox(bbox, crs=CRS) ], crs = CRS, split_shape = split_shape
    )  # bounding box will be split into grid of rows x columns bounding boxes

    bbox_list = bbox_splitter.get_bbox_list()
    sh_requests = [get_image(bbox, RESOLUTION) for bbox in bbox_list]
    dl_requests = [request.download_list[0] for request in sh_requests]
    _ = SentinelHubDownloadClient(config=None).download(dl_requests, max_threads=5)

    data_folder = sh_requests[0].data_folder
    tiffs = [Path(data_folder) / req.get_filename_list()[0] for req in sh_requests]
    str_tiffs = [str(tiff) for tiff in tiffs]
    gdal_merge(str_tiffs, bbox, output=output, dstnodata=NO_DATA)


def mosaic(bbox, start, end, output, max_retry = 10, split_shape=(10,10)):

    shretry(max_retry, download, bbox = bbox, time_interval=(start, end), output = output, split_shape=split_shape)

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
    
    from argparse import ArgumentParser
    import datetime
    
    
    parser = ArgumentParser()
    
    parser.add_argument("--minlong", type=float, default=46.00, help="minimum value for longitude used to create the bounding box")
    parser.add_argument("--minlat", type=float, default=-16.15, help="minimum value for latitude used to create the bounding box")
    parser.add_argument("--maxlong", type=float, default=46.07, help="maximum value for longitude used to create the bounding box")
    parser.add_argument("--maxlat", type=float, default=-16.01, help="maximum value for latitude used to create the bounding box")
    
    parser.add_argument("--start_date", type=str, default="2019/3/1", help="start date, in format year/month/day")
    parser.add_argument("--end_date", type=str, default="2019/12/31", help="end date, in format year/month/day")
    
    parser.add_argument("--split_shape", type=tuple, default=(10,10), help="bounding box splits in (row,columns)")
    parser.add_argument("--max_retry", type=int, default=10, help="maximimun number of requests for the same images")

    parser.add_argument("--output", type=str, default="./mosaic.tiff", help="output path")
    
    args = parser.parse_args()

    bbox = (args.minlong, args.minlat, args.maxlong, args.maxlat) 

    start = args.start_date.split("/")
    start = datetime.datetime(int(start[0]), int(start[1]), int(start[2]))
    
    end= args.end_date.split("/")
    end = datetime.datetime(int(end[0]), int(end[1]), int(end[2]))
    
    mosaic(bbox = bbox, start = start, end = end, output = args.output, max_retry=args.max_retry, split_shape=args.split_shape)