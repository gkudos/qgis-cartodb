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
from PyQt4.QtCore import Qt, QObject, QThread, QMetaObject, Q_RETURN_ARG, pyqtSignal
import traceback


class CartoDBPluginWorker(QThread):
    error = pyqtSignal(Exception, basestring)
    finished = pyqtSignal()

    def __init__(self, object=None, method=None, connection=Qt.AutoConnection):
        QThread.__init__(self)
        self.object = object
        self.method = method
        self.connection = connection

    def __del__(self):
        self.wait()

    def run(self):
        try:
            if self.object is not None and self.method is not None:
                # TODO Get return value.
                QMetaObject.invokeMethod(self.object, self.method, self.connection)
        except Exception, e:
            self.error.emit(e, traceback.format_exc())
        self.finished.emit()
