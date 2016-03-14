"""
/***************************************************************************
CartoDB Plugin

----------------------------------------------------------------------------
begin                : 2014-09-08
copyright            : (C) 2015 by Michael Salgado, Kudos Ltda.
email                : michaelsalgado@gkudos.com, info@gkudos.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import Qt, QFile, QFileInfo, QVariant

from qgis.core import QgsVectorFileWriter, QgsVectorLayer, QgsField

import os
import random
import tempfile
import zipfile
import unicodedata

def stripAccents(text):
    """Strips accent to text"""
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

def randomColor(mix=(255, 255, 255)):
    """Generate Random Color"""
    red = random.randrange(0, 256)
    blue = random.randrange(0, 256)
    green = random.randrange(0, 256)

    r, g, b = mix
    red = (red + r)/2
    green = (green + g)/2
    blue = (blue + b)/2

    return (red, blue, green)

def getSize(layer):
    """Get layer size on disk"""
    is_zip_file = False
    file_path = layer.dataProvider().dataSourceUri()
    if file_path.find('|') != -1:
        file_path = file_path[0:file_path.find('|')]

    if file_path.startswith('/vsizip/'):
        file_path = file_path.replace('/vsizip/', '')
        is_zip_file = True

    _file = QFile(file_path)
    file_info = QFileInfo(_file)

    dirname = file_info.dir().absolutePath()
    filename = file_info.completeBaseName()

    size = 0
    if layer.storageType() == 'ESRI Shapefile' and not is_zip_file:
        for suffix in ['.shp', '.dbf', '.prj', '.shx']:
            _file = QFile(os.path.join(dirname, filename + suffix))
            file_info = QFileInfo(_file)
            size = size + file_info.size()
    elif layer.storageType() in ['GPX', 'GeoJSON', 'LIBKML'] or is_zip_file:
        size = size + file_info.size()

    return size

def zipLayer(layer):
    """Compress layer to zip file"""
    file_path = layer.dataProvider().dataSourceUri()
    if file_path.find('|') != -1:
        file_path = file_path[0:file_path.find('|')]

    if file_path.startswith('/vsizip/'):
        file_path = file_path.replace('/vsizip/', '')
        if layer.storageType() in ['ESRI Shapefile', 'GPX', 'GeoJSON', 'LIBKML']:
            return file_path
    _file = QFile(file_path)
    file_info = QFileInfo(_file)

    dirname = file_info.dir().absolutePath()
    filename = stripAccents(file_info.completeBaseName())
    layername = stripAccents(layer.name())

    tempdir = checkTempDir()

    zip_path = os.path.join(tempdir, layername + '.zip')
    zip_file = zipfile.ZipFile(zip_path, 'w')


    if layer.storageType() == 'ESRI Shapefile':
        for suffix in ['.shp', '.dbf', '.prj', '.shx']:
            if os.path.exists(os.path.join(dirname, filename + suffix)):
                zip_file.write(os.path.join(dirname, filename + suffix), layername + suffix, zipfile.ZIP_DEFLATED)
    elif layer.storageType() == 'GeoJSON':
        zip_file.write(file_path, layername + '.geojson', zipfile.ZIP_DEFLATED)
    elif layer.storageType() == 'GPX':
        zip_file.write(file_path, layername + '.gpx', zipfile.ZIP_DEFLATED)
    elif layer.storageType() == 'LIBKML':
        zip_file.write(file_path, layername + '.kml', zipfile.ZIP_DEFLATED)
    else:
        geo_json_name = os.path.join(tempfile.tempdir, layername)
        error = QgsVectorFileWriter.writeAsVectorFormat(layer, geo_json_name, "utf-8", None, "GeoJSON")
        if error == QgsVectorFileWriter.NoError:
            zip_file.write(geo_json_name + '.geojson', layername + '.geojson', zipfile.ZIP_DEFLATED)
    zip_file.close()
    return zip_path

def checkTempDir():
    """Check temporar dir"""
    tempdir = tempfile.tempdir
    if tempdir is None:
        tempdir = tempfile.mkdtemp()
    return tempdir

def checkCartoDBId(layer, convert=False):
    """Check if layer has cartodb_id field"""
    new_layer = layer

    if convert and layer.fieldNameIndex('cartodb_id') == -1:
        checkTempDir()
        temp = tempfile.NamedTemporaryFile()
        error = QgsVectorFileWriter.writeAsVectorFormat(layer, temp.name, 'utf-8', None, 'ESRI Shapefile')
        if error == QgsVectorFileWriter.NoError:
            new_layer = QgsVectorLayer(temp.name + '.shp', layer.name(), 'ogr')
            new_layer.dataProvider().addAttributes([QgsField('cartodb_id', QVariant.Int)])
            new_layer.updateFields()
            features = new_layer.getFeatures()
            i = 1
            for feature in features:
                fid = feature.id()
                aid = new_layer.fieldNameIndex('cartodb_id')
                attrs = {aid: i}
                new_layer.dataProvider().changeAttributeValues({fid : attrs})
                i = i + 1
                new_layer.updateFeature(feature)
    return new_layer

def getLineJoin(lyr):
    """Get line join from symbol layer"""
    join_style = 'miter'
    if lyr.penJoinStyle() == Qt.BevelJoin:
        join_style = 'bevel'
    elif lyr.penJoinStyle() == Qt.RoundJoin:
        join_style = 'round'
    return join_style

def getLineDasharray(lineStyle, lineWidth):
    """Get line dash array from line style"""
    line_dash_array = '0'
    if lineStyle == Qt.DashLine:
        line_dash_array = '5,5'
    elif lineStyle == Qt.DotLine:
        line_dash_array = '{},{}'.format(lineWidth, lineWidth*5)
    elif lineStyle == Qt.DashDotLine:
        line_dash_array = '{},{},{},{}'.format(lineWidth*10, lineWidth*10, lineWidth, lineWidth*10)
    elif lineStyle == Qt.DashDotDotLine:
        line_dash_array = '{},{},{},{},{},{}'.format(lineWidth*5, lineWidth*5, lineWidth, lineWidth*5, lineWidth, lineWidth*5)
    return line_dash_array
