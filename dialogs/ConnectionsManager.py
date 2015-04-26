"""
/***************************************************************************
CartoDB Plugin
A QGIS plugin

----------------------------------------------------------------------------
begin                : 2014-11-26
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
from PyQt4.QtGui import QDialog, QMessageBox

from qgis.core import QgsMessageLog

from QgisCartoDB.dialogs.NewConnection import CartoDBNewConnectionDialog


# Create the dialog for CartoDBPlugin
class CartoDBConnectionsManager(QDialog):
    def __init__(self):
        QDialog.__init__(self)

    def populateConnectionList(self):
        # Populate connections saved.
        self.settings.beginGroup('/CartoDBPlugin/')
        self.ui.connectionList.clear()
        self.ui.connectionList.addItems(self.settings.childGroups())
        self.settings.endGroup()
        self.setConnectionListPosition()

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
        multiuser = self.settings.value('/CartoDBPlugin/%s/multiuser' % currentText, False)
        QgsMessageLog.logMessage('Multiuser:' + str(multiuser) + ' - ' + str(bool(multiuser)), 'CartoDB Plugin', QgsMessageLog.INFO)

        conEdit = CartoDBNewConnectionDialog(currentText)
        conEdit.setWindowTitle(self.tr('Edit CartoDB Connection'))
        conEdit.ui.userTX.setText(currentText)
        conEdit.ui.apiKeyTX.setText(apiKey)
        conEdit.ui.multiuserCH.setChecked(str(multiuser) in ['true', '1', 'True'])
        result = conEdit.exec_()

        if result == QDialog.Accepted:
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
