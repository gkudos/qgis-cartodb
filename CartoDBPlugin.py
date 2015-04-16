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
from osgeo import gdal
from osgeo import ogr
import resources

from cartodb import CartoDBAPIKey, CartoDBException
from QgisCartoDB.dialogs.Main import CartoDBPluginDialog
from QgisCartoDB.dialogs.NewSQL import CartoDBNewSQLDialog
from CartoDBPluginLayer import CartoDBPluginLayer
from CartoDBPluginLayerType import CartoDBPluginLayerType

import os.path
import shutil

from urllib import urlopen


class CartoDBPlugin(QObject):

    def __init__(self, iface):
        super(QObject, self).__init__()
        qDebug('Probando q debug')
        QgsMessageLog.logMessage('GDAL Version: ' + str(gdal.VersionInfo('VERSION_NUM')), 'CartoDB Plugin', QgsMessageLog.INFO)

        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(os.path.abspath(__file__))

        # SQLite available?
        driverName = "SQLite"
        self.sqLiteDrv = ogr.GetDriverByName(driverName)
        if self.sqLiteDrv is None:
            QgsMessageLog.logMessage('SQLite driver not found', 'CartoDB Plugin', QgsMessageLog.CRITICAL)
        else:
            QgsMessageLog.logMessage('SQLite driver is found', 'CartoDB Plugin', QgsMessageLog.INFO)
            # orDS = self.sqLiteDrv.Open(self.plugin_dir + '/db/init_database.sqlite')
            # options=['SPATIALITE=YES']
            self.databasePath = self.plugin_dir + '/db/database.sqlite'
            shutil.copyfile(self.plugin_dir + '/db/init_database.sqlite', self.databasePath)
            # self.datasource = self.sqLiteDrv.Open(self.plugin_dir + '/db/database.sqlite', True)
        self.layers = []

    def initGui(self):
        self._cdbMenu = QMenu("CartoDB plugin", self.iface.mainWindow())
        self._cdbMenu.setIcon(QIcon(":/plugins/qgis-cartodb/images/icon.png"))
        self._mainAction = QAction("Add CartoDB Layer", self.iface.mainWindow())
        self._mainAction.setIcon(QIcon(":/plugins/qgis-cartodb/images/add.png"))
        self._addSQLAction = QAction("Add SQL CartoDB Layer", self.iface.mainWindow())
        self._addSQLAction.setIcon(QIcon(":/plugins/qgis-cartodb/images/add_sql.png"))

        QObject.connect(self._mainAction, SIGNAL("activated()"), self.run)
        QObject.connect(self._addSQLAction, SIGNAL("activated()"), self.addSQL)

        self._cdbMenu.addAction(self._mainAction)
        self._cdbMenu.addAction(self._addSQLAction)
        self.iface.addWebToolBarIcon(self._mainAction)
        self.iface.addWebToolBarIcon(self._addSQLAction)

        # Create Web menu, if it doesn't exist yet
        tmpAction = QAction("Temporal", self.iface.mainWindow())
        self.iface.addPluginToWebMenu("_tmp", tmpAction)
        self._menu = self.iface.webMenu()
        self._menu.addMenu(self._cdbMenu)
        self.iface.removePluginWebMenu("_tmp", tmpAction)

        # Register plugin layer type
        QgsPluginLayerRegistry.instance().addPluginLayerType(CartoDBPluginLayerType())

    def unload(self):
        self.iface.removeWebToolBarIcon(self._mainAction)
        self.iface.removeWebToolBarIcon(self._addSQLAction)
        self.iface.webMenu().removeAction(self._cdbMenu.menuAction())
        # self.datasource.Destroy()
        # Unregister plugin layer type
        QgsPluginLayerRegistry.instance().removePluginLayerType(CartoDBPluginLayer.LAYER_TYPE)

    def run(self):
        # Create and show the dialog
        dlg = CartoDBPluginDialog()
        dlg.show()

        result = dlg.exec_()
        # See if OK was pressed
        if result == 1 and dlg.currentUser is not None and dlg.currentApiKey is not None:
            selectedItems = dlg.getTablesListSelectedItems()
            countLayers = len(selectedItems)
            if countLayers > 0:
                progressMessageBar, progress = self.addLoadingMsg(countLayers)
                for i, table in enumerate(selectedItems):
                    layer = CartoDBPluginLayer(self.iface, table.text(), dlg.currentUser, dlg.currentApiKey)

                    if layer.readOnly:
                        self.iface.messageBar().pushMessage("Warning", 'Layer ' + layer.layerName + ' is loaded in readonly mode',
                                                            level=self.iface.messageBar().WARNING, duration=5)
                    QgsMapLayerRegistry.instance().addMapLayer(layer)
                    self.layers.append(layer)
                    percent = i / float(countLayers) * 100
                    self.iface.mainWindow().statusBar().showMessage("Processed {} %".format(int(percent)))
                    progress.setValue(i + 1)
                self.iface.mainWindow().statusBar().clearMessage()
                self.iface.messageBar().popWidget(progressMessageBar)

    def addSQL(self):
        # Create and show the dialog
        dlg = CartoDBNewSQLDialog()
        dlg.show()

        result = dlg.exec_()
        if result == 1 and dlg.currentUser is not None and dlg.currentApiKey is not None:
            sql = dlg.getQuery()
            progressMessageBar, progress = self.addLoadingMsg(1)
            QgsMessageLog.logMessage('SQL: ' + sql, 'CartoDB Plugin', QgsMessageLog.INFO)
            layer = CartoDBPluginLayer(self.iface, 'SQLQuery', dlg.currentUser, dlg.currentApiKey, sql)
            QgsMapLayerRegistry.instance().addMapLayer(layer)
            self.layers.append(layer)
            progress.setValue(1)
            self.iface.mainWindow().statusBar().clearMessage()
            self.iface.messageBar().popWidget(progressMessageBar)

    def addLoadingMsg(self, countLayers):
        progressMessageBar = self.iface.messageBar().createMessage("Loading layers...")
        progress = QProgressBar()
        progress.setMaximum(countLayers)
        progress.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        progressMessageBar.layout().addWidget(progress)
        self.iface.messageBar().pushWidget(progressMessageBar, self.iface.messageBar().INFO)
        return progressMessageBar, progress
