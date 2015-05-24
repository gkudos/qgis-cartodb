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
from PyQt4.QtCore import QSettings, QUrl, QEventLoop, pyqtSignal, pyqtSlot, Qt, qDebug
from PyQt4.QtGui import QDialog, QMessageBox, QListWidgetItem, QIcon, QColor, QImage, QPixmap, QImageReader
from PyQt4.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from qgis.core import QgsMessageLog

from QgisCartoDB.cartodb import CartoDBAPIKey, CartoDBException, CartoDBApi
from QgisCartoDB.dialogs.ConnectionManager import CartoDBConnectionsManager
from QgisCartoDB.dialogs.NewConnection import CartoDBNewConnectionDialog
from QgisCartoDB.ui.UI_CartoDBPlugin import Ui_CartoDBPlugin
from QgisCartoDB.utils import CartoDBPluginWorker
from QgisCartoDB.widgets import CartoDBDatasetsListItem

import QgisCartoDB.resources

import copy
import math


# Create the dialog for CartoDBPlugin
class CartoDBPluginDialog(QDialog):
    def __init__(self, toolbar):
        QDialog.__init__(self)
        self.toolbar = toolbar
        self.settings = QSettings()
        # Set up the user interface from Designer.
        self.ui = Ui_CartoDBPlugin()
        self.ui.setupUi(self)
        self.ui.searchTX.textChanged.connect(self.filterTables)
        self.ui.tablesList.verticalScrollBar().valueChanged.connect(self.onScroll)

        self.currentUser = None
        self.currentApiKey = None
        self.currentMultiuser = None

        self.isLoadingTables = False
        self.noLoadTables = False

    def getTablesListSelectedItems(self):
        return self.ui.tablesList.selectedItems()

    def getItemWidget(self, item):
        return self.ui.tablesList.itemWidget(item)

    @pyqtSlot()
    def connect(self):
        # Get tables from CartoDB.
        self.currentUser = self.toolbar.currentUser
        self.currentApiKey = self.toolbar.currentApiKey
        self.currentMultiuser = self.toolbar.currentMultiuser

        self.tablesPage = 1
        self.noLoadTables = False
        self.ui.searchTX.setText('')
        self.getTables(self.currentUser, self.currentApiKey, self.currentMultiuser)
        self.getUserData(self.currentUser, self.currentApiKey, self.currentMultiuser)

    def filterTables(self):
        text = self.ui.searchTX.text()
        if text == '':
            newVisualizations = self.visualizations
        else:
            newVisualizations = [t for t in self.visualizations if text in t['name']]
        self.updateList(newVisualizations)

    def updateList(self, visualizations):
        self.ui.tablesList.clear()
        for visualization in visualizations:
            item = QListWidgetItem(self.ui.tablesList)

            owner = None
            if visualization['permission']['owner']['username'] != self.currentUser:
                owner = visualization['permission']['owner']['username']

            widget = CartoDBDatasetsListItem(visualization['name'], owner, visualization['table']['size'], visualization['table']['row_count'])
            # item.setText(visualization['name'])
            readonly = False
            if visualization['permission'] is not None and visualization['permission']['acl'] is not None:
                for acl in visualization['permission']['acl']:
                    if acl['type'] == 'user' and acl['entity']['username'] == self.currentUser and acl['access'] == 'r':
                        readonly = True
                        break
            if readonly:
                widget.setTextColor('#999999')

            item.setSizeHint(widget.sizeHint())
            # item.setIcon(QIcon(":/plugins/qgis-cartodb/images/icons/layers.png"))
            self.ui.tablesList.setItemWidget(item, widget)

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

    def getTables(self, cartodbUser, apiKey, multiuser=False):
        cartoDBApi = CartoDBApi(cartodbUser, apiKey, multiuser)
        cartoDBApi.fetchContent.connect(self.cbTables)
        self.isLoadingTables = True
        cartoDBApi.getUserTables(self.tablesPage)

    @pyqtSlot(dict)
    def cbTables(self, data):
        self.totalTables = data['total_user_entries']
        self.totalShared = data['total_shared']

        if len(data['visualizations']) == 0:
            self.noLoadTables = True

        if self.tablesPage == 1:
            self.visualizations = data['visualizations']
        else:
            self.visualizations.extend(data['visualizations'])

        self.updateList(self.visualizations)
        self.settings.setValue('/CartoDBPlugin/selected', self.currentUser)
        self.ui.searchTX.setEnabled(True)
        self.isLoadingTables = False

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

    def onScroll(self, val):
        maximum = self.ui.tablesList.verticalScrollBar().maximum()
        if val >= maximum - 4 and not self.isLoadingTables and not self.noLoadTables:
            self.tablesPage = self.tablesPage + 1
            self.getTables(self.currentUser, self.currentApiKey, self.currentMultiuser)

    def showEvent(self, event):
        # super(CartoDBPluginDialog, self).showEvent(event)
        worker = CartoDBPluginWorker(self, 'connect')
        worker.start()
        # self.connect()
        # QMetaObject.invokeMethod(self.controller, 'connectCB')
