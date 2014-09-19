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
from PyQt4.QtGui import QDialog, QMessageBox

from qgis.core import QgsMessageLog

from QgisCartoDB.cartodb import CartoDBAPIKey, CartoDBException
from QgisCartoDB.dialogs.NewConnection import CartoDBNewConnectionDialog
from QgisCartoDB.ui.UI_CartoDBPlugin import Ui_CartoDBPlugin


# Create the dialog for CartoDBPlugin
class CartoDBPluginDialog(QDialog):
    def __init__(self):
        QDialog.__init__(self)
        self.settings = QSettings()
        # Set up the user interface from Designer.
        self.ui = Ui_CartoDBPlugin()
        self.ui.setupUi(self)
        self.populateConnectionList()
        self.ui.newConnectionBT.clicked.connect(self.openNewConnectionDialog)
        self.ui.editConnectionBT.clicked.connect(self.editConnectionDialog)
        self.ui.deleteConnectionBT.clicked.connect(self.deleteConnectionDialog)
        self.ui.connectBT.clicked.connect(self.findTables)

        self.currentUser = None
        self.currentApiKey = None

    def setTablesListItems(self, tables):
        self.ui.tablesList.clear()
        self.ui.tablesList.addItems(tables)
        return True

    def getTablesListSelectedItems(self):
        return self.ui.tablesList.selectedItems()

    def populateConnectionList(self):
        self.settings.beginGroup('/CartoDBPlugin/')
        self.ui.connectionList.clear()
        self.ui.connectionList.addItems(self.settings.childGroups())
        self.settings.endGroup()
        self.setConnectionListPosition()

    def openNewConnectionDialog(self):
        # Open new connection dialog.
        dlg = CartoDBNewConnectionDialog()
        dlg.setWindowTitle(self.tr('Add CartoDB Connection'))
        dlg.show()

        result = dlg.exec_()
        # See if OK was pressed
        if result == QDialog.Accepted:  # add to service list
            QgsMessageLog.logMessage('New connection saved', 'CartoDB Plugin', QgsMessageLog.INFO)
            self.populateConnectionList()

    def editConnectionDialog(self):
        # Modify existing connection.
        currentText = self.ui.connectionList.currentText()
        apiKey = self.settings.value('/CartoDBPlugin/%s/api' % currentText)

        conEdit = CartoDBNewConnectionDialog(currentText)
        conEdit.setWindowTitle(self.tr('Edit CartoDB Connection'))
        conEdit.ui.userTX.setText(currentText)
        conEdit.ui.apiKeyTX.setText(apiKey)
        if conEdit.exec_() == QDialog.Accepted:
            # Update connection list
            self.populateConnectionList()

    def deleteConnectionDialog(self):
        # Delete connection.
        currentText = self.ui.connectionList.currentText()
        key = '/CartoDBPlugin/%s' % currentText
        msg = self.tr('Remove connection %s?' % currentText)

        result = QMessageBox.information(self, self.tr('Confirm delete'), msg, QMessageBox.Ok | QMessageBox.Cancel)
        if result == QMessageBox.Ok:
            # Remove connection from list
            self.settings.remove(key)
            indexToDelete = self.ui.connectionList.currentIndex()
            self.ui.connectionList.removeItem(indexToDelete)
            self.setConnectionListPosition()

    def findTables(self):
        # Get tables from CartoDB.
        self.currentUser = self.ui.connectionList.currentText()
        self.currentApiKey = self.settings.value('/CartoDBPlugin/%s/api' % self.currentUser)

        cl = CartoDBAPIKey(self.currentApiKey, self.currentUser)

        try:
            res = cl.sql("SELECT * FROM pg_catalog.pg_tables WHERE tableowner != 'postgres' ORDER BY tablename")
            tables = []
            for table in res['rows']:
                tables.append(table['tablename'])
            QgsMessageLog.logMessage('This account has ' + str(len(tables)) + ' tables', 'CartoDB Plugin', QgsMessageLog.INFO)
            self.setTablesListItems(tables)
            self.settings.setValue('/CartoDBPlugin/selected', self.currentUser)
        except CartoDBException as e:
            QgsMessageLog.logMessage('Some error ocurred getting tables', 'CartoDB Plugin', QgsMessageLog.CRITICAL)
            QMessageBox.information(self, self.tr('Error'), self.tr('Error getting tables'), QMessageBox.Ok)
            self.ui.tablesList.clear()

    def setConnectionListPosition(self):
        # Set the current index to the selected connection.
        toSelect = self.settings.value('/CartoDBPlugin/selected')
        conCount = self.ui.connectionList.count()

        self.setConnectionsFound(conCount > 0)

        exists = False
        for i in range(conCount):
            if self.ui.connectionList.itemText(i) == toSelect:
                self.ui.connectionList.setCurrentIndex(i)
                exists = True
                break

        # If we couldn't find the stored item, but there are some, default
        # to the last item (this makes some sense when deleting items as it
        # allows the user to repeatidly click on delete to remove a whole
        # lot of items)
        if not exists and conCount > 0:
            # If toSelect is null, then the selected connection wasn't found
            # by QSettings, which probably means that this is the first time
            # the user has used CartoDBPlugin, so default to the first in the list
            # of connetions. Otherwise default to the last.
            if not toSelect:
                currentIndex = 0
            else:
                currentIndex = conCount - 1

            self.ui.connectionList.setCurrentIndex(currentIndex)

    def setConnectionsFound(self, found):
        self.ui.connectBT.setEnabled(found)
        self.ui.deleteConnectionBT.setEnabled(found)
        self.ui.editConnectionBT.setEnabled(found)
