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
from PyQt4.QtCore import Qt, QSettings, QFile, QFileInfo, QTimer, pyqtSlot, qDebug
from PyQt4.QtGui import QApplication, QDialog, QPixmap, QListWidgetItem, QLabel, QSizePolicy

from qgis.core import QgsMapLayerRegistry, QgsMapLayer, QgsVectorFileWriter
from qgis.gui import QgsMessageBar

from QgisCartoDB.cartodb import CartoDBApi
from QgisCartoDB.layers import CartoDBLayer
from QgisCartoDB.dialogs.Basic import CartoDBPluginUserDialog
from QgisCartoDB.ui.Upload import Ui_Upload
from QgisCartoDB.widgets import CartoDBLayerListItem

import math
import os
import tempfile
import zipfile


class CartoDBPluginUpload(CartoDBPluginUserDialog):
    def __init__(self, toolbar, parent=None):
        CartoDBPluginUserDialog.__init__(self, toolbar, parent)

        self.ui = Ui_Upload()
        self.ui.setupUi(self)

        self.ui.bar = QgsMessageBar()
        self.ui.bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.ui.verticalLayout.insertWidget(0, self.ui.bar)

        self.ui.uploadBT.clicked.connect(self.upload)
        self.ui.cancelBT.clicked.connect(self.reject)

        layers = QgsMapLayerRegistry.instance().mapLayers()

        # TODO Implement add to project
        self.ui.convertCH.hide()
        self.ui.overideCH.hide()

        self.ui.layersList.clear()
        self.ui.uploadBar.setValue(0)
        self.ui.uploadBar.hide()
        self.ui.uploadingLB.hide()
        for id, ly in layers.iteritems():
            if ly.type() == QgsMapLayer.VectorLayer and not isinstance(ly, CartoDBLayer):
                item = QListWidgetItem(self.ui.layersList)
                widget = CartoDBLayerListItem(ly.name(), ly, self.getSize(ly), ly.dataProvider().featureCount())
                item.setSizeHint(widget.sizeHint())
                self.ui.layersList.setItemWidget(item, widget)

    def upload(self):
        registry = QgsMapLayerRegistry.instance()
        for layerItem in self.ui.layersList.selectedItems():
            widget = self.ui.layersList.itemWidget(layerItem)
            qDebug('Layer: ' + str(widget.layer.storageType()))
            storageType = widget.layer.storageType()
            # if storageType in ['ESRI Shapefile', 'GPX', 'GeoJSON', 'LIBKML', 'SQLite database with SpatiaLite extension']:
            zipPath = self.zipLayer(widget.layer)
            self.uploadZip(zipPath, widget)

    def uploadZip(self, zipPath, widget):
        def completeUpload(data):
            timer = QTimer(self)

            self.ui.uploadBar.hide()
            self.ui.uploadingLB.hide()
            self.ui.uploadBT.setEnabled(True)
            self.ui.bar.clearWidgets()
            self.ui.bar.pushMessage(QApplication.translate('CartoDBPlugin', 'Upload Complete'),
                                    level=QgsMessageBar.INFO, duration=5)

            def statusComplete(d):
                if d['state'] == 'complete':
                    timer.stop()
                    self.ui.statusLB.setText(QApplication.translate('CartoDBPlugin', 'Ready'))
                    widget.setStatus(d['state'], 100)
                    self.ui.bar.clearWidgets()
                    self.ui.bar.pushMessage(QApplication.translate('CartoDBPlugin', 'Table {} created').format(d['table_name']),
                                            level=QgsMessageBar.INFO, duration=5)
                elif d['state'] == 'failure':
                    timer.stop()
                    self.ui.statusLB.setText(QApplication.translate('CartoDBPlugin', '{} failed, {}').format(widget.layer.name(), d['get_error_text']['title']))
                    widget.setStatus(d['state'])
                    self.ui.bar.clearWidgets()
                    self.ui.bar.pushMessage(QApplication.translate('CartoDBPlugin', 'Error uploading {}').format(widget.layer.name()),
                                            level=QgsMessageBar.WARNING, duration=5)
                else:
                    widget.setStatus(d['state'])

            def timerComplete():
                cartodbApi = CartoDBApi(self.currentUser, self.currentApiKey, self.currentMultiuser)
                cartodbApi.fetchContent.connect(statusComplete)
                cartodbApi.checkUploadStatus(data['item_queue_id'])

            timer.timeout.connect(timerComplete)
            timer.start(500)

        cartodbApi = CartoDBApi(self.currentUser, self.currentApiKey, self.currentMultiuser)
        cartodbApi.fetchContent.connect(completeUpload)
        cartodbApi.progress.connect(self.progressUpload)
        self.ui.uploadBar.show()
        self.ui.uploadBT.setEnabled(False)
        self.ui.uploadingLB.setText(QApplication.translate('CartoDBPlugin', 'Uploading {}').format(widget.layer.name()))
        self.ui.uploadingLB.show()
        self.ui.bar.clearWidgets()
        cartodbApi.upload(zipPath)


    def progressUpload(self, current, total):
        self.ui.uploadBar.setValue(math.ceil(float(current)/float(total)*100))

    def getSize(self, layer):
        isZipFile = False
        filePath = layer.dataProvider().dataSourceUri()
        if filePath.find('|') != -1:
            filePath = filePath[0:filePath.find('|')]

        if filePath.startswith('/vsizip/'):
            filePath = filePath.replace('/vsizip/', '')
            isZipFile = True

        file = QFile(filePath)
        fileInfo = QFileInfo(file)

        dirName = fileInfo.dir().absolutePath()
        fileName = fileInfo.completeBaseName()

        size = 0
        if layer.storageType() == 'ESRI Shapefile' and not isZipFile:
            for suffix in ['.shp', '.dbf', '.prj', '.shx']:
                file = QFile(os.path.join(dirName, fileName + suffix))
                fileInfo = QFileInfo(file)
                size = size + fileInfo.size()
        elif layer.storageType() in ['GPX', 'GeoJSON', 'LIBKML'] or isZipFile:
            size = size + fileInfo.size()

        return size

    def zipLayer(self, layer):
        filePath = layer.dataProvider().dataSourceUri()
        if filePath.find('|') != -1:
            filePath = filePath[0:filePath.find('|')]

        if filePath.startswith('/vsizip/'):
            filePath = filePath.replace('/vsizip/', '')
            if layer.storageType() in ['ESRI Shapefile', 'GPX', 'GeoJSON', 'LIBKML']:
                return filePath

        file = QFile(filePath)
        fileInfo = QFileInfo(file)

        dirName = fileInfo.dir().absolutePath()
        fileName = fileInfo.completeBaseName()

        tempdir = tempfile.tempdir
        if tempdir is None:
            tempdir = tempfile.mkdtemp()

        zipPath = os.path.join(tempdir, layer.name() + '.zip')
        zipFile = zipfile.ZipFile(zipPath, 'w')


        if layer.storageType() == 'ESRI Shapefile':
            for suffix in ['.shp', '.dbf', '.prj', '.shx']:
                if os.path.exists(os.path.join(dirName, fileName + suffix)):
                    zipFile.write(os.path.join(dirName, fileName + suffix), fileName + suffix, zipfile.ZIP_DEFLATED)
        elif layer.storageType() == 'GeoJSON':
            zipFile.write(filePath, layer.name() + '.geojson', zipfile.ZIP_DEFLATED)
        elif layer.storageType() == 'GPX':
            zipFile.write(filePath, layer.name() + '.gpx', zipfile.ZIP_DEFLATED)
        elif layer.storageType() == 'LIBKML':
            zipFile.write(filePath, layer.name() + '.kml', zipfile.ZIP_DEFLATED)
        else:
            geoJsonName = os.path.join(tempfile.tempdir, layer.name())
            error = QgsVectorFileWriter.writeAsVectorFormat(layer, geoJsonName, "utf-8", None, "GeoJSON")
            if error == QgsVectorFileWriter.NoError:
                zipFile.write(geoJsonName + '.geojson', layer.name() + '.geojson', zipfile.ZIP_DEFLATED)
        zipFile.close()
        return zipPath

    def reject(self):
        # Back out of dialogue
        QDialog.reject(self)
