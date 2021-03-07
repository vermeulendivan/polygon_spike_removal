import os
import datetime
import time
import ntpath

from osgeo import ogr


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
def perform_checks(polygons, out_folder, out_name, distance, overwrite):
    stop_script = False

    if not os.path.exists(polygons):
        write_message("ERROR: The polygons vector file does not exist: " + str(polygons))
        stop_script = True

    if os.path.exists(polygons):
        if not check_extension(polygons, ["gpkg"]):
            write_message("ERROR: Incorrect file type: " + str(polygons))
            stop_script = True

    if not os.path.exists(out_folder):
        write_message("ERROR: Output directory not found: " + str(out_folder))
        stop_script = True
    else:
        s_len = len(out_folder)
        s_char = out_folder[s_len - 1]

        if s_char != "/":
            out_folder = out_folder + "\\"

    if not check_extension(out_name, ["gpkg"]):
        write_message("ERROR: Output file name has to be geopackage format (*.gpkg).")
        stop_script = True

    output_file = out_folder + out_name
    if os.path.exists(output_file):
        if overwrite:
            os.remove(output_file)
        else:
            write_message("ERROR: Output file already exists: " + str(output_file))
            stop_script = True

    if distance <= 0:
        write_message("ERROR: Buffer distance needs to be greater than zero: " + str(distance))
        stop_script = True

    return stop_script, out_folder


# Checks if the temp folder exists, and then creates it if not
def create_folder(folder):
    # If the temp folder does not exist within the provided folder, create it
    if not os.path.exists(folder):
        os.makedirs(folder)

    return folder


def get_parameters(list_parameters):
    vec_file = list_parameters[0]
    out_fol = list_parameters[1]
    out_name = list_parameters[2]
    buf_dis = list_parameters[3]
    z_fac = list_parameters[4]
    overwrite = list_parameters[5]

    return vec_file, out_fol, out_name, buf_dis, z_fac, overwrite


# Performs polygon spike removal
def polygon_spike_removal(list_para):
    vector_file, output_folder, output_name, buf_distance, z_factor, overwrite = get_parameters(list_para)

    stop_script, output_folder = perform_checks(vector_file, output_folder, output_name, buf_distance, overwrite)

    if stop_script:
        write_message("Errors found in input parameters.")
        return

    filename = ntpath.basename(vector_file)
    write_message("Vector file: " + filename)

    file = ogr.Open(vector_file)
    vector_layers = file.GetLayer(0)
    layer_cnt = len(vector_layers)

    # Checks if the vector layer consist of features/polygons
    if layer_cnt > 0:
        write_message("Polygon count: " + str(layer_cnt))

        temp_dir = output_folder + "temp/"
        create_folder(temp_dir)

        # Buffering
        data = ogr.GetDriverByName("GPKG").CreateDataSource(temp_dir + "buffer.gpkg")
        lyr = data.CreateLayer('polygon', geom_type=ogr.wkbPolygon)

        # Points/vertices
        data_p = ogr.GetDriverByName("GPKG").CreateDataSource(temp_dir + "vertices.gpkg")
        lyr_p = data_p.CreateLayer('point', geom_type=ogr.wkbPoint)

        # Temp
        lyr_f = None

        output_file = output_folder + output_name
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
                    geom_buf = geom.Buffer(-1 * buf_distance * z_factor)
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
                        distance = (geom_buf.Distance(point_geom)) / z_factor

                        # If the point is a large distance from the negative buffer polygons, its likely a spike
                        if distance < buf_distance * 10:  # Adds the point if its not a spike
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
                        geom_buf = geom.Buffer(-1 * buf_distance * z_factor)
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
                            distance = (geom_buf.Distance(point_geom)) / z_factor

                            # If the point is a large distance from the negative buffer polygons, its likely a spike
                            if distance < buf_distance * 10:  # Adds the point if its not a spike
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
