# -*- coding: utf-8 -*-

"""
***************************************************************************
    __init__.py
    ---------------------
    Date                 : September 2020
    Copyright            : (C) 2020 by Juernjakob Dugge
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
__date__ = 'September 2020'
__copyright__ = '(C) 2020, Juernjakob Dugge'

import os

from qgis.core import (
    QgsApplication,
    QgsProcessing,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterNumber,
    QgsProcessingProvider,
    QgsCoordinateReferenceSystem,
    QgsVectorLayer,
    QgsFeature,
    QgsGeometry,
    QgsCoordinateTransform,
    QgsPointXY,
    QgsProject,
    QgsProcessingParameterVectorDestination
)

from processing.algs.qgis.QgisAlgorithm import QgisAlgorithm
import processing
import numpy as np
import cmath

pluginPath = os.path.split(os.path.split(os.path.dirname(__file__))[0])[0]


class ClipToHemisphereProvider(QgsProcessingProvider):
    
    def __init__(self):
        QgsProcessingProvider.__init__(self)
    
    def unload(self):
        pass
    
    def loadAlgorithms(self):
        self.addAlgorithm(ClipToHemisphereAlgorithm())
    
    def id(self):
        """
        Returns the unique provider id, used for identifying the provider. This
        string should be a unique, short, character only string, eg "qgis" or
        "gdal". This string should not be localised.
        """
        return 'Clip to hemisphere'
    
    def name(self):
        """
        Returns the provider name, which is used to describe the provider
        within the GUI.

        This string should be short (e.g. "Lastools") and localised.
        """
        return self.tr('Clip to hemisphere')
    
    def longName(self):
        """
        Returns the a longer version of the provider name, which can include
        extra details such as version numbers. E.g. "Lastools LIDAR tools
        (version 2.2.1)". This string should be localised. The default
        implementation returns the same string as name().
        """
        return self.name()


class ClipToHemispherePlugin(object):
    def __init__(self):
        self.provider = None
    
    def initProcessing(self):
        self.provider = ClipToHemisphereProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)
    
    def initGui(self):
        self.initProcessing()
    
    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)


class ClipToHemisphereAlgorithm(QgisAlgorithm):
    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'
    CENTER_LATITUDE = 'CENTER_LATITUDE'
    CENTER_LONGITUDE = 'CENTER_LONGITUDE'
    SEGMENTS = 'SEGMENTS'
    
    def __init__(self):
        super().__init__()
    
    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Input layer'),
                [QgsProcessing.TypeVectorAnyGeometry]
            )
        )
        
        self.addParameter(
            QgsProcessingParameterVectorDestination(
                self.OUTPUT,
                self.tr('Output layer')
            )
        )
        
        param = QgsProcessingParameterNumber(
            self.CENTER_LATITUDE,
            self.tr('Center latitude'),
            type=QgsProcessingParameterNumber.Double,
            minValue=-90,
            maxValue=90
        )
        param.setMetadata({'widget_wrapper':
                               {'decimals': 1}
                           })
        self.addParameter(param)
        
        param = QgsProcessingParameterNumber(
            self.CENTER_LONGITUDE,
            self.tr('Center longitude'),
            type=QgsProcessingParameterNumber.Double,
            minValue=-180,
            maxValue=180
        )
        param.setMetadata({'widget_wrapper':
                               {'decimals': 1}
                           })
        self.addParameter(param)
        
        self.addParameter(QgsProcessingParameterNumber(
            self.SEGMENTS,
            self.tr('Segments'),
            defaultValue=720,
            minValue=3,
            type=QgsProcessingParameterNumber.Integer
        ))
    
    def name(self):
        return 'cliptohemisphere'
    
    def displayName(self):
        return self.tr('Clip to hemisphere')
    
    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.INPUT, context)
        sourceCrs = source.sourceCrs()
        centerLatitude = self.parameterAsDouble(parameters,
                                                self.CENTER_LATITUDE, context)
        centerLongitude = self.parameterAsDouble(parameters,
                                                 self.CENTER_LONGITUDE, context)
        segments = self.parameterAsInt(parameters, self.SEGMENTS, context)
        
        earthRadius = 6371000
        targetProjString = "+proj=ortho +lat_0=" + str(centerLatitude) + \
                           " +lon_0=" + str(centerLongitude) + \
                           " +x_0=0 +y_0=0 +a=" + str(earthRadius) + \
                           " +b=" + str(earthRadius) + \
                           " +units=m +no_defs"
        targetCrs = QgsCoordinateReferenceSystem()
        targetCrs.createFromProj(targetProjString)
        
        transformTargetToSrc = QgsCoordinateTransform(targetCrs,
                                                      sourceCrs,
                                                      QgsProject.instance()).transform
        transformSrcToTarget = QgsCoordinateTransform(sourceCrs,
                                                      targetCrs,
                                                      QgsProject.instance()).transform
        clipLayer = QgsVectorLayer("MultiPolygon", "clipLayer", "memory")
        pr = clipLayer.dataProvider()
        
        # Handle edge cases:
        # Hemisphere centered on the equator
        if centerLatitude == 0:
            # Hemisphere centered on the equator and including the antimeridian
            if abs(centerLongitude) >= 90:
                edgeEast = -180 - np.sign(centerLongitude) * \
                           (180 - abs(centerLongitude)) + 90
                edgeWest = 180 - np.sign(centerLongitude) * \
                           (180 - abs(centerLongitude)) - 90
                circlePoints = [[
                    [QgsPointXY(-180.01, latitude) for
                     latitude in np.linspace(90, -90, segments // 8)] +
                    [QgsPointXY(longitude, -90) for longitude in
                     np.linspace(-180, edgeEast, segments // 8)] +
                    [QgsPointXY(edgeEast, latitude) for latitude in
                     np.linspace(-90, 90, segments // 8)] +
                    [QgsPointXY(longitude, 90) for longitude in
                     np.linspace(edgeEast, -180, segments // 8)]
                ],
                    [
                        [QgsPointXY(edgeWest, latitude) for latitude in
                         np.linspace(90, -90, segments // 8)] +
                        [QgsPointXY(longitude, -90) for longitude in
                         np.linspace(edgeWest, 180, segments // 8)] +
                        [QgsPointXY(180.01, latitude) for
                         latitude in np.linspace(-90, 90, segments // 8)] +
                        [QgsPointXY(longitude, 90) for longitude in
                         np.linspace(180, edgeWest, segments // 8)]
                    ]]
            # Hemisphere centered on the equator not including the antimeridian
            else:
                edgeWest = centerLongitude - 90
                edgeEast = centerLongitude + 90
                circlePoints = [[
                    [QgsPointXY(edgeWest, latitude) for latitude in
                     np.linspace(90, -90, segments // 4)] +
                    [QgsPointXY(longitude, -90) for longitude in
                     np.linspace(edgeWest, edgeEast, segments // 4)] +
                    [QgsPointXY(edgeEast, latitude) for
                     latitude in np.linspace(-90, 90, segments // 4)] +
                    [QgsPointXY(longitude, 90) for longitude in
                     np.linspace(edgeEast, edgeWest, segments // 4)]
                ]]
        # Hemisphere centered on one of the poles
        elif abs(centerLatitude) == 90:
            circlePoints = [[
                [QgsPointXY(-180.01, latitude) for latitude in
                 np.linspace(45 + 0.5 * centerLatitude,
                             -45 + 0.5 * centerLatitude,
                             segments // 4)] +
                [QgsPointXY(longitude, -45 + 0.5 * centerLatitude)
                 for longitude in
                 np.linspace(-180, 180, segments // 4)] +
                [QgsPointXY(180.01, latitude) for latitude in
                 np.linspace(-45 + 0.5 * centerLatitude,
                             45 + 0.5 * centerLatitude,
                             segments // 4)] +
                [QgsPointXY(longitude, 45 + 0.5 * centerLatitude) for longitude
                 in
                 np.linspace(180, -180, segments // 4)]
            ]]
        # All other hemispheres
        else:
            # Create a circle in the orthographic projection, convert the
            # circle coordinates to the source CRS
            angles = np.linspace(0, 2 * np.pi, segments, endpoint=False)
            circlePoints = np.array([
                transformTargetToSrc(
                    QgsPointXY(np.cos(angle) * earthRadius * 0.9999,
                               np.sin(angle) * earthRadius * 0.9999)
                ) for angle in angles
            ])
            
            # Sort the projected circle coordinates from west to east
            sortIdx = np.argsort(circlePoints[:, 0])
            circlePoints = circlePoints[sortIdx, :]
            circlePoints = [[[QgsPointXY(point[0], point[1])
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
            antimeridianPoint = transformTargetToSrc(QgsPointXY(
                np.sin(antimeridianAngle) * earthRadius * 0.9999,
                np.cos(antimeridianAngle) * earthRadius * 0.9999
            ))
            
            # Close the polygon
            circlePoints[0][0].extend(
                [QgsPointXY(180.01, latitude) for latitude in
                 np.linspace(antimeridianPoint[1],
                             np.sign(centerLatitude) * 90, segments // 4)] +
                [QgsPointXY(-180.01, latitude) for latitude in
                 np.linspace(np.sign(centerLatitude) * 90,
                             antimeridianPoint[1], segments // 4)]
            )
        
        # Create the feature and add it to the layer
        circle = QgsFeature()
        circle.setGeometry(QgsGeometry.fromMultiPolygonXY(circlePoints))
        
        pr.addFeatures([circle])
        
        result = processing.run('native:intersection', {
            'INPUT': parameters['INPUT'],
            'OVERLAY': clipLayer,
            'OUTPUT': parameters['OUTPUT']
        }, is_child_algorithm=True, context=context, feedback=feedback)
        
        return {self.OUTPUT: result['OUTPUT']}
