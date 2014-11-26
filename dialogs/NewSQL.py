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
from PyQt4.QtGui import QDialog, QSizePolicy, QColor
from PyQt4.Qsci import QsciScintilla, QsciScintillaBase, QsciLexerSQL

from qgis.core import QgsMessageLog

from QgisCartoDB.cartodb import CartoDBAPIKey, CartoDBException
from QgisCartoDB.ui.NewSQL import Ui_NewSQL
from QgisCartoDB.dialogs.ConnectionsManager import CartoDBConnectionsManager
from QgisCartoDB.dialogs.NewConnection import CartoDBNewConnectionDialog


class CartoDBNewSQLDialog(CartoDBConnectionsManager):
    def __init__(self):
        CartoDBConnectionsManager.__init__(self)
        self.settings = QSettings()
        self.ui = Ui_NewSQL()
        self.ui.setupUi(self)
        self._initEditor()
        self.populateConnectionList()

        self.ui.newConnectionBT.clicked.connect(self.openNewConnectionDialog)
        self.ui.editConnectionBT.clicked.connect(self.editConnectionDialog)
        self.ui.deleteConnectionBT.clicked.connect(self.deleteConnectionDialog)
        self.ui.loadTableBT.clicked.connect(self.findTables)

        self.ui.cancelBT.clicked.connect(self.reject)
        self.ui.addLayerBT.clicked.connect(self.accept)

    def _initEditor(self):
        self.ui.sqlEditor = QsciScintilla(self)
        # Don't want to see the horizontal scrollbar at all
        self.ui.sqlEditor.SendScintilla(QsciScintilla.SCI_SETHSCROLLBAR, 0)

        self.ui.sqlEditor.setMarginLineNumbers(0, True)
        self.ui.sqlEditor.setMarginWidth(0, "000")
        self.ui.sqlEditor.setMarginsForegroundColor(QColor("#2468A7"))

        # Brace matching: enable for a brace immediately before or after
        # the current position.
        self.ui.sqlEditor.setBraceMatching(QsciScintilla.SloppyBraceMatch)

        # Current line visible with special background color
        self.ui.sqlEditor.setCaretLineVisible(True)
        self.ui.sqlEditor.setCaretLineBackgroundColor(QColor("#E4EEFF"))

        lexer = QsciLexerSQL()
        self.ui.sqlEditor.setLexer(lexer)

        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.ui.sqlEditor.sizePolicy().hasHeightForWidth())
        self.ui.sqlEditor.setSizePolicy(sizePolicy)

        self.ui.splitter.setSizes([self.size().width() * 0.6, self.size().height() * 0.4])
        self.ui.leftContainer.insertWidget(1, self.ui.sqlEditor)

    def setTablesListItems(self, tables):
        self.ui.tablesList.clear()
        self.ui.tablesList.addItems(tables)
        return True

    def getTablesListSelectedItems(self):
        return self.ui.tablesList.selectedItems()

    def findTables(self):
        # Get tables from CartoDB.
        self.currentUser = self.ui.connectionList.currentText()
        self.currentApiKey = self.settings.value('/CartoDBPlugin/%s/api' % self.currentUser)

        cl = CartoDBAPIKey(self.currentApiKey, self.currentUser)

        try:
            res = cl.sql("SELECT CDB_UserTables() order by 1")
            tables = []
            for table in res['rows']:
                tables.append(table['cdb_usertables'])
            QgsMessageLog.logMessage('This account has ' + str(len(tables)) + ' tables', 'CartoDB Plugin', QgsMessageLog.INFO)
            self.setTablesListItems(tables)
            self.settings.setValue('/CartoDBPlugin/selected', self.currentUser)
        except CartoDBException as e:
            QgsMessageLog.logMessage('Some error ocurred getting tables', 'CartoDB Plugin', QgsMessageLog.CRITICAL)
            QMessageBox.information(self, self.tr('Error'), self.tr('Error getting tables'), QMessageBox.Ok)
            self.ui.tablesList.clear()

    def setConnectionsFound(self, found):
        self.ui.loadTableBT.setEnabled(found)
        self.ui.deleteConnectionBT.setEnabled(found)
        self.ui.editConnectionBT.setEnabled(found)
