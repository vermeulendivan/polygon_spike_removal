# Polygon spike removal
Remove spikes from polygons, curvepolygons, multipolygons, and multisurface polygons. Code can be found on gitHub: [Polygon spike removal](https://github.com/vermeulendivan/polygon_spike_removal).

This tool removes outlier vertices of polygons firstly performing a negative buffer on the input feature.
This will remove the sliver of the polygon produced by the outlier vertice. All polygon vertices is converted to point format,
which is used to calculate the distance to the negative buffer polygon.
If the vertice is a large distance from the negative buffer polygon, it is an outlier, and therefore excluded from the output ring boundary.
If the point is in proximity of the polygon, it is added to the final ring boundary. Once each point has been checked, the ring boundary is converted to a polygon.
The polygon is then added to the output geopackage file. This is done with each polygon.

# Installation
The installation files can be found on gitHub ([installation files](https://github.com/vermeulendivan/polygon_spike_removal/tree/main/dist)).
Use "pip install kartoza_spike_removal_divan-1.0.tar.gz" or pip install "pip install kartoza_spike_removal_divan-1.0-py3-none-any.whl" if you want to install using the wheel.

# Uninstall
Run "pip uninstall "kartoza_spike_removal_Divan" to remove the module.

# Dependencies
Gdal ([gdal](https://gdal.org/)) is the only required module for this polygon spike removal utility.

# Parameters
The parameters should be provided as a list. These are the required parameters for the polygon_spike_removal method:
1. vector_file: String; Full directory of the input polygons. Format: geopackage (*.gpkg) (e.g. */data/spikes.gpkg);
2. output: String; Folder to which the output file will be written;
3. output_name: String; Name of the output file. Format: geopackage (*.gpkg) (e.g. spikes_removed.gpkg);
4. distance: Integer; Distance in meters (m) for the negative buffer. The negative buffer is used to remove slivers created from the spike vertice of the polygon;
    * Set the value high (e.g. 10 m) for large polygons;
    * Set the value low (e.g. 0.1 m) for smaller polygons.
5. z_factor: Integer; Projected coordinate system: 1; Geographic coordinate system: 0.00001;
6. overwrite: true, if output file exists it will be deleted. false, spike removal will not be performed if the output exists.

# Methods
* check_extension(file_name, extensions): Check if a file has the correct file extension;
* write_message(message): Prints a message to the console, but includes a timestamp;
* perform_checks(polygons, out_folder, out_name, distance, overwrite): Performs checks on the parameters to check for any issues. If an error is found, the script is stopped;
* create_folder(folder): Checks if the folder exists, if not, it is created;
* get_parameters(list_parameters): Gets the list of parameters and returns it as seperate variables;
* polygon_spike_removal(list_para): Performs the spike removal on the polygons.

# Flow diagram
The flow diagram is provided below. The blue steps is for single-part polygons (e.g. polygons and curvepolygons), whereas the green steps is for multi-part polygons, namely multipolygon or multisurface.
Black steps is general steps, such as error checking, get next feature, etc.

![flow_diagram](https://github.com/vermeulendivan/polygon_spike_removal/blob/main/flow_diagram.JPG?raw=true)

# Code example

>from spike_removal.kartoza_spike_removal_v01 import polygon_spike_removal\
POLYGONS = "D:\Kartoza\additional\multisurface\test7.gpkg"  # Input geopackage (*.gpkg) file\
OUTPUT = "D:\Kartoza\output\"  # Folder to which the output will be written\
OUTPUT_NAME = "test7_spikes_removed.gpkg"  # Output geopackage (*.gpkg) filename\
DISTANCE = 10  # Distance in meters\
Z_FACTOR = 0.00001  # 1 for projected, 0.00001 for geographic\
OVERWRITE = True  # Deletes the existing output file if it exists\
polygon_spike_removal([POLYGONS, OUTPUT, OUTPUT_NAME, DISTANCE, Z_FACTOR, OVERWRITE])

