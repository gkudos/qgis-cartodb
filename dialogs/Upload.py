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
from PyQt4.QtCore import QTimer, pyqtSignal, qDebug
from PyQt4.QtGui import QApplication, QDialog, QListWidgetItem, QSizePolicy

from qgis.core import QgsMapLayerRegistry, QgsMapLayer, QgsVectorFileWriter
from qgis.gui import QgsMessageBar

# pylint: disable-msg=F0401
from QgisCartoDB.cartodb import CartoDBApi
from QgisCartoDB.layers import CartoDBLayer
from QgisCartoDB.dialogs.Basic import CartoDBPluginUserDialog
from QgisCartoDB.ui.Upload import Ui_Upload
from QgisCartoDB.utils import getSize, checkTempDir, zipLayer, checkCartoDBId, stripAccents
from QgisCartoDB.widgets import CartoDBLayerListItem

import math
import tempfile


class CartoDBPluginUpload(CartoDBPluginUserDialog):
    """Dialog for Upload data to CartoDB"""
    addedLayer = pyqtSignal(str, str)

    def __init__(self, iface, toolbar, parent=None):
        CartoDBPluginUserDialog.__init__(self, toolbar, parent)

        self.iface = iface

        self.ui = Ui_Upload()
        self.ui.setupUi(self)

        self.ui.bar = QgsMessageBar()
        self.ui.bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.ui.verticalLayout.insertWidget(0, self.ui.bar)

        self.ui.uploadBT.clicked.connect(self.upload)
        self.ui.cancelBT.clicked.connect(self.reject)
        self.ui.layersList.itemSelectionChanged.connect(self.validateButtons)

        layers = QgsMapLayerRegistry.instance().mapLayers()

        # TODO Implement add to project
        # self.ui.convertCH.hide()
        self.ui.overideCH.hide()

        self.ui.layersList.clear()
        self.ui.uploadBar.setValue(0)
        self.ui.uploadBar.hide()
        self.ui.uploadingLB.hide()
        for id_ly, ly in layers.iteritems():
            qDebug('Layer id {}'.format(stripAccents(id_ly)))
            if ly.type() == QgsMapLayer.VectorLayer and not isinstance(ly, CartoDBLayer):
                item = QListWidgetItem(self.ui.layersList)
                widget = CartoDBLayerListItem(ly.name(), ly, getSize(ly), ly.dataProvider().featureCount())
                item.setSizeHint(widget.sizeHint())
                self.ui.layersList.setItemWidget(item, widget)

    def upload(self):
        """Init upload proccess"""
        for layer_item in self.ui.layersList.selectedItems():
            widget = self.ui.layersList.itemWidget(layer_item)
            qDebug('Layer: ' + str(widget.layer.storageType()))
            layer = checkCartoDBId(widget.layer, self.ui.convertCH.isChecked())
            zip_path = zipLayer(layer)
            self.uploadZip(zip_path, widget, layer, self.ui.convertCH.isChecked())

    def uploadZip(self, zip_path, widget, convertLayer=None, convert=False):
        """Upload Zipfile"""
        def completeUpload(data):
            """On complete upload"""
            timer = QTimer(self)
            qDebug('data: {}'.format(str(data)))

            if 'error' in data and data['error'] is not None:
                self.ui.bar.clearWidgets()
                self.ui.bar.pushMessage(QApplication.translate('CartoDBPlugin', 'Error uploading layer: {}').format(data['error']),
                                        level=QgsMessageBar.CRITICAL, duration=5)
                widget.setStatus('Error', 0)
                return

            self.ui.uploadBar.hide()
            self.ui.uploadingLB.hide()
            self.ui.uploadBT.setEnabled(True)
            self.ui.bar.clearWidgets()
            self.ui.bar.pushMessage(QApplication.translate('CartoDBPlugin', 'Upload Complete'),
                                    level=QgsMessageBar.INFO, duration=5)

            def statusComplete(res):
                """On CartoDB import proccess complete o fail"""
                if res['state'] == 'complete':
                    timer.stop()
                    self.ui.statusLB.setText(QApplication.translate('CartoDBPlugin', 'Ready'))
                    widget.setStatus(res['state'], 100)
                    self.ui.bar.clearWidgets()
                    self.ui.bar.pushMessage(QApplication.translate('CartoDBPlugin', 'Table {} created').format(res['table_name']),
                                            level=QgsMessageBar.INFO, duration=5)

                    if convert:
                        self.convert2CartoDB(convertLayer if convertLayer is not None else widget.layer, res['table_name'])
                elif res['state'] == 'failure':
                    timer.stop()
                    self.ui.statusLB.setText(QApplication.translate('CartoDBPlugin', '{} failed, {}').format(
                        widget.layer.name(), res['get_error_text']['title']))
                    widget.setStatus(res['state'])
                    self.ui.bar.clearWidgets()
                    self.ui.bar.pushMessage(QApplication.translate('CartoDBPlugin', 'Error uploading {}').format(widget.layer.name()),
                                            level=QgsMessageBar.WARNING, duration=5)
                else:
                    widget.setStatus(res['state'])

            def timerComplete():
                """On timer complete, check import process in CartoDB Servers"""
                # pylint: disable-msg=E1101
                cartodb_api = CartoDBApi(self.currentUser, self.currentApiKey, self.currentMultiuser)
                cartodb_api.fetchContent.connect(statusComplete)
                cartodb_api.checkUploadStatus(data['item_queue_id'])

            timer.timeout.connect(timerComplete)
            timer.start(500)


        # pylint: disable-msg=E1101
        cartodb_api = CartoDBApi(self.currentUser, self.currentApiKey, self.currentMultiuser)
        cartodb_api.fetchContent.connect(completeUpload)
        cartodb_api.progress.connect(self.progressUpload)
        self.ui.uploadBar.show()
        self.ui.uploadBT.setEnabled(False)
        self.ui.uploadingLB.setText(QApplication.translate('CartoDBPlugin', 'Uploading {}').format(widget.layer.name()))
        self.ui.uploadingLB.show()
        self.ui.bar.clearWidgets()
        cartodb_api.upload(zip_path)

    def convert2CartoDB(self, layer, tableName):
        """Convert QGIS styles to CartoCSS"""
        checkTempDir()
        temp = tempfile.NamedTemporaryFile()
        qDebug('New file {}'.format(temp.name))
        error = QgsVectorFileWriter.writeAsVectorFormat(layer, temp.name, "utf-8", None, "SQLite")
        if error == QgsVectorFileWriter.NoError:
            self.addedLayer.emit(temp.name + '.sqlite', tableName)
        else:
            self.ui.bar.pushMessage(QApplication.translate('CartoDBPlugin', 'Error loading CartoDB layer {}').format(tableName),
                                    level=QgsMessageBar.WARNING, duration=5)

    def progressUpload(self, current, total):
        """Check upload proccess"""
        self.ui.uploadBar.setValue(math.ceil(float(current)/float(total)*100))

    def reject(self):
        """Back out of dialogue"""
        QDialog.reject(self)

    def validateButtons(self):
        """Validate upload button"""
        enabled = self.ui.layersList.count() > 0
        self.ui.uploadBT.setEnabled(enabled)
