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
from PyQt4.QtCore import Qt, QVariant, qDebug
from PyQt4.QtGui import QDrag, QListWidget

from ListItemWidgets import CartoDBLayerListItem


class CartoDBLayersListWidget(QListWidget):
    def __init__(self, parent, name=''):
        QListWidget.__init__(self, parent)
        self.name = name

    def startDrag(self, supportedActions):
        drag = QDrag(self)
        mimeData = self.model().mimeData(self.selectedIndexes())
        # mimeData.setText(str(t))
        drag.setMimeData(mimeData)
        if drag.start(Qt.MoveAction) == Qt.MoveAction:
            for item in self.selectedItems():
                self.takeItem(self.row(item))

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if isinstance(event.source(), CartoDBLayersListWidget):
            event.setDropAction(Qt.MoveAction)
            # QListWidget.dropEvent(self, event)
            for item in event.source().selectedItems():
                itemWidget = event.source().itemWidget(item)
                newItemWidget = CartoDBLayerListItem(itemWidget.tableName, itemWidget.layer, itemWidget.size, itemWidget.rows)
                newItem = event.source().takeItem(event.source().row(item))
                itemAt = self.itemAt(event.pos())

                if itemAt is not None:
                    self.insertItem(self.row(itemAt), newItem)
                else:
                    self.addItem(newItem)

                self.setItemWidget(newItem, newItemWidget)
                self.setItemSelected(newItem, True)
                # event.accept()

    def dropMimeData(self, index, mimedata, action):
        super(CartoDBLayersListWidget, self).dropMimeData(index, mimedata, action)
        return True
