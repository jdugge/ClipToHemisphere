# -*- coding: utf-8 -*-

"""
***************************************************************************
    __init__.py
    ---------------------
    Date                 : December 2014
    Copyright            : (C) 2014 by Juernjakob Dugge
    Email                : juernjakob at gmail dot com
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

__author__ = 'Juernjakob Dugge'
__date__ = 'December 2016'
__copyright__ = '(C) 2016, Juernjakob Dugge'

import os
import sys
import inspect

from qgis.core import *
import PyQt4.QtCore

from processing.core.Processing import Processing
from processing.core.AlgorithmProvider import AlgorithmProvider
from processing.core.GeoAlgorithm import GeoAlgorithm
try:
    from processing.parameters.ParameterVector import ParameterVector
    from processing.parameters.ParameterNumber import ParameterNumber
    from processing.outputs.OutputVector import OutputVector
except ImportError:
    from processing.core.parameters import ParameterVector, ParameterNumber
    from processing.core.outputs import OutputVector
from processing.core.ProcessingConfig import Setting, ProcessingConfig
from processing.tools import dataobjects, vector

import processing

import numpy as np
import cmath

cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]

if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)


def classFactory(iface):
    return ClipToHemisphereProviderPlugin()


class ClipToHemisphereProviderPlugin:

    def __init__(self):
        self.provider = ClipToHemisphereAlgorithmProvider()

    def initGui(self):
        Processing.addProvider(self.provider, updateList=True)

    def unload(self):
        Processing.removeProvider(self.provider)


class ClipToHemisphereAlgorithmProvider(AlgorithmProvider):

    def __init__(self):
        AlgorithmProvider.__init__(self)

        self.alglist = [ClipToHemisphereAlgorithm()]
        for alg in self.alglist:
            alg.provider = self

    def initializeSettings(self):
        AlgorithmProvider.initializeSettings(self)

    def unload(self):
        AlgorithmProvider.unload(self)

    def getName(self):
        return 'Clip to Hemisphere'

    def getDescription(self):
        return 'Clip to Hemisphere'

    def getIcon(self):
        return AlgorithmProvider.getIcon(self)

    def _loadAlgorithms(self):
        self.algs = self.alglist


class ClipToHemisphereAlgorithm(GeoAlgorithm):
    OUTPUT_LAYER = 'OUTPUT_LAYER'
    INPUT_LAYER = 'INPUT_LAYER'
    CENTER_LATITUDE = 'CENTER_LATITUDE'
    CENTER_LONGITUDE = 'CENTER_LONGITUDE'
    SEGMENTS = 'SEGMENTS'

    def defineCharacteristics(self):
        """Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
        self.name = 'Clip a vector layer to the hemisphere centred on a ' \
            'user specified point'
        self.group = 'Clip to Hemisphere'

        self.addParameter(ParameterVector(self.INPUT_LAYER, 'Input layer',
                          [ParameterVector.VECTOR_TYPE_ANY], False))
        self.addParameter(ParameterNumber(self.CENTER_LATITUDE, 'Latitude of '
            'center of hemisphere',
                          default=0.0))
        self.addParameter(ParameterNumber(self.CENTER_LONGITUDE, 'Longitude '
            'of center of hemisphere',
                          default=0.0))
        self.addParameter(ParameterNumber(self.SEGMENTS, 'Number of segments '
            'for approximating the hemisphere',
                          default=500))
        self.addOutput(OutputVector(self.OUTPUT_LAYER,
                       'Output clipped to hemisphere'))

    def processAlgorithm(self, progress):
        """Here is where the processing itself takes place."""

        inputFilename = self.getParameterValue(self.INPUT_LAYER)
        centerLatitude = float(self.getParameterValue(self.CENTER_LATITUDE))
        centerLongitude = float(self.getParameterValue(self.CENTER_LONGITUDE))
        segments = self.getParameterValue(self.SEGMENTS)
        output = self.getOutputValue(self.OUTPUT_LAYER)

        earthRadius = 6371000

        settings = PyQt4.QtCore.QSettings()
        inputLayer = dataobjects.getObjectFromUri(inputFilename)
        provider = inputLayer.dataProvider()
        sourceCrs = provider.crs()

        # It would be nice to give the output layer a nicer name than "Output
        # clipped to hemisphere", but I don't know how to do that. The code
        # below doesn't work
        #output.name = inputLayer.name() + u' clipped to hemisphere ' + \
        #    str(centerLatitude) + u', ' + str(centerLongitude)

        targetProjString = "+proj=ortho +lat_0=" + str(centerLatitude) + \
            " +lon_0=" + str(centerLongitude) + \
            " +x_0=0 +y_0=0 +a=" + str(earthRadius) + \
            " +b=" + str(earthRadius) + \
            " +units=m +no_defs"
        targetCrs = QgsCoordinateReferenceSystem()
        targetCrs.createFromProj4(targetProjString)

        transformTargetToSrc = QgsCoordinateTransform(targetCrs,
            sourceCrs).transform
        transformSrcToTarget = QgsCoordinateTransform(sourceCrs,
            targetCrs).transform

        clipLayer = QgsVectorLayer("MultiPolygon", "clipLayer", "memory")
        pr = clipLayer.dataProvider()

        # Handle edge cases:
        # Hemisphere centered on the equator
        if centerLatitude == 0:
            # Hemisphere centered on the equator and including the antimeridian
            if abs(centerLongitude) > 90:
                edgeEast = -180 - np.sign(centerLongitude) * \
                        (180 - abs(centerLongitude)) + 90
                edgeWest = 180 - np.sign(centerLongitude) * \
                        (180 - abs(centerLongitude)) - 90
                circlePoints = [[
                    [QgsPoint(-180, latitude) for
                        latitude in np.linspace(90, -90, segments / 8)] +
                    [QgsPoint(longitude, -90) for longitude in
                        np.linspace(-180, edgeEast, segments / 8)] +
                    [QgsPoint(edgeEast, latitude) for latitude in
                        np.linspace(-90, 90, segments / 8)] +
                    [QgsPoint(longitude, 90) for longitude in
                        np.linspace(edgeEast, -180, segments / 8)]
                    ],
                    [
                    [QgsPoint(edgeWest, latitude) for latitude in
                        np.linspace(90, -90, segments / 8)] +
                    [QgsPoint(longitude, -90) for longitude in
                        np.linspace(edgeWest, 180, segments / 8)] +
                    [QgsPoint(180, latitude) for
                        latitude in np.linspace(-90, 90, segments / 8)] +
                    [QgsPoint(longitude, 90) for longitude in
                        np.linspace(180, edgeWest, segments / 8)]
                    ]]
            # Hemisphere centered on the equator not including the antimeridian
            else:
                edgeWest = centerLongitude - 90
                edgeEast = centerLongitude + 90
                circlePoints = [[
                    [QgsPoint(edgeWest, latitude) for latitude in
                        np.linspace(90, -90, segments / 4)] +
                    [QgsPoint(longitude, -90) for longitude in
                        np.linspace(edgeWest, edgeEast, segments / 4)] +
                    [QgsPoint(edgeEast, latitude) for
                        latitude in np.linspace(-90, 90, segments / 4)] +
                    [QgsPoint(longitude, 90) for longitude in
                        np.linspace(edgeEast, edgeWest, segments / 4)]
                    ]]
        # Hemisphere centered on one of the poles
        elif abs(centerLatitude) == 90:
            circlePoints = [[
                [QgsPoint(-180, latitude) for latitude in
                        np.linspace(45 + 0.5 * centerLatitude,
                                   -45 + 0.5 * centerLatitude,
                                   segments / 4)] +
                [QgsPoint(longitude, -45 + 0.5 * centerLatitude)
                        for longitude in
                        np.linspace(-180, 180, segments / 4)] +
                [QgsPoint(180, latitude) for latitude in
                        np.linspace(-45 + 0.5 * centerLatitude,
                                     45 + 0.5 * centerLatitude,
                                   segments / 4)] +
                [QgsPoint(longitude, 45 + 0.5 * centerLatitude) for longitude in
                        np.linspace(180, -180, segments / 4)]
                ]]
        # All other hemispheres
        else:
            # Create a circle in the orthographic projection, convert the
            # circle coordinates to the source CRS
            angles = np.linspace(0, 2 * np.pi, segments, endpoint=False)
            circlePoints = np.array([
                transformTargetToSrc(
                    QgsPoint(np.cos(angle) * earthRadius * 0.9999,
                             np.sin(angle) * earthRadius * 0.9999)
                            ) for angle in angles
            ])

            # Sort the projected circle coordinates from west to east
            sortIdx = np.argsort(circlePoints[:, 0])
            circlePoints = circlePoints[sortIdx, :]
            circlePoints = [[[QgsPoint(point[0], point[1])
                for point in circlePoints]]]

            # Find the circle point in the orthographic projection that lies
            # on the antimeridian by linearly interpolating the angles of the
            # first and last coordinates
            startGap = 180 + circlePoints[0][0][0][0]
            endGap = 180 - circlePoints[0][0][-1][0]
            totalGap = startGap + endGap
            startCoordinates = transformSrcToTarget(circlePoints[0][0][0])
            endCoordinates = transformSrcToTarget(circlePoints[0][0][-1])
            startAngle = np.arctan2(startCoordinates[0], startCoordinates[1])
            endAngle = np.arctan2(endCoordinates[0], endCoordinates[1])
            antimeridianAngle = cmath.phase(
                endGap / totalGap * cmath.rect(1, startAngle) +
                startGap / totalGap * cmath.rect(1, endAngle))
            antimeridianPoint = transformTargetToSrc(QgsPoint(
                np.sin(antimeridianAngle) * earthRadius * 0.9999,
                np.cos(antimeridianAngle) * earthRadius * 0.9999
                ))

            # Close the polygon
            circlePoints[0][0].extend(
                [QgsPoint(180, latitude) for latitude in
                        np.linspace(antimeridianPoint[1],
                            np.sign(centerLatitude) * 90, segments / 4)] +
                [QgsPoint(-180, latitude) for latitude in
                        np.linspace(np.sign(centerLatitude) * 90,
                            antimeridianPoint[1], segments / 4)]
                )

        # Create the feature and add it to the layer
        circle = QgsFeature()
        circle.setGeometry(QgsGeometry.fromMultiPolygon(circlePoints))

        pr.addFeatures([circle])
        pr.updateExtents()

        # We need to add the clipping layer to the layer list in order to be
        # able to use them with processing.runalg()
        clipLayerReg = QgsMapLayerRegistry.instance().addMapLayer(clipLayer)

        if hasattr(processing.algs.qgis.Intersection.Intersection, "IGNORE_NULL"):
            # Syntax changed on 2016-10-20: https://github.com/qgis/QGIS/commit/5ae0e784e78993870c416ff499616a5147803c2c
            processing.runalg("qgis:intersection", inputLayer, clipLayerReg, False, output)
        else:
            processing.runalg("qgis:intersection", inputLayer, clipLayerReg, output)

        QgsMapLayerRegistry.instance().removeMapLayer(clipLayerReg.id())