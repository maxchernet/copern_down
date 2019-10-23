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

srs_shp = fi.collection('/Users/max/satellite/cervest/shp/cropmap2017_wgs84.shp', 'r')

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

# Do a wget string
com_str = 'wget --no-check-certificate ' +\
          '--user=*** --password=*** ' +\
          '--output-document=%s ' % query_res +\
          '"https://scihub.copernicus.eu/dhus/search?q=' +\
          'footprint:\\"Intersects(%s)\\" AND ' % poly_str +\
          'beginposition:[2019-10-01T00:00:00.000Z TO NOW] AND ' +\
          'producttype:GRD"'
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
            '--user=Sigil --password=Maxim1978 ' +\
            '"https://scihub.copernicus.eu/dhus/odata/v1/Products(\'' + uuid + '\')/\$value"'
            sp.check_output(com_str, shell=True)