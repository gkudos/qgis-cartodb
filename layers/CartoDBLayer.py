"""
/***************************************************************************
CartoDB Plugin
A QGIS plugin

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

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *

from osgeo import gdal
from osgeo import ogr

import os.path

from urllib import urlopen

from PyQt4.QtCore import pyqtSlot

from qgis.core import *

import QgisCartoDB.CartoDBPlugin
from QgisCartoDB.cartodb import CartoDBAPIKey, CartoDBException, CartoDBApi
from QgisCartoDB.utils import CartoDBPluginWorker


class CartoDBLayer(QgsVectorLayer):
    LAYER_CNAME_PROPERTY = 'user'
    LAYER_TNAME_PROPERTY = 'tableName'
    LAYER_SQL_PROPERTY = 'cartoSQL'

    def __init__(self, iface, tableName, user, apiKey, owner=None, sql=None, geoJSON=None,
                 filterByExtent=False, spatiaLite=None, readonly=False, multiuser=False, isSQL=False):
        # SQLite available?
        self.iface = iface
        self.user = user
        self._apiKey = apiKey
        self.layerType = 'ogr'
        self.owner = owner
        self.isSQL = isSQL
        self.multiuser = multiuser
        driverName = "SQLite"
        sqLiteDrv = ogr.GetDriverByName(driverName)
        self.databasePath = QgisCartoDB.CartoDBPlugin.PLUGIN_DIR + '/db/database.sqlite'
        self.datasource = sqLiteDrv.Open(self.databasePath, True)
        self.layerName = tableName
        self.cartoTable = tableName

        self.forceReadOnly = False or readonly

        if sql is None:
            sql = 'SELECT * FROM ' + self._schema() + self.cartoTable
            if filterByExtent:
                extent = self.iface.mapCanvas().extent()
                sql = sql + " WHERE ST_Intersects(ST_GeometryFromText('{}', 4326), the_geom)".format(extent.asWktPolygon())
        else:
            self.forceReadOnly = True

        self._loadData(sql, geoJSON, spatiaLite)

    def initConnections(self):
        QgsMessageLog.logMessage('Init connections for: ' + self.layerName, 'CartoDB Plugin', QgsMessageLog.INFO)
        self.editingStarted.connect(self._editingStarted)
        self.attributeAdded[int].connect(self._attributeAdded)
        self.beforeCommitChanges.connect(self._beforeCommitChanges)

    def _loadData(self, sql, geoJSON=None, spatiaLite=None):
        readonly = True
        if spatiaLite is None:
            if geoJSON is None:
                cartoUrl = 'http://{}.cartodb.com/api/v2/sql?format=GeoJSON&q={}&api_key={}'.format(self.user, sql, self._apiKey)
                response = urlopen(cartoUrl)
                geoJSON = response.read()
            else:
                QgsMessageLog.logMessage('Already GeoJSON', 'CartoDB Plugin', QgsMessageLog.INFO)

            dsGeoJSON = ogr.Open(geoJSON)
            path = None
            if dsGeoJSON is not None:
                jsonLayer = dsGeoJSON.GetLayerByName('OGRGeoJSON')

                if jsonLayer is not None:
                    """ TODO Convert to numbers numeric fields when it's null.
                    layerDefinition = jsonLayer.GetLayerDefn()
                    QgsMessageLog.logMessage("Layer def: " + str(layerDefinition), 'CartoDB Plugin', QgsMessageLog.INFO)
                    for i in range(layerDefinition.GetFieldCount()):
                        fieldName = layerDefinition.GetFieldDefn(i).GetName()
                        fieldTypeCode = layerDefinition.GetFieldDefn(i).GetType()
                        fieldType = layerDefinition.GetFieldDefn(i).GetFieldTypeName(fieldTypeCode)
                        fieldWidth = layerDefinition.GetFieldDefn(i).GetWidth()
                        GetPrecision = layerDefinition.GetFieldDefn(i).GetPrecision()
                        if fieldName == 'number':
                            layerDefinition.GetFieldDefn(i).SetType(2)
                            jsonLayer.StartTransaction()
                            jsonLayer.AlterFieldDefn(i, layerDefinition.GetFieldDefn(i), ogr.ALTER_TYPE_FLAG)
                            jsonLayer.CommitTransaction()

                        fieldTypeCode = layerDefinition.GetFieldDefn(i).GetType()
                        fieldType = layerDefinition.GetFieldDefn(i).GetFieldTypeName(fieldTypeCode)

                        QgsMessageLog.logMessage(fieldName + " - " + fieldType + " " + str(fieldWidth) + " " + str(GetPrecision) + " code: " + str(fieldTypeCode), 'CartoDB Plugin', QgsMessageLog.INFO)
                    """

                    i = 1
                    tempLayerName = self.layerName
                    while self.datasource.GetLayerByName(str(tempLayerName)) is not None:
                        tempLayerName = self.layerName + str(i)
                        i = i + 1
                    self.layerName = tempLayerName
                    newLyr = self.datasource.CopyLayer(jsonLayer, str(self.layerName), options=['FORMAT=SPATIALITE'])

                    if newLyr is not None:
                        QgsMessageLog.logMessage('New Layer created', 'CartoDB Plugin', QgsMessageLog.INFO)
                        uri = QgsDataSourceURI()
                        uri.setDatabase(self.databasePath)
                        uri.setDataSource('', self.layerName, 'geometry')
                        QgsMessageLog.logMessage('New Connection: ' + uri.uri(), 'CartoDB Plugin', QgsMessageLog.INFO)
                        path = uri.uri()
                        self.layerType = 'spatialite'
                        readonly = False
                    else:
                        QgsMessageLog.logMessage('Some error ocurred opening SQLite datasource', 'CartoDB Plugin', QgsMessageLog.WARNING)
                    self.datasource.Destroy()
                else:
                    QgsMessageLog.logMessage('Some error ocurred opening GeoJSON layer', 'CartoDB Plugin', QgsMessageLog.WARNING)
            else:
                QgsMessageLog.logMessage('Some error ocurred opening GeoJSON datasource', 'CartoDB Plugin', QgsMessageLog.WARNING)
        else:
            QgsMessageLog.logMessage('New Layer created', 'CartoDB Plugin', QgsMessageLog.INFO)
            QgsMessageLog.logMessage('New Connection: ' + spatiaLite, 'CartoDB Plugin', QgsMessageLog.INFO)
            path = spatiaLite
            self.layerType = 'ogr'
            readonly = False

        if self.forceReadOnly:
            readonly = True
        if readonly:
            QgsMessageLog.logMessage('CartoDB Layer is readonly mode', 'CartoDB Plugin', QgsMessageLog.WARNING)

        if path is None and geoJSON is not None:
            super(QgsVectorLayer, self).__init__(geoJSON, self.layerName, self.layerType)
        else:
            super(QgsVectorLayer, self).__init__(path, self.layerName, self.layerType)
        self.readonly = readonly
        self._deletedFeatures = []

        if not self.readonly:
            self.initConnections()
            self._uneditableFields()

        self.setReadOnly(self.readonly)

        self.setCustomProperty(CartoDBLayer.LAYER_CNAME_PROPERTY, self.user)
        self.setCustomProperty(CartoDBLayer.LAYER_TNAME_PROPERTY, self.fullTableName())

        self.sql = sql
        if self.forceReadOnly and sql is not None:
            self.setCustomProperty(CartoDBLayer.LAYER_SQL_PROPERTY, sql)

    def _uneditableFields(self):
        schema = 'public' if not self.multiuser else self.owner
        sql = "SELECT table_name, column_name, column_default, is_nullable, data_type, table_schema \
                FROM information_schema.columns \
                WHERE data_type != 'USER-DEFINED' AND table_schema = '" + schema + "' AND table_name = '" + self.cartoTable + "' \
                ORDER BY ordinal_position"

        cl = CartoDBAPIKey(self._apiKey, self.user)
        try:
            res = cl.sql(sql, True, True)
            for pgField in res['rows']:
                if pgField['data_type'] == 'timestamp with time zone':
                    self.setEditorWidgetV2(self.fieldNameIndex(pgField['column_name']), 'DateTime')
                    self.setEditorWidgetV2Config(self.fieldNameIndex(pgField['column_name']), {
                                                 u'display_format': u'yyyy-MM-dd hh:mm:ss',
                                                 u'field_format': u'yyyy-MM-dd hh:mm:ss',
                                                 u'calendar_popup': True})
                elif pgField['data_type'] == 'boolean':
                    self.setEditorWidgetV2(self.fieldNameIndex(pgField['column_name']), 'CheckBox')
                    self.setEditorWidgetV2Config(self.fieldNameIndex(pgField['column_name']), {
                                                 u'CheckedState': u'true',
                                                 u'UncheckedState': u'false'})
        except CartoDBException as e:
            QgsMessageLog.logMessage(errorMsg + ' - ' + str(e), 'CartoDB Plugin', QgsMessageLog.CRITICAL)

        self.setFieldEditable(self.fieldNameIndex('cartodb_id'), False)
        self.setEditorWidgetV2(self.fieldNameIndex('cartodb_id'), 'Hidden')
        self.setFieldEditable(self.fieldNameIndex('updated_at'), False)
        self.setEditorWidgetV2(self.fieldNameIndex('updated_at'), 'Hidden')
        self.setFieldEditable(self.fieldNameIndex('created_at'), False)
        self.setEditorWidgetV2(self.fieldNameIndex('created_at'), 'Hidden')
        self.setFieldEditable(self.fieldNameIndex('OGC_FID'), False)
        self.setFieldEditable(self.fieldNameIndex('GEOMETRY'), False)

    def _editingStarted(self):
        self._uneditableFields()

    def _attributeAdded(self, idx):
        QgsMessageLog.logMessage('Attribute added at ' + str(idx) + ' index', 'CartoDB Plugin', QgsMessageLog.INFO)
        fields = self.pendingFields()
        field = fields.field(idx)
        if field is not None:
            QgsMessageLog.logMessage('Field is: ' + field.name(), 'CartoDB Plugin', QgsMessageLog.INFO)
            self.editBuffer().deleteAttribute(idx)

    def _beforeCommitChanges(self):
        QgsMessageLog.logMessage('Before commit', 'CartoDB Plugin', QgsMessageLog.INFO)
        self._uneditableFields()
        editBuffer = self.editBuffer()

        self._updateAttributes(editBuffer.changedAttributeValues())
        self._updateGeometries(editBuffer.changedGeometries())
        self._addFeatures(editBuffer.addedFeatures())
        self._deleteFeatures(editBuffer.deletedFeatureIds())

    def _updateAttributes(self, changedAttributeValues):
        provider = self.dataProvider()
        for featureID, v in changedAttributeValues.iteritems():
            QgsMessageLog.logMessage('Update attributes for feature ID: ' + str(featureID), 'CartoDB Plugin', QgsMessageLog.INFO)
            sql = "UPDATE " + self._schema() + self.cartoTable + " SET "
            request = QgsFeatureRequest().setFilterFid(featureID)
            try:
                feature = self.getFeatures(request).next()
                addComma = False
                for fieldID, val in v.iteritems():
                    if addComma:
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

                res = self._updateSQL(sql, 'Some error ocurred getting tables')
                if isinstance(res, dict) and res['total_rows'] == 1:
                    self.iface.messageBar().pushMessage('Info',
                                                        'Data for cartodb_id ' + str(feature['cartodb_id']) + ' from ' +
                                                        str(self.cartoTable) + ' was updated from CartoDB servers',
                                                        level=self.iface.messageBar().INFO, duration=10)
            except StopIteration:
                self.iface.messageBar().pushMessage("Warning", 'Can\'t get feature with fid ' + str(featureID),
                                                    level=self.iface.messageBar().WARNING, duration=10)

    def _updateGeometries(self, changedGeometries):
        for featureID, geom in changedGeometries.iteritems():
            QgsMessageLog.logMessage('Update geometry for feature ID: ' + str(featureID), 'CartoDB Plugin', QgsMessageLog.INFO)
            request = QgsFeatureRequest().setFilterFid(featureID)
            try:
                sql = "UPDATE " + self._schema() + self.cartoTable + " SET the_geom = "
                feature = self.getFeatures(request).next()
                sql = sql + "ST_GeomFromText('" + geom.exportToWkt() + "', ST_SRID(the_geom)) WHERE cartodb_id = " + unicode(feature['cartodb_id'])
                sql = sql.encode('utf-8')

                res = self._updateSQL(sql, 'Some error ocurred updating geometry')
                if isinstance(res, dict) and res['total_rows'] == 1:
                    self.iface.messageBar().pushMessage('Info',
                                                        'Geometry for cartodb_id ' + str(feature['cartodb_id']) +
                                                        ' was updated from ' + str(self.cartoTable) + ' at CartoDB servers',
                                                        level=self.iface.messageBar().INFO, duration=10)

            except StopIteration:
                self.iface.messageBar().pushMessage('Warning', 'Can\'t get feature with fid ' + str(featureID),
                                                    level=self.iface.messageBar().WARNING, duration=10)

    def _addFeatures(self, addedFeatures):
        provider = self.dataProvider()
        for featureID, feature in addedFeatures.iteritems():
            QgsMessageLog.logMessage('Add feature with feature ID: ' + str(featureID), 'CartoDB Plugin', QgsMessageLog.INFO)
            sql = "INSERT INTO " + self._schema() + self.cartoTable + " ("
            addComma = False
            for field in feature.fields():
                if unicode(feature[field.name()]) == 'NULL' or feature[field.name()] is None:
                    continue
                if addComma:
                    sql = sql + ", "
                sql = sql + field.name()
                addComma = True
            if addComma:
                sql = sql + ", "
            sql = sql + "the_geom) VALUES ("
            addComma = False
            for field in feature.fields():
                if unicode(feature[field.name()]) == 'NULL' or feature[field.name()] is None:
                    continue
                if addComma:
                    sql = sql + ", "
                sql = sql + "'" + unicode(feature[field.name()]) + "'"
                addComma = True
            if addComma:
                sql = sql + ", "
            sql = sql + "ST_GeomFromText('" + feature.geometry().exportToWkt() + "', 4326)) RETURNING cartodb_id, created_at, updated_at"
            sql = sql.encode('utf-8')
            res = self._updateSQL(sql, 'Some error ocurred inserting feature')
            if isinstance(res, dict) and res['total_rows'] == 1:
                self.iface.messageBar().pushMessage('Info',
                                                    'Feature inserted at CartoDB servers',
                                                    level=self.iface.messageBar().INFO, duration=10)
                for f in ['cartodb_id', 'created_at', 'updated_at']:
                    self._updateNullableFields(featureID, f, res['rows'][0][f])

    def _updateNullableFields(self, featureID, fieldName, value):
        self.setFieldEditable(self.fieldNameIndex(fieldName), True)
        self.editBuffer().changeAttributeValue(featureID, self.fieldNameIndex(fieldName), value, None)
        self.setFieldEditable(self.fieldNameIndex(fieldName), False)

    def _deleteFeatures(self, deletedFeatureIds):
        provider = self.dataProvider()
        for featureID in deletedFeatureIds:
            QgsMessageLog.logMessage('Delete feature with feature ID: ' + str(featureID), 'CartoDB Plugin', QgsMessageLog.INFO)
            request = QgsFeatureRequest().setFilterFid(featureID)
            try:
                feature = provider.getFeatures(request).next()
                sql = "DELETE FROM " + self._schema() + self.cartoTable + " WHERE cartodb_id = " + unicode(feature['cartodb_id'])
                res = self._updateSQL(sql, 'Some error ocurred deleting feature')
                if isinstance(res, dict) and res['total_rows'] == 1:
                    self.iface.messageBar().pushMessage('Info',
                                                        'Feature with cartodb_id ' + str(feature['cartodb_id']) +
                                                        ' was deleted from ' + str(self.cartoTable) + ' at CartoDB servers',
                                                        level=self.iface.messageBar().INFO, duration=10)
            except StopIteration:
                self.iface.messageBar().pushMessage('Warning', 'Can\'t get feature from dataprovider with fid ' + str(featureID),
                                                    level=self.iface.messageBar().WARNING, duration=10)
        self._deletedFeatures = []

    def _updateSQL(self, sql, errorMsg):
        # QgsMessageLog.logMessage('SQL: ' + str(sql), 'CartoDB Plugin', QgsMessageLog.INFO)
        cl = CartoDBAPIKey(self._apiKey, self.user)
        try:
            res = cl.sql(sql, True, True)
            QgsMessageLog.logMessage('Result: ' + str(res), 'CartoDB Plugin', QgsMessageLog.INFO)
            return res
        except CartoDBException as e:
            QgsMessageLog.logMessage(errorMsg + ' - ' + str(e), 'CartoDB Plugin', QgsMessageLog.CRITICAL)
            self.iface.messageBar().pushMessage('Error!!', errorMsg, level=self.iface.messageBar().CRITICAL, duration=10)
            return e

    def _schema(self):
        schema = self.schema()
        return schema + ('.' if schema != '' else '')

    def schema(self):
        return '' if not self.multiuser else self.owner

    def tableName(self):
        return self.cartoTable

    def fullTableName(self):
        return self._schema() + self.cartoTable

    def readXml(self, node):
        res = QgsVectorLayer.readXml(node)
        qDebug('ReadXML: ' + str(node))
        return res

    def writeXml(self, node, doc):
        from QgisCartoDB.layers.CartoDBPluginLayer import CartoDBPluginLayer
        res = super(QgsVectorLayer, self).writeXml(node, doc)
        qDebug('WriteXML: ' + str(node))
        element = node.toElement()
        # write plugin layer type to project (essential to be read from project)
        element.setAttribute("type", "plugin")
        element.setAttribute("name", CartoDBPluginLayer.LAYER_TYPE)
        return res


class CartoDBLayerWorker(QObject):
    finished = pyqtSignal(CartoDBLayer)
    error = pyqtSignal(Exception, basestring)

    def __init__(self, iface, tableName, owner=None, dlg=None, sql=None, filterByExtent=False, readonly=False, multiuser=False):
        QObject.__init__(self)
        self.iface = iface
        self.owner = owner
        self.tableName = tableName
        self.readonly = readonly
        self.multiuser = multiuser
        self.dlg = dlg
        self.sql = sql
        self.filterByExtent = filterByExtent

    def load(self):
        worker = CartoDBPluginWorker(self, 'loadLayer')
        worker.error.connect(self.workerError)
        self.loop = QEventLoop()
        worker.finished.connect(self.workerFinished)
        worker.start()
        self.loop.exec_()

    @pyqtSlot(str)
    def _loadData(self, spatiaLite):
        layer = CartoDBLayer(self.iface, self.tableName, self.dlg.currentUser, self.dlg.currentApiKey,
                             self.owner, self.sql, spatiaLite=spatiaLite, readonly=self.readonly, multiuser=self.multiuser)
        self.finished.emit(layer)

    @pyqtSlot()
    def loadLayer(self):
        if self.sql is None:
            sql = 'SELECT * FROM ' + ((self.owner + '.') if self.owner != self.dlg.currentUser else '') + self.tableName
            if self.filterByExtent:
                extent = self.iface.mapCanvas().extent()
                sql = sql + " WHERE ST_Intersects(ST_GeometryFromText('{}', 4326), the_geom)".format(extent.asWktPolygon())
        else:
            sql = self.sql

        cartoDBApi = CartoDBApi(self.dlg.currentUser, self.dlg.currentApiKey)
        cartoDBApi.fetchContent.connect(self._loadData)
        cartoDBApi.download(sql)
        # cartoDBApi.getDataFromTable(sql, False)
        # geoJSON = self._loadData()

    def workerFinished(self, ret):
        QgsMessageLog.logMessage('Task finished:\n' + str(ret), 'CartoDB Plugin', QgsMessageLog.INFO)
        self.loop.exit()

    def workerError(self, e, exception_string):
        QgsMessageLog.logMessage('Worker thread raised an exception:\n'.format(exception_string), 'CartoDB Plugin', QgsMessageLog.CRITICAL)
