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
from PyQt4.QtGui import QWidget, QHBoxLayout, QLayout, QComboBox, QSizePolicy
from PyQt4.QtCore import Qt, QSize, QSettings


class CartoDBToolbar(QWidget):
    def __init__(self, parent=None, flags=Qt.WindowFlags(0)):
        QWidget.__init__(self, parent, flags)
        self.settings = QSettings()
        self.setupUi()
        self.populateConnectionList()

    def setupUi(self):
        self.connectLayout = QHBoxLayout(self)
        self.connectLayout.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.connectionList = QComboBox(self)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.connectionList.sizePolicy().hasHeightForWidth())
        self.connectionList.setSizePolicy(sizePolicy)
        self.connectionList.setMaximumSize(QSize(16777215, 16777215))
        self.connectLayout.addWidget(self.connectionList)

    def populateConnectionList(self):
        # Populate connections saved.
        self.settings.beginGroup('/CartoDBPlugin/')
        self.connectionList.clear()
        self.connectionList.addItems(self.settings.childGroups())
        self.settings.endGroup()
        self.setConnectionListPosition()

    def setConnectionListPosition(self):
        # Set the current index to the selected connection.
        toSelect = self.settings.value('/CartoDBPlugin/selected')
        conCount = self.connectionList.count()

        # self.setConnectionsFound(conCount > 0)

        exists = False
        for i in range(conCount):
            if self.connectionList.itemText(i) == toSelect:
                self.connectionList.setCurrentIndex(i)
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

            self.connectionList.setCurrentIndex(currentIndex)
