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
 This script initializes the plugin, making it known to QGIS.
"""
# Import the PyQt and QGIS libraries
from PyQt4.QtCore import Qt, QCoreApplication, QObject, QSettings, QTranslator, qDebug, qVersion
from PyQt4.QtGui import QMenu, QIcon, QAction, QProgressBar

from qgis.core import QgsMessageLog, QgsPluginLayerRegistry, QgsMapLayerRegistry
from osgeo import gdal
from osgeo import ogr

import resources

from QgisCartoDB.dialogs import CartoDBPluginUpload, CartoDBPluginDialog, CartoDBNewSQLDialog, CartoDBPluginCreateViz
from QgisCartoDB.dialogs.ConnectionManager import CartoDBConnectionsManager
from QgisCartoDB.layers import CartoDBLayer, CartoDBPluginLayer, CartoDBPluginLayerType, CartoDBLayerWorker
from QgisCartoDB.toolbars import CartoDBToolbar
from QgisCartoDB.utils import CartoDBPluginWorker

import os.path
import shutil

"""
Class CartoDBPlugin

Main plugin class.
"""
class CartoDBPlugin(QObject):
    # initialize plugin directory
    PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))

    def __init__(self, iface):
        QObject.__init__(self)
        QgsMessageLog.logMessage('GDAL Version: ' + str(gdal.VersionInfo('VERSION_NUM')), 'CartoDB Plugin', QgsMessageLog.INFO)

        # Save reference to the QGIS interface
        self.iface = iface

        # initialize locale
        locale = QSettings().value("locale/userLocale")[0:2]
        localePath = os.path.join(CartoDBPlugin.PLUGIN_DIR, "i18n", "{}.qm".format(locale))

        if os.path.exists(localePath):
            self.translator = QTranslator()
            self.translator.load(localePath)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

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
        self.countLoadingLayers = 0
        self.countLoadedLayers = 0

        self._cdbMenu = None
        self._mainAction = None
        self._loadDataAction = None
        self._createVizAction = None
        self._addSQLAction = None
        self.toolbar = CartoDBToolbar()
        self._toolbarAction = None
        self._menu = None

    def initGui(self):
        self._cdbMenu = QMenu("CartoDB plugin", self.iface.mainWindow())
        self._cdbMenu.setIcon(QIcon(":/plugins/qgis-cartodb/images/icon.png"))
        self._mainAction = QAction(self.tr('Add CartoDB Layer'), self.iface.mainWindow())
        self._mainAction.setIcon(QIcon(":/plugins/qgis-cartodb/images/icons/add.png"))
        self._loadDataAction = QAction(self.tr('Upload layers to CartoDB'), self.iface.mainWindow())
        self._loadDataAction.setIcon(QIcon(":/plugins/qgis-cartodb/images/icons/upload.png"))
        self._createVizAction = QAction(self.tr('Create New Map'), self.iface.mainWindow())
        self._createVizAction.setIcon(QIcon(":/plugins/qgis-cartodb/images/icons/map.png"))
        self._addSQLAction = QAction(self.tr('Add SQL CartoDB Layer'), self.iface.mainWindow())
        self._addSQLAction.setIcon(QIcon(":/plugins/qgis-cartodb/images/icons/sql.png"))

        self.toolbar.setClick(self.connectionManager)
        self.toolbar.error.connect(self.toolbarError)
        self._toolbarAction = self.iface.addWebToolBarWidget(self.toolbar)
        worker = CartoDBPluginWorker(self.toolbar, 'connectCartoDB')
        worker.start()

        if not self.toolbar.isCurrentUserValid():
            self._mainAction.setEnabled(False)
            self._loadDataAction.setEnabled(False)
            self._createVizAction.setEnabled(False)
            self._addSQLAction.setEnabled(False)

        self._mainAction.triggered.connect(self.run)
        self._loadDataAction.triggered.connect(self.upload)
        self._createVizAction.triggered.connect(self.createNewMap)
        self._addSQLAction.triggered.connect(self.addSQL)

        self._cdbMenu.addAction(self._mainAction)
        self._cdbMenu.addAction(self._loadDataAction)
        self._cdbMenu.addAction(self._createVizAction)
        self._cdbMenu.addAction(self._addSQLAction)
        try:
            self.iface.layerToolBar().addAction(self._mainAction)
        except:
            self.iface.addWebToolBarIcon(self._mainAction)
        self.iface.addWebToolBarIcon(self._loadDataAction)
        self.iface.addWebToolBarIcon(self._createVizAction)
        try:
            self.iface.layerToolBar().addAction(self._addSQLAction)
        except:
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
        self.iface.removeWebToolBarIcon(self._loadDataAction)
        self.iface.removeWebToolBarIcon(self._createVizAction)
        self.iface.removeWebToolBarIcon(self._addSQLAction)
        self.iface.webMenu().removeAction(self._cdbMenu.menuAction())
        self.iface.removeWebToolBarIcon(self._toolbarAction)

        # Unregister plugin layer type
        QgsPluginLayerRegistry.instance().removePluginLayerType(CartoDBPluginLayer.LAYER_TYPE)

    def connectionManager(self):
        dlg = CartoDBConnectionsManager()
        dlg.notfoundconnections.connect(self.connectionsNotFound)
        dlg.deleteconnetion.connect(self.onDeleteUser)
        dlg.show()

        result = dlg.exec_()
        if result == 1 and dlg.currentUser is not None and dlg.currentApiKey is not None:
            self.toolbar.setUserCredentials(dlg.currentUser, dlg.currentApiKey, dlg.currentMultiuser)
            self._mainAction.setEnabled(True)
            self._loadDataAction.setEnabled(True)
            self._createVizAction.setEnabled(True)
            self._addSQLAction.setEnabled(True)

    def connectionsNotFound(self):
        self.toolbarError("")
        self.toolbar.reset()

    def onDeleteUser(self, user):
        if self.toolbar.currentUser == user:
            self.toolbar.setConnectText()

    def toolbarError(self, error):
        self._mainAction.setEnabled(False)
        self._loadDataAction.setEnabled(False)
        self._createVizAction.setEnabled(False)
        self._addSQLAction.setEnabled(False)

    def run(self):
        # Create and show the dialog
        dlg = CartoDBPluginDialog(self.toolbar)
        dlg.show()

        result = dlg.exec_()
        # See if OK was pressed
        if result == 1 and dlg.currentUser is not None and dlg.currentApiKey is not None:
            selectedItems = dlg.getTablesListSelectedItems()
            countLayers = len(selectedItems)
            self.countLoadingLayers = self.countLoadingLayers + countLayers
            if countLayers > 0:
                self.progressMessageBar, self.progress = self.addLoadingMsg(self.countLoadingLayers)
                self.iface.messageBar().pushWidget(self.progressMessageBar, self.iface.messageBar().INFO)
                self.iface.mainWindow().statusBar().showMessage(self.tr('Processed {} %').format(0))
                for i, table in enumerate(selectedItems):
                    widget = dlg.getItemWidget(table)
                    worker = CartoDBLayerWorker(self.iface, widget.tableName, widget.tableOwner, dlg,
                                                filterByExtent=dlg.filterByExtent(), readonly=widget.readonly,
                                                multiuser=widget.multiuser)
                    worker.finished.connect(self.addLayer)
                    self.worker = worker
                    worker.load()
        elif dlg.loadSQL:
            self.addSQL()


    def addLayer(self, layer):
        try:
            self.worker.deleteLater()
        except Exception, e:
            pass

        self.countLoadedLayers = self.countLoadedLayers + 1

        if layer.readonly:
            self.iface.messageBar().pushMessage(self.tr('Warning'),
                                                self.tr('Layer {}  is loaded in readonly mode').format(layer.layerName),
                                                level=self.iface.messageBar().WARNING, duration=5)
        QgsMapLayerRegistry.instance().addMapLayer(layer)
        self.layers.append(layer)
        self.progressMessageBar.setText(str(self.countLoadedLayers) + '/' + str(self.countLoadingLayers))
        percent = self.countLoadedLayers / float(self.countLoadingLayers) * 100
        self.iface.mainWindow().statusBar().showMessage(self.tr('Processed {}% - Loaded: {}').format(int(percent), layer.cartoTable))
        self.progress.setValue(self.countLoadedLayers)
        if self.countLoadedLayers == self.countLoadingLayers:
            self.iface.mainWindow().statusBar().clearMessage()
            self.iface.messageBar().popWidget(self.progressMessageBar)
            self.countLoadedLayers = 0
            self.countLoadingLayers = 0

    def addSQL(self):
        # Create and show the dialog
        dlg = CartoDBNewSQLDialog(self.toolbar)
        dlg.show()

        result = dlg.exec_()
        if result == 1 and dlg.currentUser is not None and dlg.currentApiKey is not None:
            sql = dlg.getQuery()
            progressMessageBar, progress = self.addLoadingMsg(1)
            QgsMessageLog.logMessage('SQL: ' + sql, 'CartoDB Plugin', QgsMessageLog.INFO)
            layer = CartoDBLayer(self.iface, 'SQLQuery', dlg.currentUser, dlg.currentApiKey, sql=sql, isSQL=True)
            QgsMapLayerRegistry.instance().addMapLayer(layer)
            self.layers.append(layer)
            progress.setValue(1)
            self.iface.mainWindow().statusBar().clearMessage()
            self.iface.messageBar().popWidget(progressMessageBar)

    def upload(self):
        dlg = CartoDBPluginUpload(self.iface, self.toolbar)
        def addLayer(fileName, tableName):
            newLayer = CartoDBLayer(self.iface, tableName, dlg.currentUser, dlg.currentApiKey,
                             dlg.currentUser, None, spatiaLite=fileName, multiuser=dlg.currentMultiuser)
            QgsMapLayerRegistry.instance().addMapLayer(newLayer)
            self.layers.append(newLayer)

        dlg.addedLayer.connect(addLayer)
        dlg.show()
        dlg.exec_()

    def createNewMap(self):
        dlg = CartoDBPluginCreateViz(self.toolbar, self.iface)
        dlg.show()
        dlg.exec_()

    def addLoadingMsg(self, countLayers, barText='Downloading datasets'):
        barText = self.tr(barText)
        progressMessageBar = self.iface.messageBar().createMessage(barText, '0/' + str(countLayers))
        progress = QProgressBar()
        progress.setMaximum(countLayers)
        progress.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        progressMessageBar.layout().addWidget(progress)
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
