
from argparse import ArgumentParser
import datetime

import mosaic.sentinel1
import mosaic.sentinel2
import mosaic.esalulc
import mosaic.dwlulc
import mosaic.copernicusdem

def get_parser(temporal):
    #parser.add_argument("--bbox", type=str, default="46.00/-16.15/46.02/-16.01", help="bounding box: minlong/minlat/maxlong/maxlat")

    parser = ArgumentParser()
    parser.add_argument("--minlong", type=float, default=46.00, help="minimum value for longitude used to create the bounding box")
    parser.add_argument("--minlat", type=float, default=-16.15, help="minimum value for latitude used to create the bounding box")
    parser.add_argument("--maxlong", type=float, default=46.05, help="maximum value for longitude used to create the bounding box")
    parser.add_argument("--maxlat", type=float, default=-16.01, help="maximum value for latitude used to create the bounding box")
    parser.add_argument("--start", type=str, default="2020/10/5", help="start date, in format year/month/day")
    parser.add_argument("--end", type=str, default="2021/12/7", help="end date, in format year/month/day")
    parser.add_argument("--split_shape", type=tuple, default=(10,10), help="bounding box splits in (row,columns)")
    parser.add_argument("--max_retry", type=int, default=10, help="maximimun number of requests for the same images")
    parser.add_argument("--output", type=str, default="./mosaic.tiff", help="output path")

    if(temporal == True):
        parser.add_argument("--n", type=int, default=3, help="number of periods to use")
    
    args = parser.parse_args()
    
    args.bbox = (args.minlong, args.minlat, args.maxlong, args.maxlat)

    args.start = args.start.split("/")
    args.start = datetime.datetime(int(args.start[0]), int(args.start[1]), int(args.start[2]))
    args.end   =  args.end.split("/")
    args.end   = datetime.datetime(int(args.end[0]), int(args.end[1]), int(args.end[2]))


    del args.minlong
    del args.minlat
    del args.maxlong
    del args.maxlat
    
    args = vars(args)
    
    return(args)

def sentinel1():
    mosaic.sentinel1.mosaic(**get_parser(temporal=True))

def sentinel2():
    mosaic.sentinel2.mosaic(**get_parser(temporal=True))

def dwlulc():
    mosaic.dwlulc.mosaic(**get_parser(temporal=True))

def esalulc():
    mosaic.esalulc.mosaic(**get_parser(temporal=False))

def copernicusdem():
    mosaic.copernicusdem.mosaic(**get_parser(temporal=False))