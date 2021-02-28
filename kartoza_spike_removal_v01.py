import os
import sys
import datetime
import time
import ntpath
import statistics

from osgeo import gdal
from osgeo import ogr

POLYGONS = "D:/Kartoza/qgis/spiky-polygons.gpkg"
OUTPUT = "D:/Kartoza/output/"


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
# Stops the script if any errors is found
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

    data = ogr.GetDriverByName("GPKG").CreateDataSource(OUTPUT + "copy.gpkg")
    lyr = data.CreateLayer('polygon2d', geom_type=ogr.wkbPolygon)

    data_p = ogr.GetDriverByName("GPKG").CreateDataSource(OUTPUT + "points.gpkg")
    lyr_p = data_p.CreateLayer('point', geom_type=ogr.wkbPoint)

    data_f = ogr.GetDriverByName("GPKG").CreateDataSource(OUTPUT + "final.gpkg")
    lyr_f = data_f.CreateLayer('polygon2d', geom_type=ogr.wkbPolygon)

    point_geom = ogr.Geometry(ogr.wkbPoint)
    for feat in vector_layers:
        geom = feat.GetGeometryRef()
        ring = geom.GetGeometryRef(0)

        geom_buf = geom.Buffer(-10 * 0.00001)
        new_feat = ogr.Feature(lyr.GetLayerDefn())
        new_feat.SetGeometry(ogr.CreateGeometryFromWkt(str(geom_buf)))
        lyr.CreateFeature(new_feat)

        cnt = ring.GetPointCount()
        write_message("Vertice cnt: " + str(cnt))
        
        #list_distances = []
        #for i in range(0, cnt):
        #    point = ring.GetPoint(i)
        #    point_geom.AddPoint(point[0], point[1])

        #    new_point = ogr.Feature(lyr_p.GetLayerDefn())
        #    new_point.SetGeometry(ogr.CreateGeometryFromWkt(str(point_geom)))

        #    distance = (geom_buf.Distance(point_geom))/0.00001
        #    list_distances.append(distance)
        
        #std_dev = statistics.stdev(list_distances)
        #write_message("std_dev: " + str(std_dev))

        ring_spike_removed = ogr.Geometry(ogr.wkbLinearRing)

        for i in range(0, cnt):
            point = ring.GetPoint(i)
            point_geom.AddPoint(point[0], point[1])

            new_point = ogr.Feature(lyr_p.GetLayerDefn())
            new_point.SetGeometry(ogr.CreateGeometryFromWkt(str(point_geom)))

            distance = (geom_buf.Distance(point_geom))/0.00001

            if distance < 20:
                lyr_p.CreateFeature(new_point)
                ring_spike_removed.AddPoint(point[0], point[1])
            else:
                write_message("Spike polygon vertice found (" + str(distance) + "m from polygon.)")

        poly_spike_removed = ogr.Geometry(ogr.wkbPolygon)
        poly_spike_removed.AddGeometry(ring_spike_removed)

        new_poly = ogr.Feature(lyr_f.GetLayerDefn())
        new_poly.SetGeometry(ogr.CreateGeometryFromWkt(str(poly_spike_removed)))

        lyr_f.CreateFeature(new_poly)


def main():
    stop_script = perform_checks()
    if not stop_script:
        write_message("=======================Spike removal=======================")

        read_vector_file(POLYGONS)

        write_message("=======================Spike removal successfull=======================")
    else:
        write_message("=======================Script not executed=======================")


main()
