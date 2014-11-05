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

from PyQt4.QtCore import QSettings
from PyQt4.QtGui import QDialog, QSizePolicy, QColor
from QgisCartoDB.ui.NewSQL import Ui_NewSQL

from PyQt4.Qsci import QsciScintilla, QsciScintillaBase, QsciLexerSQL


class CartoDBNewSQLDialog(QDialog):
    def __init__(self):
        QDialog.__init__(self)
        self.settings = QSettings()
        self.ui = Ui_NewSQL()
        self.ui.setupUi(self)
        self._initEditor()
        self.populateConnectionList()

    def _initEditor(self):
        self.ui.sqlEditor = QsciScintilla(self)
        # Don't want to see the horizontal scrollbar at all
        self.ui.sqlEditor.SendScintilla(QsciScintilla.SCI_SETHSCROLLBAR, 0)

        self.ui.sqlEditor.setMarginLineNumbers(0, True)
        self.ui.sqlEditor.setMarginWidth(0, "000")
        self.ui.sqlEditor.setMarginsForegroundColor(QColor("#2468A7"))

        # Brace matching: enable for a brace immediately before or after
        # the current position.
        self.ui.sqlEditor.setBraceMatching(QsciScintilla.SloppyBraceMatch)

        # Current line visible with special background color
        self.ui.sqlEditor.setCaretLineVisible(True)
        self.ui.sqlEditor.setCaretLineBackgroundColor(QColor("#E4EEFF"))

        lexer = QsciLexerSQL()
        self.ui.sqlEditor.setLexer(lexer)

        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.ui.sqlEditor.sizePolicy().hasHeightForWidth())
        self.ui.sqlEditor.setSizePolicy(sizePolicy)

        self.ui.verticalLayout.insertWidget(0, self.ui.sqlEditor)

    def populateConnectionList(self):
        self.settings.beginGroup('/CartoDBPlugin/')
        self.ui.connectionList.clear()
        self.ui.connectionList.addItems(self.settings.childGroups())
        self.settings.endGroup()
        self.setConnectionListPosition()

    def setConnectionListPosition(self):
        # Set the current index to the selected connection.
        toSelect = self.settings.value('/CartoDBPlugin/selected')
        conCount = self.ui.connectionList.count()

        # self.setConnectionsFound(conCount > 0)

        exists = False
        for i in range(conCount):
            if self.ui.connectionList.itemText(i) == toSelect:
                self.ui.connectionList.setCurrentIndex(i)
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

            self.ui.connectionList.setCurrentIndex(currentIndex)
