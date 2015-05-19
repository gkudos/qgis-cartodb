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
from QgisCartoDB.dialogs.ConnectionManager import CartoDBConnectionsManager
from QgisCartoDB.layers import CartoDBLayer, CartoDBPluginLayer, CartoDBPluginLayerType, CartoDBLayerWorker
from QgisCartoDB.toolbars import CartoDBToolbar
from QgisCartoDB.utils import CartoDBPluginWorker

import os.path
import shutil

from urllib import urlopen


class CartoDBPlugin(QObject):
    # initialize plugin directory
    PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))

    def __init__(self, iface):
        super(QObject, self).__init__()
        QgsMessageLog.logMessage('GDAL Version: ' + str(gdal.VersionInfo('VERSION_NUM')), 'CartoDB Plugin', QgsMessageLog.INFO)

        # Save reference to the QGIS interface
        self.iface = iface

        # SQLite available?
        driverName = "SQLite"
        self.sqLiteDrv = ogr.GetDriverByName(driverName)
        if self.sqLiteDrv is None:
            QgsMessageLog.logMessage('SQLite driver not found', 'CartoDB Plugin', QgsMessageLog.CRITICAL)
        else:
            QgsMessageLog.logMessage('SQLite driver is found', 'CartoDB Plugin', QgsMessageLog.INFO)
            self.databasePath = CartoDBPlugin.PLUGIN_DIR + '/db/database.sqlite'
            shutil.copyfile(CartoDBPlugin.PLUGIN_DIR + '/db/init_database.sqlite', self.databasePath)
        self.layers = []

    def initGui(self):
        self._cdbMenu = QMenu("CartoDB plugin", self.iface.mainWindow())
        self._cdbMenu.setIcon(QIcon(":/plugins/qgis-cartodb/images/icon.png"))
        self._mainAction = QAction("Add CartoDB Layer", self.iface.mainWindow())
        self._mainAction.setIcon(QIcon(":/plugins/qgis-cartodb/images/add.png"))
        self._addSQLAction = QAction("Add SQL CartoDB Layer", self.iface.mainWindow())
        self._addSQLAction.setIcon(QIcon(":/plugins/qgis-cartodb/images/add_sql.png"))

        self.toolbar = CartoDBToolbar()
        self.toolbar.setClick(self.connectionManager)
        self._toolbarAction = self.iface.addWebToolBarWidget(self.toolbar)
        worker = CartoDBPluginWorker(self.toolbar, 'connectCartoDB')
        worker.start()

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
        self.pluginLayerType = CartoDBPluginLayerType(self.iface, self.createLayerCB)
        QgsPluginLayerRegistry.instance().addPluginLayerType(self.pluginLayerType)

    def unload(self):
        self.iface.removeWebToolBarIcon(self._mainAction)
        self.iface.removeWebToolBarIcon(self._addSQLAction)
        self.iface.webMenu().removeAction(self._cdbMenu.menuAction())
        self.iface.removeWebToolBarIcon(self._toolbarAction)
        # self.datasource.Destroy()

        # Unregister plugin layer type
        QgsPluginLayerRegistry.instance().removePluginLayerType(CartoDBPluginLayer.LAYER_TYPE)

    def connectionManager(self):
        dlg = CartoDBConnectionsManager()
        dlg.show()

        result = dlg.exec_()
        if result == 1 and dlg.currentUser is not None and dlg.currentApiKey is not None:
            self.toolbar.setUserCredentials(dlg.currentUser, dlg.currentApiKey, dlg.currentMultiuser)

    def run(self):
        # Create and show the dialog
        dlg = CartoDBPluginDialog(self.toolbar)
        dlg.show()

        result = dlg.exec_()
        # See if OK was pressed
        if result == 1 and dlg.currentUser is not None and dlg.currentApiKey is not None:
            selectedItems = dlg.getTablesListSelectedItems()
            countLayers = len(selectedItems)
            if countLayers > 0:
                progressMessageBar, self.progress = self.addLoadingMsg(countLayers)
                for i, table in enumerate(selectedItems):
                    worker = CartoDBLayerWorker(self.iface, table.text(), dlg, i)
                    worker.cartoDBLoaded.connect(self.addLayer)
                    worker.loadLayer()

                self.iface.mainWindow().statusBar().clearMessage()
                self.iface.messageBar().popWidget(progressMessageBar)

    def addLayer(self, layer, dlg, i):
        selectedItems = dlg.getTablesListSelectedItems()
        countLayers = len(selectedItems)
        if layer.readOnly:
            self.iface.messageBar().pushMessage("Warning", 'Layer ' + layer.layerName + ' is loaded in readonly mode',
                                                level=self.iface.messageBar().WARNING, duration=5)
        QgsMapLayerRegistry.instance().addMapLayer(layer)
        self.layers.append(layer)
        percent = i / float(countLayers) * 100
        self.iface.mainWindow().statusBar().showMessage("Processed {} %".format(int(percent)))
        self.progress.setValue(i + 1)

    def addSQL(self):
        # Create and show the dialog
        dlg = CartoDBNewSQLDialog()
        dlg.show()

        result = dlg.exec_()
        if result == 1 and dlg.currentUser is not None and dlg.currentApiKey is not None:
            sql = dlg.getQuery()
            progressMessageBar, progress = self.addLoadingMsg(1)
            QgsMessageLog.logMessage('SQL: ' + sql, 'CartoDB Plugin', QgsMessageLog.INFO)
            layer = CartoDBLayer(self.iface, 'SQLQuery', dlg.currentUser, dlg.currentApiKey, sql)
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

    def createLayerCB(self, layer):
        qDebug('Opening cartodb layer')
        lr = QgsMapLayerRegistry.instance()
        lr.layerWasAdded.connect(self._onAddProjectLayer)
        # lr.removeMapLayer(layer.id())
        # lr.addMapLayer(layer.cartodbLayer)
        self.layers.append(layer)

    def _onAddProjectLayer(self, ly):
        lr = QgsMapLayerRegistry.instance()
        lr.layerWasAdded.disconnect(self._onAddProjectLayer)
        qDebug('Layer id: ' + ly.id())
        qDebug('Cartodb Layer: ' + str(ly.cartodbLayer))
        # lr.removeMapLayer(ly.id())
        # lr.addMapLayer(ly.cartodbLayer)
