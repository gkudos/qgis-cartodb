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

from QgisCartoDB.ui.UI_CartoDBPlugin import Ui_CartoDBPlugin
from QgisCartoDB.dialogs.NewConnection import CartoDBNewConnectionDialog


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

        if self.ui.connectionList.count() == 0:
            self.ui.connectBT.setEnabled(False)
            self.ui.deleteConnectionBT.setEnabled(False)
            self.ui.editConnectionBT.setEnabled(False)

    def openNewConnectionDialog(self):
        dlg = CartoDBNewConnectionDialog()
        dlg.setWindowTitle(self.tr('Add CartoDB Connection'))

        dlg.show()
        result = dlg.exec_()

        # See if OK was pressed
        if result == QDialog.Accepted:  # add to service list
            QgsMessageLog.logMessage('New connection saved', 'CartoDB Plugin', QgsMessageLog.INFO)
            self.populateConnectionList()

    def editConnectionDialog(self):
        """modify existing connection"""

        current_text = self.ui.connectionList.currentText()
        api_key = self.settings.value('/CartoDBPlugin/%s/api' % current_text)

        conn_edit = CartoDBNewConnectionDialog(current_text)
        conn_edit.setWindowTitle(self.tr('Edit CartoDB Connection'))
        conn_edit.ui.userTX.setText(current_text)
        conn_edit.ui.apiKeyTX.setText(api_key)
        if conn_edit.exec_() == QDialog.Accepted:  # update service list
            self.populateConnectionList()

    def setConnectionListPosition(self):
        """set the current index to the selected connection"""
        to_select = self.settings.value('/CartoDBPlugin/selected')
        conn_count = self.ui.connectionList.count()

        """
        if conn_count == 0:
            self.btnDelete.setEnabled(False)
            self.btnServerInfo.setEnabled(False)
            self.btnEdit.setEnabled(False)
        """

        # does to_select exist in cmbConnectionsServices?
        exists = False
        for i in range(conn_count):
            if self.ui.connectionList.itemText(i) == to_select:
                self.ui.connectionList.setCurrentIndex(i)
                exists = True
                break

        # If we couldn't find the stored item, but there are some, default
        # to the last item (this makes some sense when deleting items as it
        # allows the user to repeatidly click on delete to remove a whole
        # lot of items)
        if not exists and conn_count > 0:
            # If to_select is null, then the selected connection wasn't found
            # by QSettings, which probably means that this is the first time
            # the user has used CSWClient, so default to the first in the list
            # of connetions. Otherwise default to the last.
            if not to_select:
                current_index = 0
            else:
                current_index = conn_count - 1

            self.ui.connectionList.setCurrentIndex(current_index)
