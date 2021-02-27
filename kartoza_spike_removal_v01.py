import os
import sys
import datetime
import time
import shapely
import ntpath

from shapely.geometry import Polygon
from osgeo import gdal
from osgeo import ogr

#import fiona

POLYGONS = "D:/Kartoza/qgis/spiky-polygons.gpkg"


# Checks the extension of a given file
# file_name: name of file with extension
# extensions: list of allowed extensions
def check_extension(file_name, extensions):
    length = len(file_name)
    lowercase = file_name.lower()

    # If the string length is less than 3 character, it has no extension
    if length < 3:
        return False
    else:
        for extension in extensions:
            found = lowercase.find(extension, length - 4, length)

            # Extension found, return true
            if found != -1:
                return True
    # Extension not found, return false
    return False


# Writes a message to the console with a timestamp
# message: prints this message to the console
def write_message(message):
    time_sec = time.time()
    timestamp = datetime.datetime.fromtimestamp(time_sec).strftime('%Y-%m-%d %H:%M:%S')

    message = "[" + str(timestamp) + "] " + str(message)

    print(message)


# Checks the input data for errors
def perform_checks():
    stop_script = False

    if not os.path.exists(POLYGONS):
        write_message("ERROR: The polygons vector file does not exist: " + str(POLYGONS))
        stop_script = True

    if os.path.exists(POLYGONS):
        if not check_extension(POLYGONS, ["gpkg"]):
            write_message("ERROR: Incorrect file type: " + str(POLYGONS))

    return stop_script


def read_vector_file(vector_file):
    filename = ntpath.basename(vector_file)
    write_message("Vector file: " + filename)
    
    file = ogr.Open(POLYGONS)
    vector_layers = file.GetLayer(0)
    layer_cnt = len(vector_layers)
    spatial_ref = vector_layers.GetSpatialRef()
    layer_extent = vector_layers.GetExtent()

    write_message("Feature count: " + str(layer_cnt))

    return vector_layers


def main():
    stop_script = perform_checks()
    if not stop_script:
        write_message("=======================Spike removal=======================")

        read_vector_file(POLYGONS)




        write_message("=======================Spike removal successfull=======================")
    else:
        write_message("=======================Script not executed=======================")


main()
