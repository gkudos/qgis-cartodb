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

    def __init__(self, iface, tableName, cartoName, apiKey):
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
                i = 1
                while datasource.GetLayerByName(str(layerName)) is not None:
                    layerName = layerName + str(i)
                    i = i + 1
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

        super(QgsVectorLayer, self).__init__(path, layerName, layerType)
        self.databasePath = databasePath
        self.layerType = layerType
        self.readOnly = readOnly
        self.layerName = layerName
        self.cartoTable = tableName
        self.user = cartoName
        self._apiKey = apiKey
        self.iface = iface

        self.initConnections()

    def initConnections(self):
        QgsMessageLog.logMessage('Init connections for: ' + self.layerName, 'CartoDB Plugin', QgsMessageLog.INFO)
        self.editingStarted.connect(self._editingStarted)
        self.attributeAdded[int].connect(self._attributeAdded)
        self.beforeCommitChanges.connect(self._beforeCommitChanges)

    def _editingStarted(self):
        QgsMessageLog.logMessage('Editing started', 'CartoDB Plugin', QgsMessageLog.INFO)

    def _attributeAdded(self, idx):
        QgsMessageLog.logMessage('Attribute added at ' + str(idx) + ' index', 'CartoDB Plugin', QgsMessageLog.INFO)
        fields = self.pendingFields()
        field = fields.field(idx)
        if field is not None:
            QgsMessageLog.logMessage('Field is: ' + field.name(), 'CartoDB Plugin', QgsMessageLog.INFO)
            self.deleteAttribute(idx)

    def _beforeCommitChanges(self):
        QgsMessageLog.logMessage('Before commit', 'CartoDB Plugin', QgsMessageLog.INFO)
        editBuffer = self.editBuffer()
        changedAttributeValues = editBuffer.changedAttributeValues()
        for fieldID, v in changedAttributeValues.iteritems():
            QgsMessageLog.logMessage('Field ID: ' + str(fieldID), 'CartoDB Plugin', QgsMessageLog.INFO)
            QgsMessageLog.logMessage('Val: ' + str(v), 'CartoDB Plugin', QgsMessageLog.INFO)
