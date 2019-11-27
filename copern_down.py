"""
Simple Sentinel downloader
Author:  Maxim Chernetskiy, University College London, 2019
Version: 0.0.1
"""

import numpy as np
import fiona as fi
import subprocess as sp
import requests
import urllib.request
import time

#shp_file = '/home/maksim/vector/cropmap2017_wgs84/cropmap2017_wgs84.shp'
shp_file = '/home/maksim/vector/french_farms/french_farms_rect.shp'

srs_shp = fi.collection(shp_file, 'r')
#dir_out = '/media/fun-drive/datasets/s1_scihub/french_farms/'
dir_out = '/media/fun-drive/datasets/s2_scihub/france/'

#product_type = 'SLC'
#producttype = 'GRD'
producttype = 'S2MSI1C'
platformname = 'Sentinel-2'
#platformname = 'Sentinel-1'

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

# Get total number of results by query
com_str = 'wget --no-check-certificate ' +\
          '--user=cervest --password=cervest69 ' +\
          '--output-document=%s ' % query_res +\
          '"https://scihub.copernicus.eu/dhus/search?start=0&rows=100&q=' +\
          'footprint:\\"Intersects(%s)\\" AND ' % poly_str +\
          'beginposition:[2018-01-01T00:00:00.000Z TO 2019-07-25T00:00:00.000Z] AND ' +\
          'platformname:%s AND ' % platformname +\
          'producttype:%s"' % producttype
print(com_str)
sp.check_output(com_str, shell=True)

# Read total number of results
with open(query_res) as f:
    for line in f:
        if 'totalResults' in line:
            total_n = int(line.split('>')[1].split('<')[0])

# Query and download all results with 100 results per page
for page_start in range(0, total_n, 100):
    query_res = 'query_results_%d.txt' % page_start
    # Do a wget string
    com_str = 'wget --no-check-certificate ' +\
              '--user=sigil --password=Maxim1978 ' +\
              '--output-document=%s ' % query_res +\
              '"https://scihub.copernicus.eu/dhus/search?start=%d&rows=100&q=' % page_start +\
              'footprint:\\"Intersects(%s)\\" AND ' % poly_str +\
              'beginposition:[2018-01-01T00:00:00.000Z TO 2019-07-25T00:00:00.000Z] AND ' +\
              'platformname:%s AND ' % platformname +\
              'producttype:%s"' % producttype
    #print(com_str)
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
                #com_str = 'wget --content-disposition --continue ' +\
                #'--user=cervest --password=cervest69 ' +\
                #'"https://scihub.copernicus.eu/dhus/odata/v1/Products(\'' + uuid + '\')/\$value" ' +\
                #'-P %s' % dir_out
                
                #cmd_online = 'https://scihub.copernicus.eu/dhus/odata/v1/Products(\'' + uuid + '\')/Online/\$value'
                
                com_online = 'wget --no-check-certificate --content-disposition --continue '+\
                '--user=cervest --password=cervest69 ' +\
                '"https://scihub.copernicus.eu/dhus/odata/v1/Products(\'' + uuid + '\')/Online/\$value" '

                print(com_online)
                sp.check_output(com_online, shell=True)
                f = open("$value")
                online = f.read()
                print('Online: ', online)
                f.close()
                sp.check_output("rm '$value'", shell=True)
                
                com_str = 'wget --no-check-certificate --content-disposition --continue '+\
                '--user=cervest --password=cervest69 ' +\
                '"https://scihub.copernicus.eu/dhus/odata/v1/Products(\'' + uuid + '\')/\$value" ' +\
                '-P %s' % dir_out
                
                if online == 'false':
                    try:
                        sp.check_output(com_str, shell=True)
                    except:
                        time.sleep(600)
                #r = requests.get(cmd_online, auth=('cervest', 'cervest69'))
                #r = urllib.request.urlopen(cmd_online).read()
                #print('Online: ', r.status_code, r.headers, r.content, r.text, r.json)
                
                
                #print(com_str)
                #try:
                sp.check_output(com_str, shell=True)
                #except:
                #    print('Something going wrong. Probably the product offline')
