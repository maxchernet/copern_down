"""
Simple Sentinel downloader
Author:  Maxim Chernetskiy, University College London, 2019
Version: 0.0.1
"""

import numpy as np
import fiona as fi
import subprocess as sp
# import wget
# import urllib.request


# shp_file = '/home/maksim/vector/cropmap2017_wgs84/cropmap2017_wgs84.shp'
shp_file = '/home/maksim/vector/french_farms/french_farms_rect.shp'

srs_shp = fi.collection(shp_file, 'r')
dir_out = '/media/fun-drive/datasets/s1_scihub/french_farms/'

#product_type = 'SLC'
producttype = 'GRD'
#producttype = 'S2MSI1C'
#platformname = 'Sentinel-2'
platformname = 'Sentinel-1'

# Get all the coordinates from a shape file. I.e. it doesn't necessary to be a rectangle.
# It can consist of many records but we extract an outline of the whole thing.
lat_arr = []
lon_arr = []
for rec in srs_shp:
    coord = np.array(rec['geometry']['coordinates'])
    if len(coord.shape) == 3:
        lon_arr = np.append(lon_arr, coord[0, :, 0])
        lat_arr = np.append(lat_arr, coord[0, :, 1])

poly_str = 'POLYGON((%.4f %.4f, %.4f %.4f, %.4f %.4f, %.4f %.4f, %.4f %.4f))' % \
           (lon_arr.min(), lat_arr.max(),
            lon_arr.max(), lat_arr.max(),
            lon_arr.max(), lat_arr.min(),
            lon_arr.min(), lat_arr.min(),
            lon_arr.min(), lat_arr.max())

query_res = 'query_results.txt'

#'beginposition:[2019-10-27T00:00:00.000Z TO NOW] AND ' +\
# 2019-10-01T00:00:00.000Z TO 2019-10-13T00:00:00.000Z

#  'rows=10 AND start=0 AND ' +\

# Do a wget string
com_str = 'wget --no-check-certificate ' +\
          '--user=cervest --password=cervest69 ' +\
          '--output-document=%s ' % query_res +\
          '"https://scihub.copernicus.eu/dhus/search?start=100&rows=100&q=' +\
          'footprint:\\"Intersects(%s)\\" AND ' % poly_str +\
          'beginposition:[2018-01-01T00:00:00.000Z TO NOW] AND ' +\
          'platformname:%s AND ' % platformname +\
          'producttype:%s"' % producttype
print(com_str)
sp.check_output(com_str, shell=True)

# sp.check_output with shell=True is not safe. Below other methods which are usable instead of
# a system call.
# urllib.request.urlopen(com_str)
# wget.download(com_str)

# Look for uuid entities in the results
with open(query_res) as f:
    for line in f:
        if 'uuid' in line:
            uuid = line.split('>')[1].split('<')[0]
            com_str = 'wget --content-disposition --continue ' +\
            '--user=cervest --password=cervest69 ' +\
            '"https://scihub.copernicus.eu/dhus/odata/v1/Products(\'' + uuid + '\')/\$value" ' +\
            '-P %s' % dir_out
            #sp.check_output(com_str, shell=True)
