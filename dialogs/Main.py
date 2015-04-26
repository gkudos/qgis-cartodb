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
"""
from PyQt4.QtCore import QSettings
from PyQt4.QtGui import QDialog, QMessageBox, QListWidgetItem, QIcon

from qgis.core import QgsMessageLog

from QgisCartoDB.cartodb import CartoDBAPIKey, CartoDBException
from QgisCartoDB.dialogs.ConnectionsManager import CartoDBConnectionsManager
from QgisCartoDB.dialogs.NewConnection import CartoDBNewConnectionDialog
from QgisCartoDB.ui.UI_CartoDBPlugin import Ui_CartoDBPlugin

import QgisCartoDB.resources

import copy


# Create the dialog for CartoDBPlugin
class CartoDBPluginDialog(CartoDBConnectionsManager):
    def __init__(self):
        CartoDBConnectionsManager.__init__(self)
        self.settings = QSettings()
        # Set up the user interface from Designer.
        self.ui = Ui_CartoDBPlugin()
        self.ui.setupUi(self)
        self.populateConnectionList()
        self.ui.newConnectionBT.clicked.connect(self.openNewConnectionDialog)
        self.ui.editConnectionBT.clicked.connect(self.editConnectionDialog)
        self.ui.deleteConnectionBT.clicked.connect(self.deleteConnectionDialog)
        self.ui.connectBT.clicked.connect(self.findTables)
        self.ui.searchTX.textChanged.connect(self.filterTables)

        self.currentUser = None
        self.currentApiKey = None
        self.currentMultiuser = None

    def setTablesListItems(self, tables):
        self.ui.tablesList.clear()
        for item in tables:
            self.ui.tablesList.addItem(item)
        return True

    def getTablesListSelectedItems(self):
        return self.ui.tablesList.selectedItems()

    def findTables(self):
        # Get tables from CartoDB.
        self.currentUser = self.ui.connectionList.currentText()
        self.currentApiKey = self.settings.value('/CartoDBPlugin/%s/api' % self.currentUser)
        self.currentMultiuser = self.settings.value('/CartoDBPlugin/%s/multiuser' % self.currentUser, False)

        cl = CartoDBAPIKey(self.currentApiKey, self.currentUser)

        try:
            if not self.currentMultiuser:
                res = cl.sql("SELECT CDB_UserTables() order by 1")
            else:
                res = cl.sql(
                    "SELECT string_agg(privilege_type, ', ') AS privileges, table_schema, table_name as cdb_usertables \
                        FROM information_schema.role_table_grants tg \
                        JOIN ( \
                            SELECT DISTINCT u.usename \
                            FROM information_schema.tables t \
                            JOIN pg_catalog.pg_class c ON (t.table_name = c.relname) \
                            JOIN pg_catalog.pg_user u ON (c.relowner = u.usesysid) \
                            WHERE t.table_schema = '" + self.currentUser + "') u ON u.usename = tg.grantee \
                    WHERE table_schema NOT IN ('pg_catalog', 'information_schema', 'cartodb', 'public', 'cdb_importer') \
                    GROUP BY table_schema, table_name \
                    ORDER BY table_schema, table_name")

            self.tables = []
            items = []
            for table in res['rows']:
                item = QListWidgetItem()
                item.setText(table['cdb_usertables'])
                item.setIcon(QIcon(":/plugins/qgis-cartodb/images/icons/layers.png"))
                self.tables.append(table['cdb_usertables'])
                items.append(item)
            self.setTablesListItems(items)
            self.settings.setValue('/CartoDBPlugin/selected', self.currentUser)
            self.ui.searchTX.setEnabled(True)
        except CartoDBException as e:
            QgsMessageLog.logMessage('Some error ocurred getting tables', 'CartoDB Plugin', QgsMessageLog.CRITICAL)
            QMessageBox.information(self, self.tr('Error'), self.tr('Error getting tables'), QMessageBox.Ok)
            self.ui.tablesList.clear()
            self.ui.searchTX.setEnabled(False)

    def filterTables(self):
        text = self.ui.searchTX.text()
        if text == '':
            newTables = self.tables
        else:
            newTables = [t for t in self.tables if text in t]
        items = []
        for table in newTables:
            item = QListWidgetItem()
            item.setText(table)
            item.setIcon(QIcon(":/plugins/qgis-cartodb/images/icons/layers.png"))
            items.append(item)
        self.setTablesListItems(items)

    def setConnectionsFound(self, found):
        self.ui.connectBT.setEnabled(found)
        self.ui.deleteConnectionBT.setEnabled(found)
        self.ui.editConnectionBT.setEnabled(found)
