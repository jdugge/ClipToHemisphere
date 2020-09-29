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


def classFactory(iface):
    from .ClipToHemisphere import ClipToHemispherePlugin
    return ClipToHemispherePlugin()
