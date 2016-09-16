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

from PyQt4.QtCore import pyqtSlot, qDebug
from PyQt4.QtGui import QApplication, QDialog, QSizePolicy, QColor, QTreeWidgetItem, QIcon, QMessageBox
from PyQt4.Qsci import QsciScintilla, QsciScintillaBase, QsciLexerSQL, QsciAPIs

from qgis.core import QgsMessageLog
from qgis.gui import QgsMessageBar

from QgisCartoDB.cartodb import CartoDBAPIKey, CartoDBException
from QgisCartoDB.dialogs.UserData import CartoDBUserDataDialog
from QgisCartoDB.ui.NewSQL import Ui_NewSQL
from QgisCartoDB.utils import CartoDBPluginWorker

from urllib import urlopen

import json
import QgisCartoDB.resources


class CartoDBNewSQLDialog(CartoDBUserDataDialog):
    def __init__(self, toolbar, parent=None):
        CartoDBUserDataDialog.__init__(self, toolbar, parent)

        self.ui = Ui_NewSQL()
        self.ui.setupUi(self)
        self._initEditor()

        self.ui.bar = QgsMessageBar()
        self.ui.bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.ui.verticalLayout.insertWidget(0, self.ui.bar)

        self.ui.testBT.clicked.connect(self.testQuery)

        self.ui.cancelBT.clicked.connect(self.reject)
        self.ui.addLayerBT.clicked.connect(self.accept)

        self.initUserConnection()

    def _initEditor(self):
        self.ui.sqlEditor = QsciScintilla(self)
        self.ui.sqlEditor.textChanged.connect(self.setValidQuery)
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

        ''' TODO autocomplete.
        api = QsciAPIs(lexer)
        api.add('aLongString')
        api.add('aLongerString')
        api.add('aDifferentString')
        api.add('sOmethingElse')
        api.prepare()

        self.ui.sqlEditor.setAutoCompletionThreshold(1)
        self.ui.sqlEditor.setAutoCompletionSource(QsciScintilla.AcsAPIs)
        '''

        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.ui.sqlEditor.sizePolicy().hasHeightForWidth())
        self.ui.sqlEditor.setSizePolicy(sizePolicy)

        self.ui.splitter.setSizes([self.size().width() * 0.6, self.size().height() * 0.4])
        self.ui.leftContainer.insertWidget(1, self.ui.sqlEditor)

    def setTablesListItems(self, tables):
        self.ui.tablesTree.clear()
        self.ui.tablesTree.addTopLevelItems(tables)
        return True

    def getTablesListSelectedItems(self):
        return []   # self.ui.tablesTree.selectedItems()

    @pyqtSlot()
    def findTables(self):
        self.ui.testBT.setEnabled(True)

        cl = CartoDBAPIKey(self.currentApiKey, self.currentUser)
        try:
            if not str(self.currentMultiuser) in ['true', '1', 'True']:
                sqlTables = "SELECT CDB_UserTables() table_name"
                res = cl.sql(
                    "WITH usertables AS (" + sqlTables + ") \
                        SELECT ut.table_name, c.column_name, c.data_type column_type \
                          FROM usertables ut \
                          JOIN information_schema.columns c ON c.table_name = ut.table_name \
                        WHERE c.data_type != 'USER-DEFINED' \
                        ORDER BY ut.table_name, c.column_name")
            else:
                sqlTables = "SELECT string_agg(privilege_type, ', ') AS privileges, table_schema, table_name \
                                FROM information_schema.role_table_grants tg \
                                JOIN ( \
                                    SELECT DISTINCT u.usename \
                                    FROM information_schema.tables t \
                                    JOIN pg_catalog.pg_class c ON (t.table_name = c.relname) \
                                    JOIN pg_catalog.pg_user u ON (c.relowner = u.usesysid) \
                                    WHERE t.table_schema = '" + self.currentUser + "') u ON u.usename = tg.grantee \
                            WHERE table_schema NOT IN ('pg_catalog', 'information_schema', 'cartodb', 'public', 'cdb_importer') \
                            GROUP BY table_schema, table_name \
                            ORDER BY table_schema, table_name"
                res = cl.sql(
                    "WITH usertables AS (" + sqlTables + ") \
                     SELECT ut.table_name, c.column_name, c.data_type column_type, ut.privileges \
                        FROM usertables ut \
                        JOIN information_schema.columns c ON c.table_name = ut.table_name \
                     WHERE c.data_type != 'USER-DEFINED' \
                     ORDER BY ut.table_name, c.column_name")

            tables = []
            oldTableName = None
            parentTableItem = None
            for table in res['rows']:

                if table['table_name'] != oldTableName:
                    parentTableItem = QTreeWidgetItem()
                    oldTableName = table['table_name']
                    parentTableItem.setText(0, self.tr(oldTableName))
                    parentTableItem.setIcon(0, QIcon(":/plugins/qgis-cartodb/images/icons/layers.png"))
                    if str(self.currentMultiuser) in ['true', '1', 'True'] and table['privileges'] == 'SELECT':
                        parentTableItem.setTextColor(0, QColor('#999999'))
                    tables.append(parentTableItem)

                tableItem = QTreeWidgetItem(parentTableItem)
                tableItem.setText(0, self.tr(table['column_name']))
                if str(self.currentMultiuser) in ['true', '1', 'True'] and table['privileges'] == 'SELECT':
                    tableItem.setTextColor(0, QColor('#999999'))
                tableItem.setToolTip(0, self.tr(table['column_type']))
                tableItem.setIcon(0, QIcon(":/plugins/qgis-cartodb/images/icons/text.png"))
                if table['column_type'] == 'integer' or table['column_type'] == 'double precision':
                    tableItem.setIcon(0, QIcon(":/plugins/qgis-cartodb/images/icons/number.png"))
                elif table['column_type'] == 'timestamp with time zone':
                    tableItem.setIcon(0, QIcon(":/plugins/qgis-cartodb/images/icons/calendar.png"))
            self.setTablesListItems(tables)
        except CartoDBException as e:
            QgsMessageLog.logMessage('Some error ocurred getting tables: ' + str(e.args), 'CartoDB Plugin', QgsMessageLog.CRITICAL)
            QMessageBox.information(self, QApplication.translate('CartoDBPlugin', 'Error'), QApplication.translate('CartoDBPlugin', 'Error getting tables'), QMessageBox.Ok)
            self.ui.tablesTree.clear()

    def testQuery(self):
        self.ui.bar.clearWidgets()
        self.ui.bar.pushMessage("Info", QApplication.translate('CartoDBPlugin', 'Validating Query'), level=QgsMessageBar.INFO)
        sql = self.ui.sqlEditor.text()

        if sql is None or sql == '':
            self.ui.bar.clearWidgets()
            self.ui.bar.pushMessage("Warning", "Please write the sql query", level=QgsMessageBar.WARNING, duration=5)
            self.setValidQuery(False)
            return

        sql = 'SELECT count(cartodb_id) num, ST_Union(the_geom) the_geom FROM (' + sql + ') a'
        cartoUrl = 'http://{}.carto.com/api/v2/sql?format=GeoJSON&q={}&api_key={}'.format(self.currentUser, sql, self.currentApiKey)
        response = urlopen(cartoUrl)
        result = json.loads(response.read())

        self.ui.bar.clearWidgets()
        if 'error' not in result:
            self.ui.bar.pushMessage("Info", QApplication.translate('CartoDBPlugin', 'Query is valid'), level=QgsMessageBar.INFO, duration=5)
            self.setValidQuery(True)
        else:
            if 'hint' in result:
                self.ui.bar.pushMessage("Warning", result['hint'], level=QgsMessageBar.WARNING, duration=10)
            for error in result['error']:
                self.ui.bar.pushMessage("Error", error, level=QgsMessageBar.CRITICAL, duration=5)
            self.setValidQuery(False)

    def setValidQuery(self, valid=False):
        self.ui.addLayerBT.setEnabled(valid)

    def getQuery(self):
        return self.ui.sqlEditor.text()

    def showEvent(self, event):
        worker = CartoDBPluginWorker(self, 'findTables')
        worker.start()
