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
from PyQt4.QtCore import Qt, QSettings, pyqtSlot, qDebug
from PyQt4.QtGui import QApplication, QDialog, QPixmap, QListWidgetItem

from qgis.core import QgsMapLayerRegistry, QgsMapLayer

from QgisCartoDB.layers import CartoDBLayer
from QgisCartoDB.ui.Upload import Ui_Upload
from QgisCartoDB.utils import CartoDBPluginWorker

import math
import os
import tempfile
import zipfile


class CartoDBPluginUpload(QDialog):
    def __init__(self, toolbar, parent=None):
        QDialog.__init__(self, parent)
        self.toolbar = toolbar
        self.settings = QSettings()

        self.ui = Ui_Upload()
        self.ui.setupUi(self)

        self.ui.uploadBT.clicked.connect(self.upload)
        self.ui.cancelBT.clicked.connect(self.reject)

        self.currentUser = self.toolbar.currentUser
        self.currentApiKey = self.toolbar.currentApiKey
        self.currentMultiuser = self.toolbar.currentMultiuser

        layers = QgsMapLayerRegistry.instance().mapLayers()

        self.ui.layersList.clear()
        for id, ly in layers.iteritems():
            if ly.type() == QgsMapLayer.VectorLayer and not isinstance(ly, CartoDBLayer):
                item = QListWidgetItem(self.ui.layersList)
                item.setText(ly.name())

        worker = CartoDBPluginWorker(self, 'connectUser')
        worker.start()

    @pyqtSlot()
    def connectUser(self):
        self.getUserData(self.currentUser, self.currentApiKey, self.currentMultiuser)

    def getUserData(self, cartodbUser, apiKey, multiuser=False):
        if self.toolbar.avatarImage is not None:
            pixMap = QPixmap.fromImage(self.toolbar.avatarImage).scaled(self.ui.avatarLB.size(), Qt.KeepAspectRatio)
            self.ui.avatarLB.setPixmap(pixMap)
            self.ui.avatarLB.show()

        if self.toolbar.currentUserData is not None:
            self.currentUserData = self.toolbar.currentUserData
            self.setUpUserData()

    def setUpUserData(self):
        usedQuota = (float(self.currentUserData['quota_in_bytes']) - float(self.currentUserData['remaining_byte_quota']))/1024/1024
        quota = float(self.currentUserData['quota_in_bytes'])/1024/1024

        self.ui.remainingBar.setValue(math.ceil(usedQuota/quota*100))

        if usedQuota >= 1000:
            usedQuota = "{:.2f}".format(usedQuota/1024) + ' GB'
        else:
            usedQuota = "{:.2f}".format(usedQuota) + ' MB'

        if quota >= 1000:
            quota = "{:.2f}".format(quota/1024) + ' GB'
        else:
            quota = "{:.2f}".format(quota) + ' MB'

        self.ui.nameLB.setText(self.currentUserData['username'])
        self.ui.quotaLB.setText(
            QApplication.translate('CartoDBPlugin', 'Using {} of {}')
                        .format(usedQuota, quota))

    def upload(self):
        registry = QgsMapLayerRegistry.instance()
        for layerItem in self.ui.layersList.selectedItems():
            layer = registry.mapLayersByName(layerItem.text())[0]
            qDebug('Layer: ' + str(layer.storageType()))
            if layer.storageType() == 'ESRI Shapefile':
                self.zipLayer(layer)

    def zipLayer(self, layer):
        filePath = layer.dataProvider().dataSourceUri()
        if filePath.find('|') != -1:
            filePath = filePath[0:filePath.find('|')]

        dirName = os.path.dirname(filePath)
        baseName = os.path.basename(filePath)
        fileName = os.path.splitext(baseName)[0]
        zipPath = os.path.join(tempfile.tempdir, layer.name() + '.zip')
        zipFile = zipfile.ZipFile(zipPath, 'w')

        if os.path.exists(os.path.join(dirName, fileName + '.shp')):
            zipFile.write(os.path.join(dirName, fileName + '.shp'), fileName + '.shp', zipfile.ZIP_DEFLATED)
        if os.path.exists(os.path.join(dirName, fileName + '.dbf')):
            zipFile.write(os.path.join(dirName, fileName + '.dbf'), fileName + '.dbf', zipfile.ZIP_DEFLATED)
        if os.path.exists(os.path.join(dirName, fileName + '.prj')):
            zipFile.write(os.path.join(dirName, fileName + '.prj'), fileName + '.prj', zipfile.ZIP_DEFLATED)
        if os.path.exists(os.path.join(dirName, fileName + '.shx')):
            zipFile.write(os.path.join(dirName, fileName + '.shx'), fileName + '.shx', zipfile.ZIP_DEFLATED)
        zipFile.close()
        return zipPath

    def reject(self):
        # Back out of dialogue
        QDialog.reject(self)
