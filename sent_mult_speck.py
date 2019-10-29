"""
SNAPPY based multitemporal speckle filtering for Sentinel-1 data

Version: 0.0.1

Author: Maxim Chernetskiy, 2019

SNAPPY must be installed!

Example of usage:
python sent_mult_speck.py --list_in list.txt \
--shp_in /Users/max/satellite/cervest/shp/cropmap2017_wgs84.shp \
--dir_out /Volumes/lacie_data/satellite/Sentinel-1/cervest/proc_01/
"""

import numpy as np
import snappy
import fiona as fi
import time
import psutil
import os
import sys
import optparse


HashMap = snappy.jpy.get_type('java.util.HashMap')


def mt_speckle(p_in, f_out='s1a_speck.dim'):
    """
    Multi-Temporal speckle filtering

    :param p_in: input snap product
    :param str f_out: output file
    :return: Corrected snap product
    """
    parameters = snappy.HashMap()
    p_speck = snappy.GPF.createProduct('Multi-Temporal-Speckle-Filter', parameters, p_in)

    snappy.ProductIO.writeProduct(p_speck, f_out, "BEAM-DIMAP")

    return p_speck


def get_poly(shp_file):
    """
    Get corners of a shape file

    :param shp_file:
    :return:
    """

    srs_shp = fi.collection(shp_file, 'r')

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

    return poly_str


def get_subset(p_in, f_shp, f_out='s1a_subset.dim'):
    """
    Get a subset from data based on a shapefile

    :param p_in: input snap product
    :param f_shp:
    :return: Snap product
    """
    WKTReader = snappy.jpy.get_type('com.vividsolutions.jts.io.WKTReader')
    wkt = get_poly(f_shp)
    geom = WKTReader().read(wkt)
    param = HashMap()
    param.put('geoRegion', geom)
    param.put('outputImageScaleInDb', False)

    dst = snappy.GPF.createProduct("Subset", param, p_in)

    snappy.ProductIO.writeProduct(dst, f_out, 'BEAM-DIMAP')

    return dst


if __name__ == "__main__":

    parser = optparse.OptionParser(formatter=optparse.TitledHelpFormatter(), usage=globals()['__doc__'])

    parser.add_option('--list_in', action='store', dest='list_in', type='str', help='S1 list of input files')
    parser.add_option('--shp_in', action='store', dest='shp_in', type='str', help='Shape file of a region of interest (Optional)')
    parser.add_option('--dir_out', action='store', dest='dir_out', type='str', help='Output directory')

    (options, args) = parser.parse_args()

    list_in0 = options.list_in
    if os.path.isfile(list_in0) is False:
        print('File %s does not exists')
        sys.exit(0)
    list_in = list_in0.split('/')[-1]
    dir_in = '/'.join(list_in0.split('/')[:-1]) + '/'

    shp_crop = options.shp_in
    if shp_crop == None:
        shp_crop = ''

    dir_out = options.dir_out

    process = psutil.Process(os.getpid())
    print('Process memory (b):')
    print(process.memory_info().rss)

    timeBefore = time.clock()

    f = open(list_in0)
    lst = f.read().split('\n')

    lst_sub = []
    prod_set = []

    for f_in in lst:

        if os.path.isfile(f_in) is False:
            continue
        p_in = snappy.ProductIO.readProduct(f_in)

        print(p_in)
        print(list(p_in.getBandNames()))

        print('S1 processing has started')

        if np.logical_and(shp_crop != '', os.path.isfile(shp_crop)):
            timeBeforeSub = time.clock()
            print('Get subset')
            f_in = f_in.split('.')[0] + '_sub.dim'
            p_in = get_subset(p_in, shp_crop, f_in)
            lst_sub = np.append(lst_sub, f_in)
            prod_set.append(p_in)
            timeAfterSub = time.clock()
            print 'Subsetting lasted for (m): ', (timeAfterSub - timeBeforeSub)/60.
        else:
            print('Subset file does not exist or you want to process the whole scene')


    # define the stack parameters
    params = snappy.HashMap()
    params.put('resamplingType', None)
    params.put('initialOffsetMethod', 'Product Geolocation')
    params.put('extent', 'Master')

    # make the stack
    prod_stack = snappy.GPF.createProduct('CreateStack', params, prod_set)

    # prod_set = []
    # for f_in in lst_sub:
    #         prod_set.append(snappy.ProductIO.readProduct(f_in))

    timeBeforeSpeck = time.clock()
    print('Multi Temporal Speckle filtering')
    f_in = f_in.split('.')[0] + 'target_speck.dim'
    p_speck = mt_speckle(prod_stack, dir_out + f_in)
    timeAfterSpeck = time.clock()
    print 'Multi Temporal speckle filtering lasted for (m): ', (timeAfterSpeck - timeBeforeSpeck)/60.

    timeAfter = time.clock()
    print 'it lasted for (h): ', (timeAfter - timeBefore)/(60.*60.)

    process = psutil.Process(os.getpid())
    print('Process memory (b):')
    print(process.memory_info().rss)

    print("All Done!")