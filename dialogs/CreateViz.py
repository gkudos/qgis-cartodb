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
from PyQt4.QtCore import Qt, QFile, QFileInfo, pyqtSlot, qDebug
from PyQt4.QtGui import QApplication, QAbstractItemView, QDialog, QListWidgetItem, QLabel, QPixmap

from qgis.core import QgsMapLayerRegistry, QgsMapLayer

from QgisCartoDB.dialogs.Basic import CartoDBPluginUserDialog
from QgisCartoDB.ui.CreateViz import Ui_CreateViz
from QgisCartoDB.widgets import CartoDBLayersListWidget, CartoDBLayerListItem

import os


class CartoDBPluginCreateViz(CartoDBPluginUserDialog):
    def __init__(self, toolbar, parent=None):
        CartoDBPluginUserDialog.__init__(self, toolbar, parent)
        self.toolbar = toolbar

        self.ui = Ui_CreateViz()
        self.ui.setupUi(self)

        self.ui.availableList = CartoDBLayersListWidget(self)
        self.ui.availableList.setAcceptDrops(True)
        self.ui.availableList.viewport().setAcceptDrops(True)
        self.ui.availableList.setDragEnabled(True)
        self.ui.availableList.setDropIndicatorShown(True)
        self.ui.availableList.setDragDropMode(QAbstractItemView.DragDrop)
        self.ui.availableList.setDefaultDropAction(Qt.MoveAction)
        self.ui.availableList.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.ui.availableLayout.addWidget(self.ui.availableList)

        self.ui.mapList = CartoDBLayersListWidget(self)
        self.ui.mapList.setAcceptDrops(True)
        self.ui.mapList.viewport().setAcceptDrops(True)
        self.ui.mapList.setDragEnabled(True)
        self.ui.mapList.setDropIndicatorShown(True)
        self.ui.mapList.setDragDropMode(QAbstractItemView.DragDrop)
        self.ui.mapList.setDefaultDropAction(Qt.MoveAction)
        self.ui.mapList.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.ui.mapLayout.addWidget(self.ui.mapList)

        self.ui.saveBT.clicked.connect(self.convert2cartoCSS)

        layers = QgsMapLayerRegistry.instance().mapLayers()

        self.ui.availableList.clear()
        for id, ly in layers.iteritems():
            if ly.type() == QgsMapLayer.VectorLayer:
                item = QListWidgetItem(self.ui.availableList)
                widget = CartoDBLayerListItem(ly.name(), ly, self.getSize(ly), ly.dataProvider().featureCount())
                item.setSizeHint(widget.sizeHint())
                self.ui.availableList.setItemWidget(item, widget)

    def getSize(self, layer):
        filePath = layer.dataProvider().dataSourceUri()
        if filePath.find('|') != -1:
            filePath = filePath[0:filePath.find('|')]

        file = QFile(filePath)
        fileInfo = QFileInfo(file)

        dirName = fileInfo.dir().absolutePath()
        fileName = fileInfo.completeBaseName()

        size = 0
        if layer.storageType() == 'ESRI Shapefile':
            for suffix in ['.shp', '.dbf', '.prj', '.shx']:
                file = QFile(os.path.join(dirName, fileName + suffix))
                fileInfo = QFileInfo(file)
                size = size + fileInfo.size()
        elif layer.storageType() in ['GPX', 'GeoJSON', 'LIBKML']:
            size = size + fileInfo.size()

        return size

    def convert2cartoCSS(self):
        items = self.ui.availableList.selectedItems()
        for i, table in enumerate(items):
            widget = self.ui.availableList.itemWidget(table)
            renderer = widget.layer.rendererV2()
            qDebug('Type: + ' + renderer.type())
            symbol = renderer.symbol()
            for i in xrange(symbol.symbolLayerCount()):
                lyr = symbol.symbolLayer(i)
                qDebug("%d: %s" % (i, lyr.layerType()))
