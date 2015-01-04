ClipToHemisphere
================

Plugin for the QGIS Processing framework to clip vector layers to one hemisphere

When projecting data to the orthographic projection, features that cross the horizon can lead to unsightly artefacts.
By clipping the data to the hemisphere that will be visible in the orthographic projection, these artifacts can be
avoided. This plugin for the QGIS Processing framework takes a vector layer and a latitude and longitude for the
center of the hemisphere and clips the vector layer accordingly.
