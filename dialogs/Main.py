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
from PyQt4.QtCore import QSettings, QUrl, QEventLoop, pyqtSignal, pyqtSlot, Qt, qDebug
from PyQt4.QtGui import QApplication, QDialog, QMessageBox, QListWidgetItem, QIcon, QColor, QImage, QPixmap, QImageReader
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
import json


# Create the dialog for CartoDBPlugin
class CartoDBPluginDialog(QDialog):
    def __init__(self, toolbar, parent=None):
        QDialog.__init__(self, parent)
        self.toolbar = toolbar
        self.settings = QSettings()
        # Set up the user interface from Designer.
        self.ui = Ui_CartoDBPlugin()
        self.ui.setupUi(self)
        self.ui.searchTX.textChanged.connect(self.filterTables)
        # self.ui.tablesList.verticalScrollBar().valueChanged.connect(self.onScroll)

        self.currentUser = self.toolbar.currentUser
        self.currentApiKey = self.toolbar.currentApiKey
        self.currentMultiuser = self.toolbar.currentMultiuser

        self.isLoadingTables = False
        self.noLoadTables = False
        self.totalTables = None
        self.totalShared = None

        worker = CartoDBPluginWorker(self, 'connectUser')
        worker.start()

    def getTablesListSelectedItems(self):
        return self.ui.tablesList.selectedItems()

    def getItemWidget(self, item):
        return self.ui.tablesList.itemWidget(item)

    def filterByExtent(self):
        return self.ui.extentCH.isChecked()

    @pyqtSlot()
    def connect(self):
        # Get tables from CartoDB.
        self.tablesPage = 1
        self.noLoadTables = False
        self.ui.searchTX.setText('')
        self.getTables(self.currentUser, self.currentApiKey, self.currentMultiuser)

    @pyqtSlot()
    def connectUser(self):
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
            # qDebug('Vis:' + json.dumps(visualization, sort_keys=True, indent=2, separators=(',', ': ')))
            if visualization['permission'] is not None and visualization['permission']['owner']['username'] != self.currentUser and \
               visualization['permission']['acl'] is not None:
                for acl in visualization['permission']['acl']:
                    if acl['type'] == 'user' and 'username' in acl['entity'] and acl['entity']['username'] == self.currentUser and \
                       acl['access'] == 'r':
                        readonly = True
                        break
            if readonly:
                widget.setTextColor('#999999')

            item.setSizeHint(widget.sizeHint())
            # item.setIcon(QIcon(":/plugins/qgis-cartodb/images/icons/layers.png"))
            self.ui.tablesList.setItemWidget(item, widget)

    def getUserData(self, cartodbUser, apiKey, multiuser=False):
        if self.toolbar.avatarImage is not None:
            pixMap = QPixmap.fromImage(self.toolbar.avatarImage).scaled(self.ui.avatarLB.size(), Qt.KeepAspectRatio)
            self.ui.avatarLB.setPixmap(pixMap)
            self.ui.avatarLB.show()

        if self.toolbar.currentUserData is not None:
            self.currentUserData = self.toolbar.currentUserData
            self.setUpUserData()
        else:
            cartoDBApi = CartoDBApi(cartodbUser, apiKey, multiuser)
            cartoDBApi.fetchContent.connect(self.cbUserData)
            cartoDBApi.getUserDetails()

    @pyqtSlot(dict)
    def cbUserData(self, data):
        self.currentUserData = data

        if self.toolbar.avatarImage is None:
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

        self.setUpUserData()

    def getTables(self, cartodbUser, apiKey, multiuser=False):
        cartoDBApi = CartoDBApi(cartodbUser, apiKey, multiuser)
        cartoDBApi.fetchContent.connect(self.cbTables)
        self.isLoadingTables = True
        # cartoDBApi.getUserTables(self.tablesPage)
        cartoDBApi.getUserTables(1, 100000)

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

        self.visualizations.reverse()

        self.updateList(self.visualizations)
        self.settings.setValue('/CartoDBPlugin/selected', self.currentUser)
        self.ui.searchTX.setEnabled(True)
        self.isLoadingTables = False
        self.setUpUserData()

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

        if self.totalTables is None or self.totalShared is None:
            self.ui.nameLB.setText(
                QApplication.translate('CartoDBPlugin', '{}, using {} of {}')
                            .format(self.currentUserData['username'], usedQuota, quota))
        else:
            self.ui.nameLB.setText(
                QApplication.translate('CartoDBPlugin', '{}, using {} of {}, {} tables, {} shared')
                            .format(self.currentUserData['username'], usedQuota, quota, self.totalTables, self.totalShared))

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
