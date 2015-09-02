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
# pylint: disable-msg=E0611
from PyQt4.QtCore import Qt, qDebug, QPyNullVariant
from PyQt4.QtGui import QApplication, QListWidgetItem, QPushButton, QSizePolicy
from PyQt4.QtGui import QPainter, QColor

from qgis.core import QGis, QgsMapLayer, QgsPalLayerSettings
from qgis.gui import QgsMessageBar

# pylint: disable-msg=F0401
import QgisCartoDB.CartoDBPlugin
from QgisCartoDB.cartodb import CartoDBApi
from QgisCartoDB.dialogs.Basic import CartoDBPluginUserDialog
from QgisCartoDB.layers import CartoDBLayer
from QgisCartoDB.ui.CreateViz import Ui_CreateViz
from QgisCartoDB.utils import randomColor, getSize, getLineJoin, getLineDasharray
from QgisCartoDB.widgets import CartoDBLayerListItem

from string import Template

import copy
import webbrowser


class CartoDBPluginCreateViz(CartoDBPluginUserDialog):
    """Dialog for create map"""
    def __init__(self, toolbar, iface, parent=None):
        CartoDBPluginUserDialog.__init__(self, toolbar, parent)

        self.currentViz = None
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
        # pylint: disable-msg=E1101
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
        cartodb_layers_count = 0
        for ly in layers:
            if ly.type() == QgsMapLayer.VectorLayer and isinstance(ly, CartoDBLayer):
                cartodb_layers_count = cartodb_layers_count + 1
                # pylint: disable-msg=E1101
                if ly.user == self.currentUser:
                    self.cartoDBLayers.append(ly)
                    item = QListWidgetItem(self.ui.availableList)
                    widget = CartoDBLayerListItem(ly.name(), ly, getSize(ly), ly.dataProvider().featureCount())
                    item.setSizeHint(widget.sizeHint())
                    self.ui.availableList.setItemWidget(item, widget)

        if cartodb_layers_count > 0 and len(self.cartoDBLayers) == 0:
            self.ui.bar.clearWidgets()
            # pylint: disable-msg=E1101
            self.ui.bar.pushMessage(QApplication.translate('CartoDBPlugin', 'Warning') + '!!',
                                    QApplication.translate('CartoDBPlugin',
                                                           'At least one CartoDB layer should belong or be visible to {}').format(self.currentUser),
                                    level=QgsMessageBar.WARNING)
            self.ui.mapNameTX.setEnabled(False)
            self.ui.descriptionTX.setEnabled(False)
            self.ui.publicCH.setEnabled(False)
        elif cartodb_layers_count == 0:
            self.ui.bar.clearWidgets()
            self.ui.bar.pushMessage(QApplication.translate('CartoDBPlugin', 'Warning') + '!!',
                                    QApplication.translate('CartoDBPlugin',
                                                           'At least there should be a CartoDB layer in the project.'),
                                    level=QgsMessageBar.WARNING)
            self.ui.mapNameTX.setEnabled(False)
            self.ui.descriptionTX.setEnabled(False)
            self.ui.publicCH.setEnabled(False)
        else:
            self.cartoDBLayers.reverse()

    '''
    def copyItem(self, source, dest, item):
        """Copy Item from source to dest"""
        itemWidget = source.itemWidget(item)
        newItemWidget = CartoDBLayerListItem(itemWidget.tableName, itemWidget.layer, itemWidget.size, itemWidget.rows)
        newItem = source.takeItem(source.row(item))

        dest.addItem(newItem)
        dest.setItemWidget(newItem, newItemWidget)
        dest.setItemSelected(newItem, True)

    def addAllItems(self):
        self.ui.availableList.selectAll()
        self.addItems()

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

    def createCartoCss(self):
        """Create CartoCSS for selected layer"""
        item = self.ui.availableList.currentItem()

        if item is not None:
            widget = self.ui.availableList.itemWidget(item)
            layer = widget.layer
            carto_css = self.convert2CartoCSS(layer)
            qDebug('CartoCSS: {}'.format(carto_css.encode('utf8', 'ignore')))

    def createViz(self):
        """Create Map in CartoDB"""
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
            # pylint: disable-msg=E1101
            cartodb_api = CartoDBApi(self.currentUser, self.currentApiKey, self.currentMultiuser)
            cartodb_api.fetchContent.connect(self.cbCreateViz)
            cartodb_api.createVizFromTable(layer.fullTableName(), self.ui.mapNameTX.text(), self.ui.descriptionTX.toPlainText())
        else:
            self.ui.bar.clearWidgets()
            widget = self.ui.bar.createMessage(QApplication.translate('CartoDBPlugin', 'Error!!'),
                                               QApplication.translate('CartoDBPlugin', 'All layers are SQL layers'))
            self.ui.bar.pushWidget(widget, QgsMessageBar.CRITICAL)

    def cbCreateViz(self, data):
        """Callback for create map, get created map data"""
        self.currentViz = data

        # pylint: disable-msg=E1101
        cartodb_api = CartoDBApi(self.currentUser, self.currentApiKey, self.currentMultiuser)
        cartodb_api.fetchContent.connect(self.cbGetLayers)
        cartodb_api.getLayersMap(data['map_id'])
        if self.ui.publicCH.isChecked():
            data['privacy'] = 'PUBLIC'
            cartodb_api = CartoDBApi(self.currentUser, self.currentApiKey, self.currentMultiuser)
            cartodb_api.updateViz(data)

    def cbGetLayers(self, data):
        """Callback for getLayers, update cartoCSS to map layers"""
        layer = self.cartoDBLayers[0]
        carto_css = self.convert2CartoCSS(layer)
        # pylint: disable-msg=E1101
        cartodb_api = CartoDBApi(self.currentUser, self.currentApiKey, self.currentMultiuser)
        layer1 = data['layers'][1]
        if layer.isSQL:
            layer1["options"]["query"] = layer.sql
        else:
            layer1["options"]["query"] = ""
            qDebug('Layer {}'.format(layer.fullTableName()))
            layer1["options"]["table_name"] = layer.fullTableName()
        layer1['options']['tile_style'] = carto_css
        layer1["options"]["legend"] = None
        layer1["options"]["order"] = 1
        layer1["order"] = 1
        cartodb_api.fetchContent.connect(self.showMessage)
        cartodb_api.updateLayerInMap(self.currentViz['map_id'], layer1)

        for i, layer in enumerate(self.cartoDBLayers[1:len(self.cartoDBLayers)]):
            order = i + 2
            qDebug('Agregando: {} en pos: {}'.format(layer.tableName(), order))
            carto_css = self.convert2CartoCSS(layer)
            # cartodb_api.fetchContent.connect(self.cbCreateViz)
            new_layer = copy.deepcopy(layer1)
            new_layer["options"]["tile_style"] = carto_css
            new_layer["options"]["order"] = order
            new_layer["options"]["legend"] = None
            new_layer["order"] = order
            new_layer["id"] = None
            if layer.isSQL:
                new_layer["options"]["query"] = layer.sql
            else:
                qDebug('Layer {}'.format(layer.fullTableName()))
                new_layer["options"]["query"] = ""
                new_layer["options"]["table_name"] = layer.fullTableName()
            cartodb_api.addLayerToMap(self.currentViz['map_id'], new_layer)

    # pylint: disable-msg=W0613
    def showMessage(self, data):
        """Show message to user"""
        # pylint: disable-msg=E1101
        url = '{}/viz/{}/public_map'.format(self.currentUserData['base_url'], self.currentViz['id'])

        def openVis():
            """Open map in default browser"""
            webbrowser.open(url)

        def copyURL():
            """Copy map URL to clipboard"""
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
        """Convert layer symbology to CartoCSS"""
        renderer = layer.rendererV2()
        carto_css = ''
        label_css = ''

        label_settings = QgsPalLayerSettings()
        label_settings.readFromLayer(layer)
        if label_settings.enabled:
            d = {
                'layername': '#' + layer.tableName(),
                'field': label_settings.getLabelExpression().dump(),
                # TODO Get font size
                'size': 11,
                'color': label_settings.textColor.name()
            }
            filein = open(QgisCartoDB.CartoDBPlugin.PLUGIN_DIR + '/templates/labels.less')
            label_css = Template(filein.read())
            label_css = label_css.substitute(d)
        # qDebug('Label CSS: ' + label_css)

        # CSS for single symbols
        if renderer.type() == 'singleSymbol':
            symbol = renderer.symbol()
            carto_css = self.symbol2CartoCSS(layer, symbol, '#' + layer.tableName())
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
                    style_name = '#{}[{}={}]'.format(layer.tableName(), renderer.classAttribute(), value).decode('utf8')
                    carto_css = carto_css + \
                        self.symbol2CartoCSS(layer, symbol, style_name)
                else:
                    carto_css = self.symbol2CartoCSS(layer, symbol, '#' + layer.tableName()) + carto_css
        # CSS for graduated symbols
        elif renderer.type() == 'graduatedSymbol':
            # qDebug('Graduated')
            def upperValue(ran):
                """Get upper value from range"""
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
                carto_css = carto_css + \
                    self.symbol2CartoCSS(layer, symbol, '#' + layer.tableName() + \
                    '[' + renderer.classAttribute() + '<=' + str(ran.upperValue()) + ']')

        return '/** Styles designed from QGISCartoDB Plugin */\n\n' + carto_css + '\n' + label_css

    def symbol2CartoCSS(self, layer, symbol, styleName):
        # pylint: disable-msg=R0914,R0912,R0915
        """Convert QGIS symbol to cartoCSS"""
        carto_css = ''
        layer_opacity = str(float((100.0 - layer.layerTransparency())/100.0))

        blend_mode = layer.featureBlendMode()
        composition_mode = 'src-over'
        if blend_mode == QPainter.CompositionMode_Lighten:
            composition_mode = 'lighten'
        elif blend_mode == QPainter.CompositionMode_Screen:
            composition_mode = 'screen'
        elif blend_mode == QPainter.CompositionMode_ColorDodge:
            composition_mode = 'color-dodge'
        elif blend_mode == QPainter.CompositionMode_Plus:
            composition_mode = 'plus'
        elif blend_mode == QPainter.CompositionMode_Darken:
            composition_mode = 'darken'
        elif blend_mode == QPainter.CompositionMode_Multiply:
            composition_mode = 'multiply'
        elif blend_mode == QPainter.CompositionMode_ColorBurn:
            composition_mode = 'color-burn'
        elif blend_mode == QPainter.CompositionMode_Overlay:
            composition_mode = 'overlay'
        elif blend_mode == QPainter.CompositionMode_SoftLight:
            composition_mode = 'soft-light'
        elif blend_mode == QPainter.CompositionMode_HardLight:
            composition_mode = 'hard-light'
        elif blend_mode == QPainter.CompositionMode_Difference:
            composition_mode = 'difference'
        elif blend_mode == QPainter.CompositionMode_Exclusion:
            composition_mode = 'exclusion'

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
                        'opacity': layer_opacity,
                        'borderColor': lyr.outlineColor().name(),
                        'borderWidth': round(3.7795275552 * lyr.outlineWidth(), 0),
                        'markerCompOp': composition_mode
                    }
                    filein = open(QgisCartoDB.CartoDBPlugin.PLUGIN_DIR + '/templates/simplepoint.less')
                elif layer.geometryType() == QGis.Line:
                    line_width = round(3.7795275552 * lyr.width(), 0)
                    if lyr.penStyle() == Qt.NoPen:
                        line_width = 0

                    d = {
                        'layername': styleName,
                        'lineColor': lyr.color().name(),
                        'lineWidth': line_width,
                        'opacity': layer_opacity,
                        'lineCompOp': composition_mode,
                        'lineJoin': getLineJoin(lyr),
                        'lineDasharray': getLineDasharray(lyr.penStyle(), line_width)
                    }
                    filein = open(QgisCartoDB.CartoDBPlugin.PLUGIN_DIR + '/templates/simpleline.less')
                elif layer.geometryType() == QGis.Polygon:
                    border_width = round(3.7795275552 * lyr.borderWidth(), 0)
                    if lyr.borderStyle() == Qt.NoPen:
                        border_width = 0

                    d = {
                        'layername': styleName,
                        'fillColor': lyr.fillColor().name(),
                        'opacity': layer_opacity,
                        'borderColor': lyr.outlineColor().name(),
                        'borderWidth': border_width,
                        'polygonCompOp': composition_mode,
                        'lineJoin': getLineJoin(lyr),
                        'lineDasharray': getLineDasharray(lyr.borderStyle(), border_width)
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
                        'markerCompOp': composition_mode
                    }
                    filein = open(QgisCartoDB.CartoDBPlugin.PLUGIN_DIR + '/templates/defaultpoint.less')
                elif layer.geometryType() == QGis.Line:
                    d = {
                        'layername': styleName,
                        'lineColor': QColor(r, g, b, 255).name(),
                        'lineCompOp': composition_mode,
                    }
                    filein = open(QgisCartoDB.CartoDBPlugin.PLUGIN_DIR + '/templates/defaultline.less')
                elif layer.geometryType() == QGis.Polygon:
                    d = {
                        'layername': styleName,
                        'fillColor': QColor(r, g, b, 255).name(),
                        'polygonCompOp': composition_mode,
                    }
                    filein = open(QgisCartoDB.CartoDBPlugin.PLUGIN_DIR + '/templates/defaultpolygon.less')

        carto_css = Template(filein.read())
        carto_css = carto_css.substitute(
            d,
            input_encoding='utf-8',
            output_encoding='utf-8',
            encoding_errors='replace'
        )
        return carto_css

    def validateButtons(self):
        """Validate save button"""
        enabled = self.ui.mapNameTX.text() != '' # and self.ui.mapList.count() > 0
        self.ui.saveBT.setEnabled(enabled)
