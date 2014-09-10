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
 This script initializes the plugin, making it known to QGIS.
"""
# Import the PyQt and QGIS libraries
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
import resources

from cartodb import CartoDBAPIKey, CartoDBException
from CartoDBPluginDialog import CartoDBPluginDialog

import os.path

from urllib import urlopen


def openPublicReadonly(cartoName, tableName, apiKey):
    sql = 'SELECT * FROM ' + tableName
    cartoUrl = 'http://{}.cartodb.com/api/v2/sql?format=GeoJSON&q={}&api_key={}'.format(cartoName, sql, apiKey)
    response = urlopen(cartoUrl)
    content = response.read()
    layer = QgsVectorLayer(content, tableName, 'ogr')
    QgsMapLayerRegistry.instance().addMapLayer(layer)
    QgsVectorFileWriter.writeAsVectorFormat(layer, layer.name() + ".sqlite", "utf-8", layer.crs(), "SpatiaLite", False, None, ["SPATIALITE=YES"])


class CartoDBPlugin:

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(os.path.abspath(__file__))

    def initGui(self):
        self._cdbMenu = QMenu("CartoDB plugin", self.iface.mainWindow())
        self._cdbMenu.setIcon(QIcon(":/plugins/qgis-cartodb/images/icon.png"))
        self._mainAction = QAction("Add CartoDB Layer", self.iface.mainWindow())
        self._mainAction.setIcon(QIcon("%s/%s" % (self.plugin_dir, "images/icon.png")))
        QObject.connect(self._mainAction, SIGNAL("activated()"), self.run)

        self._cdbMenu.addAction(self._mainAction)
        self.iface.addToolBarIcon(self._mainAction)

        # Create Web menu, if it doesn't exist yet
        tmpAction = QAction("Temporal", self.iface.mainWindow())
        self.iface.addPluginToWebMenu("_tmp", tmpAction)
        self._menu = self.iface.webMenu()
        self._menu.addMenu(self._cdbMenu)
        self.iface.removePluginWebMenu("_tmp", tmpAction)

    def unload(self):
        self.iface.removeToolBarIcon(self._mainAction)
        self.iface.webMenu().removeAction(self._cdbMenu.menuAction())

    def run(self):
        # create and show the dialog
        dlg = CartoDBPluginDialog()

        QgsMessageLog.logMessage('Drivers: ' + str(QgsVectorFileWriter.ogrDriverList()), 'CartoDB Plugin', QgsMessageLog.INFO)

        apiKey = 'XXXXXXXXXXXXXXX'
        cartoDBDomain = 'XXXXXXXXXXXXXXXXX'
        cl = CartoDBAPIKey(apiKey, cartoDBDomain)

        try:
            res = cl.sql("SELECT * FROM pg_catalog.pg_tables WHERE tableowner != 'postgres' ORDER BY tablename")
            tables = []
            for table in res['rows']:
                tables.append(table['tablename'])
            QgsMessageLog.logMessage('Cantidad de tablas encontras: ' + str(len(tables)), 'CartoDB Plugin', QgsMessageLog.INFO)
            dlg.setTablesListItems(tables)
        except CartoDBException as e:
            QgsMessageLog.logMessage('Some error ocurred', 'CartoDB Plugin', QgsMessageLog.ERROR)

        # show the dialog
        dlg.show()
        result = dlg.exec_()

        # See if OK was pressed
        if result == 1:
            selectedItems = dlg.getTablesListSelectedItems()
            QgsMessageLog.logMessage('Tablas seleccionadas: ' + str(selectedItems), 'CartoDB Plugin', QgsMessageLog.INFO)
            if len(selectedItems) > 0:
                for table in selectedItems:
                    openPublicReadonly(cartoDBDomain, table.text(), apiKey)
