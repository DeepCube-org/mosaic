FROM nvcr.io/nvidia/tensorflow:23.02-tf2-py3

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update
RUN apt-get install -y gdal-bin
RUN apt-get install -y libgdal-dev
RUN export CPLUS_INCLUDE_PATH=/usr/include/gdal && export C_INCLUDE_PATH=/usr/include/gdal && pip install GDAL