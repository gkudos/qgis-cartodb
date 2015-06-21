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

from PyQt4.QtGui import QApplication, QDialog, QMessageBox
from PyQt4.QtCore import QSettings

from QgisCartoDB.ui.NewConnection import Ui_NewConnection


class CartoDBNewConnectionDialog(QDialog):
    def __init__(self, user=None):
        QDialog.__init__(self)
        self.ui = Ui_NewConnection()
        self.ui.setupUi(self)
        self.settings = QSettings()
        self.user = None
        self.user_orig = user

    def accept(self):
        user = self.ui.userTX.text().strip()
        apiKey = self.ui.apiKeyTX.text().strip()
        multiuser = self.ui.multiuserCH.isChecked()

        if any([user == '', apiKey == '']):
            QMessageBox.warning(self, QApplication.translate('CartoDBPlugin', 'Save connection'),
                                QApplication.translate('CartoDBPlugin', 'Both User and Api Key must be provided'))
            return

        if user is not None:
            key = '/CartoDBPlugin/%s' % user
            keyapi = '%s/api' % key
            keymultiuser = '%s/multiuser' % key
            key_orig = '/CartoDBPlugin/%s' % self.user_orig
            # warn if entry was renamed to an existing connection
            if all([self.user_orig != user,
                    self.settings.contains(keyapi)]):
                res = QMessageBox.warning(self, QApplication.translate('CartoDBPlugin', 'Save connection'),
                                          QApplication.translate('CartoDBPlugin', 'Overwrite {}?').format(user),
                                          QMessageBox.Ok | QMessageBox.Cancel)
                if res == QMessageBox.Cancel:
                    return

            # on rename delete original entry first
            if all([self.user_orig is not None, self.user_orig != user]):
                self.settings.remove(key_orig)

            self.settings.setValue(keyapi, apiKey)
            self.settings.setValue(keymultiuser, multiuser)
            self.settings.setValue('/CartoDBPlugin/selected', user)

            QDialog.accept(self)

    def reject(self):
        # Back out of dialogue
        QDialog.reject(self)
