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

from QgisCartoDB.cartodb import CartoDBAPIKey, CartoDBException


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

        if not self.readOnly:
            self.initConnections()
            self._uneditableFields()

    def initConnections(self):
        QgsMessageLog.logMessage('Init connections for: ' + self.layerName, 'CartoDB Plugin', QgsMessageLog.INFO)
        self.editingStarted.connect(self._editingStarted)
        self.attributeAdded[int].connect(self._attributeAdded)
        self.featureDeleted.connect(self._featureDeleted)
        self.beforeCommitChanges.connect(self._beforeCommitChanges)

    def _uneditableFields(self):
        fieldMap = self.dataProvider().fieldNameMap()
        self.setFieldEditable(fieldMap['cartodb_id'], False)

    def _editingStarted(self):
        QgsMessageLog.logMessage('Editing started', 'CartoDB Plugin', QgsMessageLog.INFO)
        self._uneditableFields()

    def _attributeAdded(self, idx):
        QgsMessageLog.logMessage('Attribute added at ' + str(idx) + ' index', 'CartoDB Plugin', QgsMessageLog.INFO)
        fields = self.pendingFields()
        field = fields.field(idx)
        if field is not None:
            QgsMessageLog.logMessage('Field is: ' + field.name(), 'CartoDB Plugin', QgsMessageLog.INFO)
            self.deleteAttribute(idx)

    def _featureDeleted(self, featureID):
        request = QgsFeatureRequest().setFilterFid(featureID)
        try:
            feature = self.getFeatures(request).next()
        except StopIteration:
            QgsMessageLog.logMessage('Can\'t get feature with fid: ' + str(featureID), 'CartoDB Plugin', QgsMessageLog.WARNING)

    def _beforeCommitChanges(self):
        QgsMessageLog.logMessage('Before commit', 'CartoDB Plugin', QgsMessageLog.INFO)
        self._uneditableFields()
        editBuffer = self.editBuffer()
        changedAttributeValues = editBuffer.changedAttributeValues()
        provider = self.dataProvider()
        for featureID, v in changedAttributeValues.iteritems():
            QgsMessageLog.logMessage('Update attributes for feature ID: ' + str(featureID), 'CartoDB Plugin', QgsMessageLog.INFO)
            sql = "UPDATE " + self.cartoTable + " SET "
            request = QgsFeatureRequest().setFilterFid(featureID)
            try:
                feature = self.getFeatures(request).next()
                addComma = False
                for fieldID, val in v.iteritems():
                    if(addComma):
                        sql = sql + ", "

                    fieldValue = unicode(val)
                    if fieldValue != 'NULL':
                        fieldValue = "'" + fieldValue + "'"

                    fName = provider.fields().field(fieldID).name()
                    if fName != 'cartodb_id':
                        sql = sql + fName + " = " + fieldValue
                        addComma = True
                    else:
                        # TODO Rollback changes.
                        pass

                sql = sql + " WHERE cartodb_id = " + unicode(feature['cartodb_id'])
                sql = sql.encode('utf-8')

                self._updateSQL(sql, 'Some error ocurred getting tables')
            except StopIteration:
                QgsMessageLog.logMessage('Can\'t get feature with fid: ' + str(featureID), 'CartoDB Plugin', QgsMessageLog.WARNING)

        changedGeometries = editBuffer.changedGeometries()
        for featureID, geom in changedGeometries.iteritems():
            QgsMessageLog.logMessage('Update geometry for feature ID: ' + str(featureID), 'CartoDB Plugin', QgsMessageLog.INFO)
            QgsMessageLog.logMessage('Geom WKT: ' + geom.exportToWkt(), 'CartoDB Plugin', QgsMessageLog.INFO)
            request = QgsFeatureRequest().setFilterFid(featureID)
            try:
                sql = "UPDATE " + self.cartoTable + " SET the_geom = "
                feature = self.getFeatures(request).next()
                sql = sql + "ST_GeomFromText('" + geom.exportToWkt() + "', ST_SRID(the_geom)) WHERE cartodb_id = " + unicode(feature['cartodb_id'])
                sql = sql.encode('utf-8')

                self._updateSQL(sql, 'Some error ocurred updating geometry')
            except StopIteration:
                QgsMessageLog.logMessage('Can\'t get feature with fid: ' + str(featureID), 'CartoDB Plugin', QgsMessageLog.WARNING)

        deletedFeatureIds = editBuffer.deletedFeatureIds()
        for featureID in deletedFeatureIds:
            QgsMessageLog.logMessage('Delete feature with feature ID: ' + str(featureID), 'CartoDB Plugin', QgsMessageLog.INFO)
            request = QgsFeatureRequest().setFilterFid(featureID)
            try:
                feature = self.getFeatures(request).next()
                sql = "DELETE FROM " + self.cartoTable + " WHERE cartodb_id = " + unicode(feature['cartodb_id'])
                self._updateSQL(sql, 'Some error ocurred deleting feature')
            except StopIteration:
                QgsMessageLog.logMessage('Can\'t get feature with fid: ' + str(featureID), 'CartoDB Plugin', QgsMessageLog.WARNING)

    def _updateSQL(self, sql, errorMsg):
        QgsMessageLog.logMessage('SQL: ' + unicode(sql), 'CartoDB Plugin', QgsMessageLog.INFO)
        cl = CartoDBAPIKey(self._apiKey, self.user)
        try:
            res = cl.sql(sql, True, True)
            QgsMessageLog.logMessage('Result: ' + str(res), 'CartoDB Plugin', QgsMessageLog.INFO)
            return res
        except CartoDBException as e:
            QgsMessageLog.logMessage(errorMsg + ' - ' + str(e), 'CartoDB Plugin', QgsMessageLog.CRITICAL)
            return e
