"""
/***************************************************************************
CartoDB Plugin
A QGIS plugin

----------------------------------------------------------------------------
begin                : 2014-09-08
copyright            : (C) 2014 by Michael Salgado, Kudos Ltda.
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

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *

from osgeo import gdal
from osgeo import ogr

import os.path

from urllib import urlopen


class CartoDBPluginLayer(QgsVectorLayer):
    LAYER_TYPE = "cartodb"

    def __init__(self, tableName, cartoName, apiKey):
        # initialize plugin directory
        plugin_dir = os.path.dirname(os.path.abspath(__file__))

        # SQLite available?
        layerType = 'ogr'
        readOnly = True
        driverName = "SQLite"
        sqLiteDrv = ogr.GetDriverByName(driverName)
        databasePath = plugin_dir + '/db/database.sqlite'
        datasource = sqLiteDrv.Open(databasePath, True)
        layerName = tableName

        sql = 'SELECT * FROM ' + tableName
        cartoUrl = 'http://{}.cartodb.com/api/v2/sql?format=GeoJSON&q={}&api_key={}'.format(cartoName, sql, apiKey)
        response = urlopen(cartoUrl)
        path = response.read()
        dsGeoJSON = ogr.Open(path)
        if dsGeoJSON is not None:
            jsonLayer = dsGeoJSON.GetLayerByName('OGRGeoJSON')
            if jsonLayer is not None:
                newLyr = datasource.CopyLayer(jsonLayer, str(layerName), options=['FORMAT=SPATIALITE'])
                datasource.Destroy()

                if newLyr is not None:
                    QgsMessageLog.logMessage('New Layer created', 'CartoDB Plugin', QgsMessageLog.INFO)
                    uri = QgsDataSourceURI()
                    uri.setDatabase(databasePath)
                    uri.setDataSource('', layerName, 'geometry')
                    QgsMessageLog.logMessage('New Connection: ' + uri.uri(), 'CartoDB Plugin', QgsMessageLog.INFO)
                    path = uri.uri()
                    layerType = 'spatialite'
                    readOnly = False
                else:
                    QgsMessageLog.logMessage('Some error ocurred opening SQLite datasource', 'CartoDB Plugin', QgsMessageLog.WARNING)
            else:
                QgsMessageLog.logMessage('Some error ocurred opening GeoJSON layer', 'CartoDB Plugin', QgsMessageLog.WARNING)
        else:
            QgsMessageLog.logMessage('Some error ocurred opening GeoJSON datasource', 'CartoDB Plugin', QgsMessageLog.WARNING)

        if readOnly:
            QgsMessageLog.logMessage('CartoDB Layer is readonly mode', 'CartoDB Plugin', QgsMessageLog.WARNING)

        QgsVectorLayer.__init__(self, path, layerName, layerType)
        self.databasePath = databasePath
        self.layerType = layerType
        self.readOnly = readOnly
        self.layerName = layerName
