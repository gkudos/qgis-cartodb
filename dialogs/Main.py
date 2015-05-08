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
from PyQt4.QtCore import QSettings, QUrl, QEventLoop, pyqtSlot, Qt, qDebug
from PyQt4.QtGui import QDialog, QMessageBox, QListWidgetItem, QIcon, QColor, QImage, QPixmap, QImageReader
from PyQt4.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from qgis.core import QgsMessageLog

from QgisCartoDB.cartodb import CartoDBAPIKey, CartoDBException, CartoDBApi
from QgisCartoDB.dialogs.ConnectionsManager import CartoDBConnectionsManager
from QgisCartoDB.dialogs.NewConnection import CartoDBNewConnectionDialog
from QgisCartoDB.ui.UI_CartoDBPlugin import Ui_CartoDBPlugin

import QgisCartoDB.resources

import copy
import math


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

        self.getUserData(self.currentUser, self.currentApiKey, self.currentMultiuser)

        try:
            if not str(self.currentMultiuser) in ['true', '1', 'True']:
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

            self.tables = res['rows']
            self.updateList(self.tables)
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
            newTables = [t for t in self.tables if text in t['cdb_usertables']]
        self.updateList(newTables)

    def updateList(self, tables):
        items = []
        for table in tables:
            item = QListWidgetItem()
            item.setText(table['cdb_usertables'])
            if str(self.currentMultiuser) in ['true', '1', 'True'] and table['privileges'] == 'SELECT':
                item.setTextColor(QColor('#999999'))
            item.setIcon(QIcon(":/plugins/qgis-cartodb/images/icons/layers.png"))
            items.append(item)
        self.setTablesListItems(items)

    def setConnectionsFound(self, found):
        self.ui.connectBT.setEnabled(found)
        self.ui.deleteConnectionBT.setEnabled(found)
        self.ui.editConnectionBT.setEnabled(found)

    def getUserData(self, cartodbUser, apiKey, multiuser=False):
        cartoDBApi = CartoDBApi(cartodbUser, apiKey, multiuser)
        cartoDBApi.fetchContent.connect(self.cbUserData)
        cartoDBApi.getUserDetails()

    @pyqtSlot(dict)
    def cbUserData(self, data):
        self.currentUserData = data
        manager = QNetworkAccessManager()
        manager.finished.connect(self.returnAvatar)

        if 's3.amazonaws.com' in data['avatar_url']:
            imageUrl = QUrl(data['avatar_url'])
        else:
            imageUrl = QUrl('http:' + data['avatar_url'])

        request = QNetworkRequest(imageUrl)
        request.setRawHeader('User-Agent', 'QGIS 2.x')
        reply = manager.get(request)
        loop = QEventLoop()
        reply.finished.connect(loop.exit)
        loop.exec_()

    def setUpUserData(self):
        usedQuota = (float(self.currentUserData['quota_in_bytes']) - float(self.currentUserData['remaining_byte_quota']))/1024/1024
        quota = float(self.currentUserData['quota_in_bytes'])/1024/1024

        self.ui.remainingBar.setValue(math.ceil(usedQuota/quota*100))

        if usedQuota >= 1000:
            usedQuota = "{:.2f}".format(usedQuota/1024) + ' GB'
        else:
            usedQuota = "{:.2f}".format(usedQuota) + ' MB'

        if quota >= 1000:
            quota = "{:.2f}".format(quota/1024) + ' GB'
        else:
            quota = "{:.2f}".format(quota) + ' MB'

        self.ui.nameLB.setText(self.currentUserData['username'] + ', using ' + usedQuota + ' of ' + quota)

    def returnAvatar(self, reply):
        imageReader = QImageReader(reply)
        image = imageReader.read()

        lbl = self.ui.avatarLB
        if reply.error() == QNetworkReply.NoError:
            pixMap = QPixmap.fromImage(image).scaled(lbl.size(), Qt.KeepAspectRatio)
            lbl.setPixmap(pixMap)
            lbl.show()
        else:
            # TODO Put default image if not load from URL.
            pass

        self.setUpUserData()
