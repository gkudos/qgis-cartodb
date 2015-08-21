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
from PyQt4.QtCore import Qt, QFile, QFileInfo, pyqtSlot, qDebug, QPyNullVariant
from PyQt4.QtGui import QApplication, QAbstractItemView, QDialog, QListWidgetItem, QLabel, QPixmap, QPushButton, QSizePolicy
from PyQt4.QtGui import QClipboard, QPainter, QColor

from qgis.core import QGis, QgsMapLayerRegistry, QgsMapLayer, QgsPalLayerSettings, NULL
from qgis.gui import QgsMessageBar

import QgisCartoDB.CartoDBPlugin
from QgisCartoDB.cartodb import CartoDBApi
from QgisCartoDB.dialogs.Basic import CartoDBPluginUserDialog
from QgisCartoDB.layers import CartoDBLayer
from QgisCartoDB.ui.CreateViz import Ui_CreateViz
from QgisCartoDB.utils import randomColor
from QgisCartoDB.widgets import CartoDBLayersListWidget, CartoDBLayerListItem

from string import Template

import copy
import os
import webbrowser


class CartoDBPluginCreateViz(CartoDBPluginUserDialog):
    def __init__(self, toolbar, iface, parent=None):
        CartoDBPluginUserDialog.__init__(self, toolbar, parent)

        self.iface = iface

        self.ui = Ui_CreateViz()
        self.ui.setupUi(self)

        self.ui.bar = QgsMessageBar()
        self.ui.bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.ui.verticalLayout.insertWidget(0, self.ui.bar)

        '''
        self.ui.availableList = CartoDBLayersListWidget(self, 'availableList')
        self.ui.availableList.setAcceptDrops(True)
        self.ui.availableList.viewport().setAcceptDrops(True)
        self.ui.availableList.setDragEnabled(True)
        self.ui.availableList.setDropIndicatorShown(True)
        self.ui.availableList.setDragDropMode(QAbstractItemView.DragDrop)
        self.ui.availableList.setDefaultDropAction(Qt.MoveAction)
        self.ui.availableList.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.ui.availableLayout.addWidget(self.ui.availableList)

        self.ui.mapList = CartoDBLayersListWidget(self, 'mapList')
        self.ui.mapList.setAcceptDrops(True)
        self.ui.mapList.viewport().setAcceptDrops(True)
        self.ui.mapList.setDragEnabled(True)
        self.ui.mapList.setDropIndicatorShown(True)
        self.ui.mapList.setDragDropMode(QAbstractItemView.DragDrop)
        self.ui.mapList.setDefaultDropAction(Qt.MoveAction)
        self.ui.mapList.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.ui.mapLayout.addWidget(self.ui.mapList)
        '''

        self.ui.mapNameTX.textChanged.connect(self.validateButtons)
        # self.ui.mapList.itemSelectionChanged.connect(self.validateButtons)
        self.ui.cancelBT.clicked.connect(self.reject)
        self.ui.saveBT.clicked.connect(self.createViz)
        self.ui.cartoCssBT.clicked.connect(self.createCartoCss)
        '''
        self.ui.addAllBT.clicked.connect(self.addAllItems)
        self.ui.addBT.clicked.connect(self.addItems)
        self.ui.removeAllBT.clicked.connect(self.removeAllItems)
        self.ui.removeBT.clicked.connect(self.removeItems)
        '''

        # TODO Implement functionality
        self.ui.sqlBT.hide()
        self.ui.cartoCssBT.hide()

        self.withWarnings = False

        layers = self.iface.legendInterface().layers()

        self.ui.availableList.clear()
        self.cartoDBLayers = []
        cartoDBLayersCount = 0
        for ly in layers:
            if ly.type() == QgsMapLayer.VectorLayer and isinstance(ly, CartoDBLayer):
                cartoDBLayersCount = cartoDBLayersCount + 1
                if ly.user == self.currentUser:
                    self.cartoDBLayers.append(ly)
                    item = QListWidgetItem(self.ui.availableList)
                    widget = CartoDBLayerListItem(ly.name(), ly, self.getSize(ly), ly.dataProvider().featureCount())
                    item.setSizeHint(widget.sizeHint())
                    self.ui.availableList.setItemWidget(item, widget)

        if cartoDBLayersCount > 0 and len(self.cartoDBLayers) == 0:
            self.ui.bar.clearWidgets()
            self.ui.bar.pushMessage(QApplication.translate('CartoDBPlugin', 'Warning') + '!!',
                                    QApplication.translate('CartoDBPlugin',
                                                           'At least one CartoDB layer should belong or be visible to {}').format(self.currentUser),
                                    level=QgsMessageBar.WARNING)
        else:
            self.cartoDBLayers.reverse()

    def copyItem(self, source, dest, item):
        itemWidget = source.itemWidget(item)
        newItemWidget = CartoDBLayerListItem(itemWidget.tableName, itemWidget.layer, itemWidget.size, itemWidget.rows)
        newItem = source.takeItem(source.row(item))

        dest.addItem(newItem)
        dest.setItemWidget(newItem, newItemWidget)
        dest.setItemSelected(newItem, True)

    def addAllItems(self):
        self.ui.availableList.selectAll()
        self.addItems()

    '''
    def addItems(self):
        if len(self.ui.availableList.selectedItems()) > 0:
            for item in self.ui.availableList.selectedItems():
                self.copyItem(self.ui.availableList, self.ui.mapList, item)
            self.ui.mapList.setFocus()

    def removeAllItems(self):
        self.ui.mapList.selectAll()
        self.removeItems()

    def removeItems(self):
        if len(self.ui.mapList.selectedItems()) > 0:
            for item in self.ui.mapList.selectedItems():
                self.copyItem(self.ui.mapList, self.ui.availableList, item)
            self.ui.availableList.setFocus()
            self.validateButtons()
    '''

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

    def createCartoCss(self):
        item = self.ui.availableList.currentItem()

        if item is not None:
            widget = self.ui.availableList.itemWidget(item)
            layer = widget.layer
            cartoCSS = self.convert2CartoCSS(layer)
            qDebug('CartoCSS: {}'.format(cartoCSS.encode('utf8', 'ignore')))

    def createViz(self):
        self.ui.bar.clearWidgets()
        self.ui.bar.pushMessage("Info", QApplication.translate('CartoDBPlugin', 'Creating Map'), level=QgsMessageBar.INFO)
        self.withWarnings = False

        for ly in self.cartoDBLayers:
            layer = ly
            if not layer.isSQL:
                break
            else:
                layer = None

        if layer is not None:
            cartoDBApi = CartoDBApi(self.currentUser, self.currentApiKey, self.currentMultiuser)
            cartoDBApi.fetchContent.connect(self.cbCreateViz)
            cartoDBApi.createVizFromTable(layer.fullTableName(), self.ui.mapNameTX.text(), self.ui.descriptionTX.toPlainText())
        else:
            self.ui.bar.clearWidgets()
            widget = self.ui.bar.createMessage(QApplication.translate('CartoDBPlugin', 'Error!!'),
                                               QApplication.translate('CartoDBPlugin', 'All layers are SQL layers'))
            self.ui.bar.pushWidget(widget, QgsMessageBar.CRITICAL)

    def cbCreateViz(self, data):
        self.currentViz = data

        cartoDBApi = CartoDBApi(self.currentUser, self.currentApiKey, self.currentMultiuser)
        cartoDBApi.fetchContent.connect(self.cbGetLayers)
        cartoDBApi.getLayersMap(data['map_id'])

    def cbGetLayers(self, data):
        layer = self.cartoDBLayers[0]
        cartoCSS = self.convert2CartoCSS(layer)
        cartoDBApi = CartoDBApi(self.currentUser, self.currentApiKey, self.currentMultiuser)
        layer1 = data['layers'][1]
        if layer.isSQL:
            layer1["options"]["query"] = layer.sql
        else:
            layer1["options"]["query"] = ""
            qDebug('Layer {}'.format(layer.fullTableName()))
            layer1["options"]["table_name"] = layer.fullTableName()
        layer1['options']['tile_style'] = cartoCSS
        layer1["options"]["legend"] = None
        layer1["options"]["order"] = 1
        layer1["order"] = 1
        cartoDBApi.fetchContent.connect(self.showMessage)
        cartoDBApi.updateLayerInMap(self.currentViz['map_id'], layer1)

        for i, layer in enumerate(self.cartoDBLayers[1:len(self.cartoDBLayers)]):
            order = i + 2
            qDebug('Agregando: {} en pos: {}'.format(layer.tableName(), order))
            cartoCSS = self.convert2CartoCSS(layer)
            # cartoDBApi.fetchContent.connect(self.cbCreateViz)
            newLayer = copy.deepcopy(layer1)
            newLayer["options"]["tile_style"] = cartoCSS
            newLayer["options"]["order"] = order
            newLayer["options"]["legend"] = None
            newLayer["order"] = order
            newLayer["id"] = None
            if layer.isSQL:
                newLayer["options"]["query"] = layer.sql
            else:
                qDebug('Layer {}'.format(layer.fullTableName()))
                newLayer["options"]["query"] = ""
                newLayer["options"]["table_name"] = layer.fullTableName()
            cartoDBApi.addLayerToMap(self.currentViz['map_id'], newLayer)

    def showMessage(self, data):
        url = '{}/viz/{}/public_map'.format(self.currentUserData['base_url'], self.currentViz['id'])

        def openVis():
            webbrowser.open(url)

        def copyURL():
            QApplication.clipboard().setText(url)


        if not self.withWarnings:
            self.ui.bar.clearWidgets()
            msg = '{} created'
        else:
            msg = '{} created, but has warnings'

        widget = self.ui.bar.createMessage(QApplication.translate('CartoDBPlugin', 'Map Created'),
                                           QApplication.translate('CartoDBPlugin', msg).format(self.currentViz['name']))
        button = QPushButton(widget)
        button.setText(QApplication.translate('CartoDBPlugin', 'Copy Link'))
        button.pressed.connect(copyURL)
        widget.layout().addWidget(button)

        button = QPushButton(widget)
        button.setText(QApplication.translate('CartoDBPlugin', 'Open'))
        button.pressed.connect(openVis)
        widget.layout().addWidget(button)
        self.ui.bar.pushWidget(widget, QgsMessageBar.INFO if not self.withWarnings else QgsMessageBar.WARNING, duration=10)

    def convert2CartoCSS(self, layer):
        renderer = layer.rendererV2()
        cartoCSS = ''
        labelCSS = ''

        labelSettings = QgsPalLayerSettings()
        labelSettings.readFromLayer(layer)
        if labelSettings.enabled:
            d = {
                'layername': '#' + layer.tableName(),
                'field': labelSettings.getLabelExpression().dump(),
                # TODO Get font size
                'size': 11,
                'color': labelSettings.textColor.name()
            }
            filein = open(QgisCartoDB.CartoDBPlugin.PLUGIN_DIR + '/templates/labels.less')
            labelCSS = Template(filein.read())
            labelCSS = labelCSS.substitute(d)
        # qDebug('Label CSS: ' + labelCSS)

        # CSS for single symbols
        if renderer.type() == 'singleSymbol':
            symbol = renderer.symbol()
            cartoCSS = self.symbol2CartoCSS(layer, symbol, '#' + layer.tableName())
        # CSS for categorized symbols
        elif renderer.type() == 'categorizedSymbol':
            # qDebug('Categorized: ' + renderer.classAttribute())
            for cat in renderer.categories():
                symbol = cat.symbol()
                # qDebug("%s: %s type: %s" % (str(cat.value()), cat.label(), type(cat.value())))
                if cat.value() is not None and cat.value() != '' and not isinstance(cat.value(), QPyNullVariant):
                    if isinstance(cat.value(), (int, float, long)) or (isinstance(cat.value(), str) and cat.value().isdecimal()):
                        value = unicode(cat.value())
                    else:
                        value = unicode('"' + cat.value() + '"')

                    value = str(value.encode('utf8', 'ignore'))
                    # qDebug('Value {}'.format(value))
                    styleName = '#{}[{}={}]'.format(layer.tableName(), renderer.classAttribute(), value).decode('utf8')
                    cartoCSS = cartoCSS + \
                        self.symbol2CartoCSS(layer, symbol, styleName)
                else:
                    cartoCSS = self.symbol2CartoCSS(layer, symbol, '#' + layer.tableName()) + cartoCSS
        # CSS for graduated symbols
        elif renderer.type() == 'graduatedSymbol':
            # qDebug('Graduated')
            def upperValue(ran):
                return ran.upperValue()

            ranges = sorted(renderer.ranges(), key=upperValue, reverse=True)
            for ran in ranges:
                symbol = ran.symbol()
                '''
                qDebug("%f - %f: %s" % (
                    ran.lowerValue(),
                    ran.upperValue(),
                    ran.label()
                ))
                '''
                cartoCSS = cartoCSS + \
                    self.symbol2CartoCSS(layer, symbol, '#' + layer.tableName() + '[' + renderer.classAttribute() + '<=' + str(ran.upperValue()) + ']')

        return '/** Styles designed from QGISCartoDB Plugin */\n\n' + cartoCSS + '\n' + labelCSS

    def symbol2CartoCSS(self, layer, symbol, styleName):
        cartoCSS = ''
        layerOpacity = str(float((100.0 - layer.layerTransparency())/100.0))

        blendMode = layer.featureBlendMode()
        compositionMode = 'src-over'
        if blendMode == QPainter.CompositionMode_Lighten:
            compositionMode = 'lighten'
        elif blendMode == QPainter.CompositionMode_Screen:
            compositionMode = 'screen'
        elif blendMode ==  QPainter.CompositionMode_ColorDodge:
            compositionMode = 'color-dodge'
        elif blendMode == QPainter.CompositionMode_Plus:
            compositionMode = 'plus'
        elif blendMode == QPainter.CompositionMode_Darken:
            compositionMode = 'darken'
        elif blendMode == QPainter.CompositionMode_Multiply:
            compositionMode = 'multiply'
        elif blendMode == QPainter.CompositionMode_ColorBurn:
            compositionMode = 'color-burn'
        elif blendMode == QPainter.CompositionMode_Overlay:
            compositionMode = 'overlay'
        elif blendMode == QPainter.CompositionMode_SoftLight:
            compositionMode = 'soft-light'
        elif blendMode == QPainter.CompositionMode_HardLight:
            compositionMode = 'hard-light'
        elif blendMode == QPainter.CompositionMode_Difference:
            compositionMode = 'difference'
        elif blendMode == QPainter.CompositionMode_Exclusion:
            compositionMode = 'exclusion'

        if symbol.symbolLayerCount() > 0:
            lyr = None
            for i in range(0, symbol.symbolLayerCount()):
                lyr = symbol.symbolLayer(i)
                if lyr.layerType().startswith('Simple'):
                    break

            # qDebug("Symbol Type: {}".format(lyr.layerType()))
            # qDebug("Symbol Properties: {}".format(lyr.properties()))

            if lyr is not None and lyr.layerType().startswith('Simple'):
                filein = None
                if layer.geometryType() == QGis.Point:
                    d = {
                        'layername': styleName,
                        'fillColor': lyr.fillColor().name(),
                        # 96 ppi = 3.7795275552 mm
                        'width': round(3.7795275552 * lyr.size(), 0),
                        'opacity': layerOpacity,
                        'borderColor': lyr.outlineColor().name(),
                        'borderWidth': round(3.7795275552 * lyr.outlineWidth(), 0),
                        'markerCompOp': compositionMode
                    }
                    filein = open(QgisCartoDB.CartoDBPlugin.PLUGIN_DIR + '/templates/simplepoint.less')
                elif layer.geometryType() == QGis.Line:
                    lineWidth = round(3.7795275552 * lyr.width(), 0)
                    if lyr.penStyle() == Qt.NoPen:
                        lineWidth = 0

                    d = {
                        'layername': styleName,
                        'lineColor': lyr.color().name(),
                        'lineWidth': lineWidth,
                        'opacity': layerOpacity,
                        'lineCompOp': compositionMode,
                        'lineJoin': self._getLineJoin(lyr),
                        'lineDasharray': self._getLineDasharray(lyr.penStyle(), lineWidth)
                    }
                    filein = open(QgisCartoDB.CartoDBPlugin.PLUGIN_DIR + '/templates/simpleline.less')
                elif layer.geometryType() == QGis.Polygon:
                    borderWidth = round(3.7795275552 * lyr.borderWidth(), 0)
                    if lyr.borderStyle() == Qt.NoPen:
                        borderWidth = 0

                    d = {
                        'layername': styleName,
                        'fillColor': lyr.fillColor().name(),
                        'opacity': layerOpacity,
                        'borderColor': lyr.outlineColor().name(),
                        'borderWidth': borderWidth,
                        'polygonCompOp': compositionMode,
                        'lineJoin': self._getLineJoin(lyr),
                        'lineDasharray': self._getLineDasharray(lyr.borderStyle(), borderWidth)
                    }
                    filein = open(QgisCartoDB.CartoDBPlugin.PLUGIN_DIR + '/templates/simplepolygon.less')

            else:
                if not self.withWarnings:
                    self.ui.bar.clearWidgets()

                self.withWarnings = True
                widget = self.ui.bar.createMessage(QApplication.translate('CartoDBPlugin', 'Symbology not supported'),
                                                   QApplication.translate('CartoDBPlugin', '{} layer').format(layer.name()))
                self.ui.bar.pushWidget(widget, QgsMessageBar.WARNING)

                r, g, b = randomColor()
                if layer.geometryType() == QGis.Point:
                    d = {
                        'layername': styleName,
                        'fillColor': QColor(r, g, b, 255).name(),
                        'markerCompOp': compositionMode
                    }
                    filein = open(QgisCartoDB.CartoDBPlugin.PLUGIN_DIR + '/templates/defaultpoint.less')
                elif layer.geometryType() == QGis.Line:
                    d = {
                        'layername': styleName,
                        'lineColor': QColor(r, g, b, 255).name(),
                        'lineCompOp': compositionMode,
                    }
                    filein = open(QgisCartoDB.CartoDBPlugin.PLUGIN_DIR + '/templates/defaultline.less')
                elif layer.geometryType() == QGis.Polygon:
                    d = {
                        'layername': styleName,
                        'fillColor': QColor(r, g, b, 255).name(),
                        'polygonCompOp': compositionMode,
                    }
                    filein = open(QgisCartoDB.CartoDBPlugin.PLUGIN_DIR + '/templates/defaultpolygon.less')

        cartoCSS = Template(filein.read())
        cartoCSS = cartoCSS.substitute(d,
                            input_encoding='utf-8',
                            output_encoding='utf-8',
                            encoding_errors='replace')
        return cartoCSS

    def validateButtons(self):
        enabled = self.ui.mapNameTX.text() != '' # and self.ui.mapList.count() > 0
        self.ui.saveBT.setEnabled(enabled)

    def _getLineJoin(self, lyr):
        joinStyle = 'miter'
        if lyr.penJoinStyle() == Qt.BevelJoin:
            joinStyle = 'bevel'
        elif lyr.penJoinStyle() == Qt.RoundJoin:
            joinStyle = 'round'
        return joinStyle

    def _getLineDasharray(self, lineStyle, lineWidth):
        lineDasharray = '0'
        if lineStyle == Qt.DashLine:
            lineDasharray = '5,5'
        elif lineStyle == Qt.DotLine:
            lineDasharray = '{},{}'.format(lineWidth, lineWidth*5)
        elif lineStyle == Qt.DashDotLine:
            lineDasharray = '{},{},{},{}'.format(lineWidth*10, lineWidth*10, lineWidth, lineWidth*10)
        elif lineStyle == Qt.DashDotDotLine:
            lineDasharray = '{},{},{},{},{},{}'.format(lineWidth*5, lineWidth*5, lineWidth, lineWidth*5, lineWidth, lineWidth*5)
        return lineDasharray
