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


class CartoDBLayersListWidget(QListWidget):
    def __init__(self, parent):
        QListWidget.__init__(self, parent)

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
            QListWidget.dropEvent(self, event)
        '''
        data = event.mimeData()
        bstream = data.retrieveData("application/x-qabstractitemmodeldatalist", QVariant.ByteArray)
        qDebug('Drop Event: ' + str(bstream))
        event.setDropAction(Qt.MoveAction)
        event.accept()
        '''
    def dropMimeData(self, index, mimedata, action):
        super(CartoDBLayersListWidget, self).dropMimeData(index, mimedata, action)
        return True
