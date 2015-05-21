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

from PyQt4.QtCore import pyqtSlot

from qgis.core import *

import QgisCartoDB.CartoDBPlugin
from QgisCartoDB.cartodb import CartoDBAPIKey, CartoDBException
from QgisCartoDB.utils import CartoDBPluginWorker


class CartoDBLayerWorker(QObject):
    cartoDBLoaded = pyqtSignal(QObject, QObject, int)
    error = pyqtSignal(Exception, basestring)

    def __init__(self, iface, tableName, dlg, i, sql=None):
        QObject.__init__(self)
        self.iface = iface
        self.tableName = tableName
        self.dlg = dlg
        self.i = i
        self.sql = sql

    def load(self):
        worker = CartoDBPluginWorker(self, 'loadLayer')
        worker.error.connect(self.workerError)
        loop = QEventLoop()
        worker.finished.connect(loop.exit)
        worker.start()
        loop.exec_()

    @pyqtSlot()
    def loadLayer(self):
        layer = CartoDBLayer(self.iface, self.tableName, self.dlg.currentUser, self.dlg.currentApiKey, self.sql)
        self.emitLoad(layer)

    def emitLoad(self, layer):
        # QgsMapLayerRegistry.instance().addMapLayer(layer)
        self.cartoDBLoaded.emit(layer, self.dlg, self.i)

    def workerFinished(self, ret):
        QgsMessageLog.logMessage('Task finished:\n' + str(ret), 'CartoDB Plugin', QgsMessageLog.INFO)

    def workerError(self, e, exception_string):
        QgsMessageLog.logMessage('Worker thread raised an exception:\n'.format(exception_string), 'CartoDB Plugin', QgsMessageLog.CRITICAL)


class CartoDBLayer(QgsVectorLayer):
    LAYER_CNAME_PROPERTY = 'cartoName'
    LAYER_TNAME_PROPERTY = 'tableName'
    LAYER_SQL_PROPERTY = 'cartoSQL'

    def __init__(self, iface, tableName, cartoName, apiKey, sql=None):
        # SQLite available?
        self.iface = iface
        self.user = cartoName
        self._apiKey = apiKey
        self.layerType = 'ogr'
        readOnly = True
        driverName = "SQLite"
        sqLiteDrv = ogr.GetDriverByName(driverName)
        self.databasePath = QgisCartoDB.CartoDBPlugin.PLUGIN_DIR + '/db/database.sqlite'
        self.datasource = sqLiteDrv.Open(self.databasePath, True)
        self.layerName = tableName
        self.cartoTable = tableName
        forceReadOnly = False

        if sql is None:
            sql = 'SELECT * FROM ' + tableName
        else:
            forceReadOnly = True

        self._loadData(sql, forceReadOnly)

    def initConnections(self):
        QgsMessageLog.logMessage('Init connections for: ' + self.layerName, 'CartoDB Plugin', QgsMessageLog.INFO)
        self.editingStarted.connect(self._editingStarted)
        self.attributeAdded[int].connect(self._attributeAdded)
        self.beforeCommitChanges.connect(self._beforeCommitChanges)

    def _loadData(self, sql, forceReadOnly):
        cartoUrl = 'http://{}.cartodb.com/api/v2/sql?format=GeoJSON&q={}&api_key={}'.format(self.user, sql, self._apiKey)
        response = urlopen(cartoUrl)
        path = response.read()
        dsGeoJSON = ogr.Open(path)
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
                    readOnly = False
                else:
                    QgsMessageLog.logMessage('Some error ocurred opening SQLite datasource', 'CartoDB Plugin', QgsMessageLog.WARNING)
                self.datasource.Destroy()
            else:
                QgsMessageLog.logMessage('Some error ocurred opening GeoJSON layer', 'CartoDB Plugin', QgsMessageLog.WARNING)
        else:
            QgsMessageLog.logMessage('Some error ocurred opening GeoJSON datasource', 'CartoDB Plugin', QgsMessageLog.WARNING)

        if forceReadOnly:
            readOnly = True
        if readOnly:
            QgsMessageLog.logMessage('CartoDB Layer is readonly mode', 'CartoDB Plugin', QgsMessageLog.WARNING)

        super(QgsVectorLayer, self).__init__(path, self.layerName, self.layerType)
        self.readOnly = readOnly
        self._deletedFeatures = []

        if not self.readOnly:
            self.initConnections()
            self._uneditableFields()

        self.setCustomProperty(CartoDBLayer.LAYER_CNAME_PROPERTY, self.user)
        self.setCustomProperty(CartoDBLayer.LAYER_TNAME_PROPERTY, self.cartoTable)
        if forceReadOnly:
            self.setCustomProperty(CartoDBLayer.LAYER_SQL_PROPERTY, sql)

    def _uneditableFields(self):
        sql = "SELECT table_name, column_name, column_default, is_nullable, data_type, table_schema \
                FROM information_schema.columns \
                WHERE data_type != 'USER-DEFINED' AND table_schema = 'public' AND table_name = '" + self.cartoTable + "' \
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
            sql = "UPDATE " + self.cartoTable + " SET "
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
                sql = "UPDATE " + self.cartoTable + " SET the_geom = "
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
            sql = "INSERT INTO " + self.cartoTable + " ("
            addComma = False
            for field in feature.fields():
                if unicode(feature[field.name()]) == 'NULL' or feature[field.name()] is None:
                    continue
                if addComma:
                    sql = sql + ", "
                sql = sql + field.name()
                addComma = True
            sql = sql + ", the_geom) VALUES ("
            addComma = False
            for field in feature.fields():
                if unicode(feature[field.name()]) == 'NULL' or feature[field.name()] is None:
                    continue
                if addComma:
                    sql = sql + ", "
                sql = sql + "'" + unicode(feature[field.name()]) + "'"
                addComma = True
            sql = sql + ", ST_GeomFromText('" + feature.geometry().exportToWkt() + "', 4326)) RETURNING cartodb_id"
            sql = sql.encode('utf-8')
            res = self._updateSQL(sql, 'Some error ocurred inserting feature')
            if isinstance(res, dict) and res['total_rows'] == 1:
                self.iface.messageBar().pushMessage('Info',
                                                    'Feature inserted at CartoDB servers',
                                                    level=self.iface.messageBar().INFO, duration=10)
                self.setFieldEditable(self.fieldNameIndex('cartodb_id'), True)
                self.editBuffer().changeAttributeValue(featureID, self.fieldNameIndex('cartodb_id'), res['rows'][0]['cartodb_id'], None)
                self.setFieldEditable(self.fieldNameIndex('cartodb_id'), False)

    def _deleteFeatures(self, deletedFeatureIds):
        provider = self.dataProvider()
        for featureID in deletedFeatureIds:
            QgsMessageLog.logMessage('Delete feature with feature ID: ' + str(featureID), 'CartoDB Plugin', QgsMessageLog.INFO)
            request = QgsFeatureRequest().setFilterFid(featureID)
            try:
                feature = provider.getFeatures(request).next()
                sql = "DELETE FROM " + self.cartoTable + " WHERE cartodb_id = " + unicode(feature['cartodb_id'])
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
