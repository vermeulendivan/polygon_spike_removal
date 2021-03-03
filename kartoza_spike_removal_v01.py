import os
import sys
import datetime
import time
import ntpath

from osgeo import ogr

POLYGONS = "D:/Kartoza/additional/multipolygon/test8.gpkg"
OUTPUT = "D:/Kartoza/output/"
OUTPUT_NAME = "test8_spikes_removed.gpkg"
DISTANCE = 10  # Distance in meters
Z_FACTOR = 0.00001  # 1 for projected, 0.00001 for geographic
OVERWRITE = True


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
            stop_script = True

    if not os.path.exists(OUTPUT):
        write_message("ERROR: Output directory not found: " + str(OUTPUT))
        stop_script = True

    if not check_extension(OUTPUT_NAME, ["gpkg"]):
        write_message("ERROR: Output file name has to be geopackage format (*.gpkg).")
        stop_script = True

    output_file = OUTPUT + OUTPUT_NAME
    if os.path.exists(output_file):
        if OVERWRITE:
            os.remove(output_file)
        else:
            write_message("ERROR: Output file already exists: " + str(output_file))
            stop_script = True

    return stop_script


# Checks if the temp folder exists, and then creates it if not
def create_folder(folder):
    # If the temp folder does not exist within the provided folder, create it
    if not os.path.exists(folder):
        os.makedirs(folder)

    return folder


# Performs polygon spike removal
def polygon_spike_removal(vector_file):
    filename = ntpath.basename(vector_file)
    write_message("Vector file: " + filename)

    file = ogr.Open(vector_file)
    vector_layers = file.GetLayer(0)
    layer_cnt = len(vector_layers)

    # Checks if the vector layer consist of features/polygons
    if layer_cnt > 0:
        write_message("Polygon count: " + str(layer_cnt))

        temp_dir = OUTPUT + "temp/"
        create_folder(temp_dir)

        # Buffering
        data = ogr.GetDriverByName("GPKG").CreateDataSource(temp_dir + "buffer.gpkg")
        lyr = data.CreateLayer('polygon', geom_type=ogr.wkbPolygon)

        # Points/vertices
        data_p = ogr.GetDriverByName("GPKG").CreateDataSource(temp_dir + "vertices.gpkg")
        lyr_p = data_p.CreateLayer('point', geom_type=ogr.wkbPoint)

        output_file = OUTPUT + OUTPUT_NAME
        # Performs spike removal on each polygon
        for feat in vector_layers:
            geom = feat.GetGeometryRef()
            # Spike removal can only be performed on a feature/polygon which has geometry/exists
            if geom is not None:
                # Geometry type: polygons, multipolygon, etc.
                input_geom_type = str(geom.GetGeometryName()).lower()
                write_message("Geometry type: " + str(input_geom_type))

                # Single-part polygons
                if input_geom_type == "polygon" or input_geom_type == "curvepolygon":
                    write_message("Singlepart polygons: " + input_geom_type)

                    # Creates the output file if it does not exist
                    if not os.path.exists(output_file):
                        # Final vector file with no spikes
                        data_f = ogr.GetDriverByName("GPKG").CreateDataSource(output_file)
                        if input_geom_type == "polygon":
                            lyr_f = data_f.CreateLayer(input_geom_type, geom_type=ogr.wkbPolygon)
                        else:
                            lyr_f = data_f.CreateLayer(input_geom_type, geom_type=ogr.wkbCurvePolygon)

                    ring = geom.GetGeometryRef(0)  # Polygon boundary

                    # Creates a negative buffer to remove slivers from outlier vertices
                    geom_buf = geom.Buffer(-1 * DISTANCE * Z_FACTOR)
                    new_feat = ogr.Feature(lyr.GetLayerDefn())
                    new_feat.SetGeometry(ogr.CreateGeometryFromWkt(str(geom_buf)))
                    lyr.CreateFeature(new_feat)
    
                    cnt = ring.GetPointCount()
                    write_message("Vertice count: " + str(cnt))

                    ring_spike_removed = ogr.Geometry(ogr.wkbLinearRing)
                    removed_point_count = 0
                    point_geom = ogr.Geometry(ogr.wkbPoint)
                    # Checks each of the polygon vertices
                    for i in range(0, cnt):
                        point = ring.GetPoint(i)
                        point_geom.AddPoint(point[0], point[1])
    
                        new_point = ogr.Feature(lyr_p.GetLayerDefn())
                        new_point.SetGeometry(ogr.CreateGeometryFromWkt(str(point_geom)))
    
                        # Converts the distance based on the Z_FACTOR variable
                        distance = (geom_buf.Distance(point_geom)) / Z_FACTOR
    
                        # If the point is a large distance from the negative buffer polygons, its likely a spike
                        if distance < DISTANCE * 10:  # Adds the point if its not a spike
                            lyr_p.CreateFeature(new_point)
                            ring_spike_removed.AddPoint(point[0], point[1])
                        else:  # Remove the point
                            write_message("Spike polygon vertice found (" + str(distance) + "m from polygon.)")
                            removed_point_count = removed_point_count + 1
    
                    write_message(str(removed_point_count) + " vertice(s) removed from the polygon.")
    
                    # Convert the remaining vertices to a polygon boundary
                    poly_spike_removed = ogr.Geometry(ogr.wkbPolygon)
                    poly_spike_removed.AddGeometry(ring_spike_removed)
    
                    # Creates the spike removed polygon and adds it to the vector file
                    new_poly = ogr.Feature(lyr_f.GetLayerDefn())
                    new_poly.SetGeometry(ogr.CreateGeometryFromWkt(str(poly_spike_removed)))
                    lyr_f.CreateFeature(new_poly)
                # Multi-part polygons
                elif input_geom_type == "multipolygon" or input_geom_type == "multisurface":
                    write_message("Multipart polygons: " + input_geom_type)

                    if not os.path.exists(output_file):
                        # Final vector file with no spikes
                        data_f = ogr.GetDriverByName("GPKG").CreateDataSource(output_file)
                        if input_geom_type == "multipolygon":
                            lyr_f = data_f.CreateLayer(input_geom_type, geom_type=ogr.wkbMultiPolygon)
                        else:
                            lyr_f = data_f.CreateLayer(input_geom_type, geom_type=ogr.wkbMultiSurface)

                    multi_poly_cnt = geom.GetGeometryCount()
                    write_message("Multi-polygon count: " + str(multi_poly_cnt))

                    if input_geom_type == "multipolygon":
                        multipoly_geom = ogr.Geometry(ogr.wkbMultiPolygon)
                    else:
                        multipoly_geom = ogr.Geometry(ogr.wkbMultiSurface)

                    # Loops through each polygon of the multipolygon feature
                    for multi_polygon in geom:
                        ring = multi_polygon.GetGeometryRef(0)  # Polygon boundary

                        # Creates a negative buffer to remove slivers from outlier vertices
                        geom_buf = geom.Buffer(-1 * DISTANCE * Z_FACTOR)
                        new_feat = ogr.Feature(lyr.GetLayerDefn())
                        new_feat.SetGeometry(ogr.CreateGeometryFromWkt(str(geom_buf)))
                        lyr.CreateFeature(new_feat)

                        cnt = ring.GetPointCount()
                        write_message("Vertice count: " + str(cnt))
    
                        ring_spike_removed = ogr.Geometry(ogr.wkbLinearRing)
                        removed_point_count = 0
                        point_geom = ogr.Geometry(ogr.wkbPoint)
                        # Checks each of the polygon vertices
                        for i in range(0, cnt):
                            point = ring.GetPoint(i)
                            point_geom.AddPoint(point[0], point[1])

                            new_point = ogr.Feature(lyr_p.GetLayerDefn())
                            new_point.SetGeometry(ogr.CreateGeometryFromWkt(str(point_geom)))

                            # Converts the distance based on the Z_FACTOR value
                            distance = (geom_buf.Distance(point_geom)) / Z_FACTOR

                            # If the point is a large distance from the negative buffer polygons, its likely a spike
                            if distance < DISTANCE * 10:  # Adds the point if its not a spike
                                lyr_p.CreateFeature(new_point)
                                ring_spike_removed.AddPoint(point[0], point[1])
                            else:  # Remove the point
                                write_message("Spike polygon vertice found (" + str(distance) + "m from polygon).")
                                removed_point_count = removed_point_count + 1

                        write_message(str(removed_point_count) + " vertice(s) removed from the polygon.")

                        # Convert the remaining vertices to a polygon boundary
                        poly_spike_removed = ogr.Geometry(ogr.wkbPolygon)
                        poly_spike_removed.AddGeometry(ring_spike_removed)

                        # Adds the spike removed polygon to the multi-polygon geometry
                        multipoly_geom.AddGeometry(poly_spike_removed)

                    # Creates the spike removed multi-polygon and adds it to the vector file
                    new_poly = ogr.Feature(lyr_f.GetLayerDefn())
                    new_poly.SetGeometry(ogr.CreateGeometryFromWkt(str(multipoly_geom)))
                    lyr_f.CreateFeature(new_poly)
                # The provided file is of incorrect geometry type
                else:
                    write_message("ERROR: Incorrect geometry type: " + str(input_geom_type) +
                                  ". Should be: polygon, multipolygon, curve polygon or multisurface polygon.")
                    break
            else:  # If the polygon has no geometry, it is skipped
                write_message("WARNING: Empty feature found. Will be skipped.")
    else:  # If the vector file is empty no spike removal can/will be performed
        write_message("Vector file (" + vector_file + ") has no features/polygons.")


# Main
def main():
    # Checks if there is any problems with the input data
    stop_script = perform_checks()

    if not stop_script:  # perform_checks found no issues
        write_message("=======================Spike removal=======================")

        # Performs spike removal on the provided polygon vector file
        polygon_spike_removal(POLYGONS)

        write_message("=======================Spike removal successful=======================")
    else:  # Error found by the perform_checks method
        write_message("=======================Script not executed=======================")


main()
