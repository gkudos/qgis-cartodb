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

from PyQt4.QtGui import QDialog
from QgisCartoDB.ui.NewSQL import Ui_NewSQL

from PyQt4.QtGui import *

from qgis.core import *
from qgis.gui import *


class CartoDBNewSQLDialog(QDialog):
    def __init__(self):
        QDialog.__init__(self)
        self.ui = Ui_NewSQL()
        self.ui.setupUi(self)
        self.ui.sqlEditor = QgsCodeEditorSQL(self)
        self.ui.verticalLayout.addWidget(self.ui.sqlEditor)
