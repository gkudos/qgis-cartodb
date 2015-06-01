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

from qgis.core import *

from QgisCartoDB.layers import CartoDBLayer


class CartoDBPluginLayer(QgsPluginLayer):
    LAYER_TYPE = "cartodb"

    def __init__(self, iface, createCB):
        QgsPluginLayer.__init__(self, CartoDBPluginLayer.LAYER_TYPE, "CartoDB Layer")
        self.settings = QSettings()
        self.cartodbLayer = None;
        self.iface = iface
        self.createCB = createCB
        self.setValid(True)

    def readXml(self, node):
        element = node.toElement()
        qDebug('ReadXML CartoDB Plugin Layer: ' + str(element.namedItem('customproperties').nodeName()))

        cartoName = ''
        tableName = ''
        props = element.namedItem('customproperties').childNodes()
        for i in range(0, props.count()):
            prop = props.item(i).toElement()
            if prop.nodeName() == 'property':
                if prop.attribute('key') == 'cartoName':
                    cartoName = prop.attribute('value')
                elif prop.attribute('key') == 'tableName':
                    tableName = prop.attribute('value')

        qDebug('tableName: ' + tableName)
        qDebug('cartoName: ' + cartoName)

        if cartoName != '':
            apiKey = self.settings.value('/CartoDBPlugin/%s/api' % cartoName)
            qDebug('api: ' + apiKey)
            self.cartodbLayer = CartoDBLayer(self.iface, tableName, cartoName, apiKey)
            self.createCB(self)
        return True

    def writeXml(self, node, doc):
        qDebug('WriteXML CartoDB Plugin Layer: ' + str(node))
        return True

    def draw(self, rendererContext):
        return self.cartodbLayer.draw(rendererContext)
