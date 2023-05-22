"""
Extraction of the Sentinel-1.
https://sentinels.copernicus.eu/web/sentinel/missions/sentinel-1
"""

from sentinelhub.geometry import Geometry
from sentinelhub.time_utils import parse_time
from mosaic import evalscripts
from pathlib import Path
from sentinelhub import SentinelHubCatalog
from sentinelhub import CRS, BBox, MimeType, SentinelHubRequest, DataCollection, bbox_to_dimensions, SentinelHubDownloadClient, MosaickingOrder
import sentinelhub
import datetime
from sentinelhub import BBoxSplitter
import os
import shutil
import numpy as np
import sentinelhub
from mosaic.utils import shretry, gdal_merge
import shapely
import rasterio

NO_DATA = -9999
RESOLUTION = 10
CRS = sentinelhub.CRS.WGS84


def get_orbits(bbox, time_interval):

    catalog = SentinelHubCatalog()

    search_iterator = catalog.search(
        DataCollection.SENTINEL1_IW_DES,
        bbox=bbox,
        time=time_interval,
    )

    results = list(search_iterator)
    print("Total number of results:", len(results))

    images = {}
    dates  = {}
    bboxes = {}

    for result in results:

        date = parse_time(result['properties']['datetime'])
        id = result['id']

        if(result['properties']['platform'] == 'sentinel-1a'):
            orbit =  (result['properties']['sat:absolute_orbit'] - 73)%175 + 1
        elif(result['properties']['platform'] == 'sentinel-1b'):
            orbit =  (result['properties']['sat:absolute_orbit'] - 27)%175 + 1
        else:
            raise Exception('Error, unreconized platform')
        

        #refbbox = bbox.transform_bounds(result['geometry']['crs']['properties']['name'])
        sbbox = Geometry(result['geometry'], crs = result['geometry']['crs']['properties']['name'])
        sbbox = sbbox.transform(CRS)        

        #intersect = sbbox.geometry.intersection(refbbox.geometry).area
        #intersect = intersect/refbbox.geometry.area
        
        if(orbit not in dates.keys()):
            images[orbit] = []
            dates[orbit]  = []
            bboxes[orbit] = []
        
        images[orbit] += [id]
        dates[orbit] += [date]
        bboxes[orbit] += [sbbox]
    

    for orbit in dates.keys():
        idxs = [i[0] for i in sorted(enumerate(dates[orbit]), key=lambda x:x[1])]
        dates[orbit]  = [dates[orbit][idx] for idx in idxs]
        bboxes[orbit] = [bboxes[orbit][idx] for idx in idxs]
        images[orbit] = [images[orbit][idx] for idx in idxs]

    return(dates, bboxes)

def group_dates(dates, timedelta = datetime.timedelta(hours=1)):
   
    #idxs = [i[0] for i in sorted(enumerate(dates), key=lambda x:x[1])]
    #dates = [dates[idx] for idx in idxs]
    groups_idxs = []

    prior_date = None
    current_group = None
    for i, date in enumerate(dates):
        if i == 0:
            prior_date = date
            current_group = 0
            groups_idxs.append(current_group)
        else:
            if(abs(prior_date - date)<timedelta):
                groups_idxs.append(current_group)
            else:
                current_group = current_group + 1
                groups_idxs.append(current_group)

            prior_date = date

    return(groups_idxs)


def _get_image(bbox, time_interval, resolution):
    size = bbox_to_dimensions(bbox, resolution=resolution)
    request = SentinelHubRequest(
        data_folder="test_dir",
        evalscript=evalscripts.SENTINEL1,
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL1_IW_DES,
                time_interval=time_interval,
                mosaicking_order=MosaickingOrder.MOST_RECENT,
                other_args = {"dataFilter":{"demInstance":"COPERNICUS_30"},"processing":{"orthorectify":True,"backCoeff":"GAMMA0_ELLIPSOID"}}
            )
        ],
        responses=[SentinelHubRequest.output_response("default", MimeType.TIFF)],
        bbox=bbox,
        size=size,
        config=None,
    )
    return(request)

def get_image(
        bbox, 
        time_interval, 
        resolution,
        split_shape = (10,10)
    ):

    sh_requests = None

    if(split_shape is None):
        sh_requests = [_get_image(bbox, time_interval, resolution)]
    else:
        bbox_splitter = BBoxSplitter([ bbox], crs = CRS, split_shape = split_shape)
        bbox_list = bbox_splitter.get_bbox_list()
        sh_requests = [_get_image(bbox, time_interval, resolution) for bbox in bbox_list]

    dl_requests = [request.download_list[0] for request in sh_requests]
    _ = SentinelHubDownloadClient(config=None).download(dl_requests, max_threads=5)
    tiffs = [Path(sh_requests[0].data_folder) / req.get_filename_list()[0] for req in sh_requests]
    str_tiffs = [str(tiff) for tiff in tiffs]
    return(str_tiffs)


def subsample(groups, n):
    if(n<len(groups)):
        edges = [i * int(len(groups)/n) for i in range(n+1)]
        ss_groups = [groups[edges[i]] for i in range(len(edges)-1)]
    else:
        ss_groups = groups
    return(ss_groups)



def mosaic(bbox, start, end, output, n, max_retry = 10):

    time_interval =  [start, end]
    bbox = BBox(bbox=bbox, crs=CRS)

    dates, bboxes = get_orbits(bbox, time_interval)
    intersections = {}
    date_groups = {}
    bbox_groups = {}

    for orbit in dates.keys():

        groups_idxs = group_dates(dates[orbit])

        date_groups[orbit] =  [[] for i in range(max(groups_idxs)+1)]
        bbox_groups[orbit] =  [[] for i in range(max(groups_idxs)+1)]
        
        
        for idx in range(len(groups_idxs)):
            date_groups[orbit][groups_idxs[idx]].append(dates[orbit][idx])
            bbox_groups[orbit][groups_idxs[idx]].append(bboxes[orbit][idx])

        intersection_groups = []
        for idx in range(len(bbox_groups[orbit])):
            bbox_group_polygon = shapely.unary_union([bbox.geometry for bbox in bbox_groups[orbit][idx]])
            intersection = bbox_group_polygon.intersection(bbox.geometry).area
            intersection = intersection/bbox.geometry.area
            intersection_groups.append(intersection)
        intersections[orbit] = np.mean(intersection_groups)

    orbit = sorted(intersections, key=intersections.get, reverse=True)[0]

    date_groups = date_groups[orbit]
    bbox_groups = bbox_groups[orbit]
    intersections = intersections[orbit]
    
    groups = subsample(date_groups, n = n)

    merged_mask = None
    merged_bands = None
    files = []
    for group_idx, group in enumerate(groups):

        partial_outputs = []
        cache_files = []
        for timestamp_idx, timestamp in enumerate(group):
            
            partial_output = './image_{group_idx}_{timestamp_idx}.tiff'.format(group_idx=group_idx, timestamp_idx=timestamp_idx)
            
            tiffs = shretry(max_retry, get_image, bbox = bbox, time_interval = (timestamp - datetime.timedelta(hours=1), timestamp + datetime.timedelta(hours=1)), resolution = RESOLUTION, split_shape=(10, 10))
            cache_files.extend(tiffs)
            
            if(len(tiffs)>1):
                gdal_merge(tiffs, list(bbox), output=partial_output)
            else:
                shutil.copyfile(tiffs[0], partial_output)

            partial_outputs.append(partial_output)

        group_output = './image_{group_idx}.tiff'.format(group_idx=group_idx)
        gdal_merge(partial_outputs, list(bbox), output=group_output, dstnodata=NO_DATA)
        
        with rasterio.open(group_output, 'r') as file:
            bands = file.read()
            mask  = bands[-1,  :, :]
            bands = bands[:-1, :, :]
            profile = file.profile

        profile.update(count = bands.shape[0])
        with rasterio.open(group_output, 'w', **profile) as file:
            bands = np.array(bands).transpose((1,2,0))
            bands[mask==0] = NO_DATA
            bands = np.array(bands).transpose((2,0,1))
            file.nodata = NO_DATA
            file.write(bands)

        bands[bands==NO_DATA] = np.nan
        
        mask = np.ones_like(bands)
        mask[np.isnan(bands)] = 0
        bands[np.isnan(bands)] = 0

        if(merged_mask is None):
            merged_mask = mask
            merged_bands = bands
        else:
            merged_mask = merged_mask + mask
            merged_bands = merged_bands + bands
        
        files.append(group_output)
        
        for tiff in partial_outputs:
            os.remove(tiff)
        #for tiff in cache_files:
        #    os.remove(tiff)
        #if(len(files)<len(groups)):
        #    os.remove(group_output)

    merged_mask[merged_mask==0] = np.nan
    merged_bands = merged_bands/merged_mask
    merged_bands[np.isnan(merged_bands)] = NO_DATA
    
    shutil.copyfile(files[-1], output)
    with rasterio.open(output, 'r+') as file:
        file.write(merged_bands)
    os.remove(files[-1])






if __name__ == '__main__':
    start = "2020-12-10"
    end = "2021-02-01"
    bbox = ([
        10.81219793387203, 
        42.86271296865057, 
        11.104213429449025, 
        43.1  
    ])


    n = 3
    mosaic(bbox = bbox, start = start, end = end, output = './mosaic.tiff', n = n)