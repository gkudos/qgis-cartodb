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
from PyQt4.QtCore import Qt, QSettings, pyqtSlot, qDebug
from PyQt4.QtGui import QApplication, QDialog, QPixmap

from QgisCartoDB.utils import CartoDBPluginWorker

import math


class CartoDBPluginUserDialog(QDialog):
    def __init__(self, toolbar, parent=None):
        QDialog.__init__(self, parent)
        self.toolbar = toolbar
        self.settings = QSettings()

        self.currentUser = self.toolbar.currentUser
        self.currentApiKey = self.toolbar.currentApiKey
        self.currentMultiuser = self.toolbar.currentMultiuser
        self.currentUserData = self.toolbar.currentUserData

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

        self.ui.nameLB.setText(self.currentUserData['username'])
        if hasattr(self.ui, 'quotaLB'):
            self.ui.quotaLB.setText(
                QApplication.translate('CartoDBPlugin', 'Using {} of {}')
                            .format(usedQuota, quota))
