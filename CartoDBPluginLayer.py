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

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *


class CartoDBPluginLayer(QgsPluginLayer):
    LAYER_TYPE = "cartodb"

    def __init__(self):
        QgsPluginLayer.__init__(self, WatermarkPluginLayer.LAYER_TYPE, "CartoDB Plugin Layer")
        self.setValid(True)

    def draw(self, rendererContext):
        return True

    def readXml(self, node):
        return True

    def writeXml(self, node, doc):
        return True

    def showImageDialog(self):
        self.emit(SIGNAL("repaintRequested()"))
