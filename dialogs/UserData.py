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

from PyQt4.QtCore import QUrl, QEventLoop, pyqtSignal, pyqtSlot, Qt, qDebug
from PyQt4.QtGui import QApplication, QDialog, QPixmap, QImage, QImageReader
from PyQt4.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from QgisCartoDB.utils import CartoDBPluginWorker

import math


class CartoDBUserDataDialog(QDialog):
    def __init__(self, toolbar, parent=None):
        QDialog.__init__(self, parent)
        self.toolbar = toolbar

        self.currentUser = self.toolbar.currentUser
        self.currentApiKey = self.toolbar.currentApiKey
        self.currentMultiuser = self.toolbar.currentMultiuser

        self.totalTables = None
        self.totalShared = None

    def initUserConnection(self):
        worker = CartoDBPluginWorker(self, 'connectUser')
        worker.start()

    @pyqtSlot()
    def connectUser(self):
        self.getUserData(self.currentUser, self.currentApiKey, self.currentMultiuser)

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
                imageUrl = QUrl('https:' + data['avatar_url'])

            request = QNetworkRequest(imageUrl)
            request.setRawHeader('User-Agent', 'QGIS 2.x')
            reply = manager.get(request)
            loop = QEventLoop()
            reply.finished.connect(loop.exit)
            loop.exec_()

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
