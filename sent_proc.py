"""
SNAPPY based processing of Sentinel-1 data

Author: Maxim Chernetskiy, 2019

SNAPPY must be installed!

Example of usage:
python sent_proc.py --file_in /Users/max/satellite/sentinel-1/data/S1A_IW_GRDH_1SDV_20191014T062219_20191014T062244_029451_0359A3_1F3B.zip\
--shp_in /Users/max/satellite/cervest/shp/cropmap2017_wgs84.shp\
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

# param = snappy.HashMap()
HashMap = snappy.jpy.get_type('java.util.HashMap')
# print(param)
# param = HashMap()


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

    return p_terr


def terrain_correction(p_in, f_out='s1a_terr.dim'):
    """
    S1 SRTM based Terrain correction

    :param p_in: input snap product
    :param f_out:
    :return: Corrected snap product
    """
    parameters = snappy.HashMap()
    p_terr = snappy.GPF.createProduct('Terrain-Correction', parameters, p_in)
    p_out = snappy.ProductIO.writeProduct(p_terr, f_out, "BEAM-DIMAP")

    return p_terr


def calibration(p_in, f_out='s1a_cal.dim'):
    """
    Calibration to Db

    :param p_in: input snap product
    :param str f_out: output file
    :return: Calibrated snap product
    """
    parameters = snappy.HashMap()
    p_cal = snappy.GPF.createProduct('Calibration', parameters, p_in)
    p_out = snappy.ProductIO.writeProduct(p_cal, f_out, "BEAM-DIMAP")

    return p_cal


def multi_look(p_in, f_out='s1a_mult.dim'):
    """
    Multi-look processing

    :param p_in: input snap product
    :param str f_out: output file
    :return: Corrected snap product
    """
    parameters = snappy.HashMap()
    # parameters.put('grSquarePixel', True)
    # parameters.put('nRgLooks', rgLooks)
    # parameters.put('nAzLooks', azLooks)
    # parameters.put('outputIntensity', False)
    # parameters.put('sourceBands', source)

    p_mult = snappy.GPF.createProduct('Multilook', parameters, p_in)
    p_out = snappy.ProductIO.writeProduct(p_mult, f_out, "BEAM-DIMAP")

    return p_mult


def apply_orbit(p_in, f_out='s1a_orbit.dim'):
    """
    Extract and apply an orbital file

    :param p_in: input snap product
    :param str f_out: output file
    :return: Snap product
    """
    param = HashMap()
    param.put("Orbit State Vectors", "Sentinel Precise (Auto Download)")
    param.put("Polynomial Degree", 3)
    p_orbit = snappy.GPF.createProduct("Apply-Orbit-File", param, p_in)
    p_out = snappy.ProductIO.writeProduct(p_orbit, f_out, "BEAM-DIMAP")
    return p_orbit


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

    parser.add_option('--file_in', action='store', dest='f_in', type='str', help='S1 level 1 input file')
    parser.add_option('--shp_in', action='store', dest='shp_in', type='str', help='Shape file of a region of interest (Optional)')
    parser.add_option('--dir_out', action='store', dest='dir_out', type='str', help='Output directory')

    (options, args) = parser.parse_args()

    f_in0 = options.f_in
    if os.path.isfile(f_in0) is False:
        print('File %s does not exists')
        sys.exit(0)
    f_in = f_in0.split('/')[-1]
    # dir_in = f_in0.split('/')[0]
    dir_in = '/'.join(f_in0.split('/')[:-1]) + '/'

    shp_crop = options.shp_in
    if shp_crop == None:
        shp_crop = ''

    dir_out = options.dir_out

    # /Users/max/satellite/sentinel-1/data/S1A_IW_GRDH_1SDV_20191014T062219_20191014T062244_029451_0359A3_1F3B.zip

    # shp_crop = '/Users/max/satellite/cervest/shp/cropmap2017_wgs84.shp'
    # dir_in = '/Users/max/satellite/sentinel-1/data/'

    # f_in = 'S1A_IW_GRDH_1SDV_20191014T062219_20191014T062244_029451_0359A3_1F3B.zip'
    # dir_out = '/Volumes/lacie_data/satellite/Sentinel-1/cervest/proc_01/'

    process = psutil.Process(os.getpid())
    print('Process memory (b):')
    print(process.memory_info().rss)

    timeBefore = time.clock()

    p = snappy.ProductIO.readProduct(dir_in + f_in)

    print(p)
    print(list(p.getBandNames()))

    print('S1 processing has started')

    timeBeforeCal = time.clock()
    print('Calibration')
    f_cal = f_in.split('.')[0] + '_cal.dim'
    p_cal = calibration(p, dir_out + f_cal)
    timeAfterCal = time.clock()
    print 'Calibration lasted for (m): ', (timeAfterCal - timeBeforeCal)/60.

    if np.logical_and(shp_crop != '', os.path.isfile(shp_crop)):
        timeBeforeSub = time.clock()
        print('Get subset')
        f_sub = f_cal.split('.')[0] + '_sub.dim'
        p_sub = get_subset(p_cal, shp_crop, dir_out + f_sub)
        timeAfterSub = time.clock()
        print 'Subsetting lasted for (m): ', (timeAfterSub - timeBeforeSub)/60.
    else:
        print('Subset file does not exist or you want to process the whole scene')
        f_sub = f_cal

    timeBeforeOrb = time.clock()
    print('Extract orbit')
    f_orb = f_sub.split('.')[0] + '_orb.dim'
    p_orb = apply_orbit(p_sub, dir_out + f_orb)
    timeAfterOrb = time.clock()
    print 'Applying orbit file lasted for (m): ', (timeAfterOrb - timeBeforeOrb)/60.

    timeBeforeMult = time.clock()
    print('Multi look')
    f_mult = f_orb.split('.')[0] + '_mult.dim'
    p_mult = multi_look(p_orb, dir_out + f_mult)
    timeAfterMult = time.clock()
    print 'Multi-look processing lasted for (m): ', (timeAfterMult - timeBeforeMult)/60.

    timeBeforeTerr = time.clock()
    print('Terrain correction')
    f_terr = f_mult.split('.')[0] + '_terr.dim'
    p_terr = terrain_correction(p_mult, dir_out + f_terr)
    timeAfterTerr = time.clock()
    print 'Terrain correction lasted for (m): ', (timeAfterTerr - timeBeforeTerr)/60.

    timeBeforeSpeck = time.clock()
    print('Multi Temporal Speckle filtering')
    f_speck = f_terr.split('.')[0] + '_speck.dim'
    p_speck = mt_speckle(p_terr, dir_out + f_speck)
    timeAfterSpeck = time.clock()
    print 'Multi Temporal speckle filtering lasted for (m): ', (timeAfterSpeck - timeBeforeSpeck)/60.

    timeAfter = time.clock()
    print 'it lasted for (h): ', (timeAfter - timeBefore)/(60.*60.)

    process = psutil.Process(os.getpid())
    print('Process memory (b):')
    print(process.memory_info().rss)

    print("All Done!")
