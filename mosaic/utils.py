import subprocess
import os


def split_interval(start, end, n):
    if(n>1):
        n_chunks = n+1
        tdelta = (end - start) / n_chunks
        edges = [(start + i * tdelta).date().isoformat() for i in range(n_chunks)]
        slots = [(edges[i], edges[i + 1]) for i in range(len(edges) - 1)]
    else:
        slots = [(start.date().isoformat(), end.date().isoformat())]
    return(slots)

def shretry(max_retry, fun, **args):
    retry = 0
    while True:
        try:
            return(fun(**args))
        except Exception as e:
            print(e)

            retry = retry + 1 
            if(retry == max_retry):
                raise Exception('Error')


#Supports only local files
def gdal_merge(tiffs, bbox, output, dstnodata = None):

    filelist = 'input.txt'
    with open(filelist, 'w') as f:
        for tiff in tiffs:
            f.write('"'+tiff+'"'+'\n')

    
    command = 'gdalwarp{args} -overwrite -s_srs EPSG:4326 -t_srs EPSG:4326 -te {min_lon} {min_lat} {max_lon} {max_lat} --optfile {tiffs} "{output}"'
    if(dstnodata is not None):
        args = ' -dstnodata {dstnodata}'.format(dstnodata=dstnodata)
    else:
        args = ''
    command = command.format(args = args, min_lon = bbox[0], min_lat = bbox[1], max_lon = bbox[2], max_lat = bbox[3], tiffs = filelist, output = output)

    print(command)
    subprocess.run(command)
    os.remove(filelist)
    return(output)
