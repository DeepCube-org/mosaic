# SentinelHub - Mosaic

## Description

Simple Python Package for the extraction of mosaics from Sentinel-Hub.
Given a temporal range and a spatial bounding box, the code is able to create a mosaic from it.
For the generation of the Sentinel-2 L1C mosaic, the code uses the s2cloudless package in order to identify the clouds and mask them from the sentinel-2 images. The code is very simple but I have created it because I did not find a lot of examples of how to create this kind of objects, so I hope that it can help someone. 

s2cloudless can be slow for very big images, it would be very usefull to find a way to optimize it. I have a couple of ideas of how to do it but if someone is interested to contribute in this direction you are welcome.

#### Supported layers: 

- ESA WorldCover
- Sentinel-1 GRD
- Sentinle-2 L1C
- Copernicus DEM
- DynamicWorld 


#### Installation

```
docker build -t mosaic .
docker run -it -v %CD%:/opt/ml/code/ mosaic /bin/bash
```

```
cd /opt/ml/code/
pip install -e .
```
