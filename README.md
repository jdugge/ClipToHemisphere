ClipToHemisphere
================

Plugin for the QGIS Processing framework to clip vector layers to one hemisphere

When projecting data to the orthographic projection, features that cross the horizon can lead to unsightly artefacts.
By clipping the data to the hemisphere that will be visible in the orthographic projection, these artifacts can be
avoided. This plugin for the QGIS Processing framework takes a vector layer and a latitude and longitude for the
center of the hemisphere and clips the vector layer accordingly.



Usage
-----

1. Load the vector layer you want to project to an orthographic projection. Note that the vector layer must be in WGS 84, so reproject the layer to the EPSG:4326 projection if necessary. Setting the project CRS to EPSG:4326 with on-the-fly projection is not sufficient, the layer itself has to be in the right projection.
2. In the Processing Toolbox, run the `Clip to Hemisphere | Clip to Hemisphere | Clip a vector layer to the hemisphere centred on a user specified point` algorithm.
3. In the Parameters tab of the algorithm, choose the latitude and longitude of the central point of the desired orthographic projection in degrees. The algorithm assumes the central point to be given in WGS 84 coordinates.
4. Either choose a file name for the clipped output, or leave the field empty to create a temporary memory layer.
5. Choose run. The clipped layer will be added to the project.
6. If you haven't done so already, create a custom CRS for the orthographic projection using the `Settings | Custom CRS` menu. The projection string should be similar to `+proj=ortho +lat_0=20 +lon_0=30 +x_0=0 +y_0=0 +a=6370997 +b=6370997 +units=m +no_defs`, replacing the values for `lat_0` and `lon_0` with the central point of the desired projection.
7. Disable the `Simplify geometry` feature for the clipped layer in the `Rendering` tab of the Layer properties.
8. In the `CRS` tab of the Project properties, choose the newly created custom CRS and check the `Enable 'on the fly' reprojection`.
 
