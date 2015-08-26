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

from PyQt4.QtCore import Qt, QSize
from PyQt4.QtGui import QWidget, QLabel, QProgressBar

from QgisCartoDB.ui.ListItem import Ui_ListItem


class CartoDBDatasetsListItem(QWidget):
    def __init__(self, tableName=None, tableOwner=None, size=None, rows=None, multiuser=False, shared=False):
        QWidget.__init__(self)
        self.ui = Ui_ListItem()
        self.ui.setupUi(self)

        self.shared = shared
        self.multiuser = multiuser
        self.readonly = False
        self.tableOwner = tableOwner

        self.setTableName(tableName)
        self.setSize(size)
        self.setRows(rows)

    def setTableName(self, tableName):
        self.tableName = tableName
        text = tableName
        if tableName is not None:
            if self.shared:
                text = text + ' ({})'.format(self.tableOwner)
            self.ui.tableNameTX.setText(text)

    def setSize(self, size):
        self.size = size
        if size is not None:
            sizeText = float(size/1024)

            if sizeText >= 1000:
                sizeText = sizeText/1024
                if sizeText >= 1000:
                    sizeText = "{:.2f}".format(sizeText/1024) + ' GB'
                else:
                    sizeText = "{:.2f}".format(sizeText) + ' MB'
            else:
                sizeText = "{:.2f}".format(sizeText) + ' KB'

            self.ui.sizeTX.setText(sizeText)

    def setRows(self, rows):
        self.rows = rows
        if rows is not None:
            self.ui.rowsTX.setText("{:,} rows".format(rows))

    def setTextColor(self, color):
        self.ui.tableNameTX.setStyleSheet('color: ' + color)
        self.ui.rowsTX.setStyleSheet('color: ' + color)
        self.ui.sizeTX.setStyleSheet('color: ' + color)

    def clone(self):
        return CartoDBDatasetsListItem(self.tableName, self.tableOwner, self.size, self.rows)


class CartoDBLayerListItem(CartoDBDatasetsListItem):
    def __init__(self, tableName=None, layer=None, size=None, rows=None):
        CartoDBDatasetsListItem.__init__(self, tableName, None, size, rows)

        '''
        self.ui.statusLB = QLabel(self)
        self.ui.statusLB.setMaximumSize(QSize(100, 16777215))
        self.ui.statusLB.setAlignment(Qt.AlignCenter | Qt.AlignTrailing | Qt.AlignVCenter)
        self.ui.statusLB.setWordWrap(True)
        self.ui.horizontalLayout.insertWidget(1, self.ui.statusLB)
        '''

        self.ui.statusBar = QProgressBar(self)
        self.ui.statusBar.setProperty("value", 0)
        self.ui.statusBar.setFormat("Init")
        self.ui.statusBar.hide()
        self.ui.horizontalLayout.insertWidget(1, self.ui.statusBar)

        self.layer = layer

    def setStatus(self, status, value = 0):
        self.ui.statusBar.setProperty("value", value)
        self.ui.statusBar.setFormat(status)
        self.ui.statusBar.show()

    def clone(self):
        return CartoDBDatasetsListItem(self.tableName, self.layer, self.size, self.rows)
