"""
Utility functions used by the other modules.
"""

import subprocess
import os


"""
Split a temporal interval in a set of sub interval having similar size.
"""
def split_interval(start, end, n):
    if(n>1):
        tdelta = (end - start) / n
        edges = [(start + i * tdelta).date().isoformat() for i in range(n+1)]
        slots = [(edges[i], edges[i + 1]) for i in range(len(edges)-1)]
    else:
        slots = [(start.date().isoformat(), end.date().isoformat())]
    return(slots)

"""
Retry multiple time the execution of a function with a set of parameters in input.
"""
def shretry(max_retry, fun, **args):
    for attempt in range(1,max_retry+1):
        try:
            return(fun(**args))
        except Exception as e:
            print(f"attempt {attempt} failed" )
    
    raise Exception('Execution unsuccessful')


"""
Wrapper around the execution of the merge of multiple images, using the GDAL library.
"""
def gdal_merge(tiffs, bbox, output, dstnodata = None):

    filelist = 'input.txt'
    with open(filelist, 'w') as f:
        for tiff in tiffs:
            f.write(tiff+'\n')

    
    command = 'gdalwarp{args} -overwrite -s_srs EPSG:4326 -t_srs EPSG:4326 -te {min_lon} {min_lat} {max_lon} {max_lat} --optfile {tiffs} {output}'
    if(dstnodata is not None):
        args = ' -dstnodata {dstnodata}'.format(dstnodata=dstnodata)
    else:
        args = ''
    command = command.format(args = args, min_lon = bbox[0], min_lat = bbox[1], max_lon = bbox[2], max_lat = bbox[3], tiffs = filelist, output = output)

    print(command)
    os.system(command)
    os.remove(filelist)
    return(output)



