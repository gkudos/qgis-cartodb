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

from PyQt4.QtGui import QWidget

from QgisCartoDB.ui.ListItem import Ui_ListItem


class CartoDBDatasetsListItem(QWidget):
    def __init__(self, tableName=None, tableOwner=None, size=None, rows=None):
        QWidget.__init__(self)
        self.ui = Ui_ListItem()
        self.ui.setupUi(self)
        self.setTableName(tableName)
        self.tableOwner = tableOwner
        self.setSize(size)
        self.setRows(rows)

    def setTableName(self, tableName):
        self.tableName = tableName
        if tableName is not None:
            self.ui.tableNameTX.setText(tableName)

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


class CartoDBLayerListItem(CartoDBDatasetsListItem):
    def __init__(self, tableName=None, layer=None, size=None, rows=None):
        CartoDBDatasetsListItem.__init__(self, tableName, None, size, rows)
        self.layer = layer
