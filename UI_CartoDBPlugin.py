# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'UI_CartoDBPlugin.ui'
#
# Created: Wed Sep 10 15:05:51 2014
#      by: PyQt4 UI code generator 4.10.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_CartoDBPlugin(object):
    def setupUi(self, CartoDBPlugin):
        CartoDBPlugin.setObjectName(_fromUtf8("CartoDBPlugin"))
        CartoDBPlugin.resize(538, 337)
        self.verticalLayout = QtGui.QVBoxLayout(CartoDBPlugin)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.label = QtGui.QLabel(CartoDBPlugin)
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setObjectName(_fromUtf8("label"))
        self.verticalLayout.addWidget(self.label)
        self.connectionList = QtGui.QComboBox(CartoDBPlugin)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.connectionList.sizePolicy().hasHeightForWidth())
        self.connectionList.setSizePolicy(sizePolicy)
        self.connectionList.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.connectionList.setObjectName(_fromUtf8("connectionList"))
        self.verticalLayout.addWidget(self.connectionList)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.connectBT = QtGui.QPushButton(CartoDBPlugin)
        self.connectBT.setObjectName(_fromUtf8("connectBT"))
        self.horizontalLayout.addWidget(self.connectBT)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.newConnectionBT = QtGui.QPushButton(CartoDBPlugin)
        self.newConnectionBT.setObjectName(_fromUtf8("newConnectionBT"))
        self.horizontalLayout.addWidget(self.newConnectionBT)
        self.editConnectionBT = QtGui.QPushButton(CartoDBPlugin)
        self.editConnectionBT.setObjectName(_fromUtf8("editConnectionBT"))
        self.horizontalLayout.addWidget(self.editConnectionBT)
        self.deleteConnectionBT = QtGui.QPushButton(CartoDBPlugin)
        self.deleteConnectionBT.setObjectName(_fromUtf8("deleteConnectionBT"))
        self.horizontalLayout.addWidget(self.deleteConnectionBT)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.tablesList = QtGui.QListWidget(CartoDBPlugin)
        self.tablesList.setAlternatingRowColors(True)
        self.tablesList.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
        self.tablesList.setObjectName(_fromUtf8("tablesList"))
        self.verticalLayout.addWidget(self.tablesList)
        self.buttonBox = QtGui.QDialogButtonBox(CartoDBPlugin)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(CartoDBPlugin)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), CartoDBPlugin.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), CartoDBPlugin.reject)
        QtCore.QMetaObject.connectSlotsByName(CartoDBPlugin)

    def retranslateUi(self, CartoDBPlugin):
        CartoDBPlugin.setWindowTitle(_translate("CartoDBPlugin", "Add CartoDB Layer", None))
        self.label.setText(_translate("CartoDBPlugin", "CartoDB Connections", None))
        self.connectBT.setText(_translate("CartoDBPlugin", "Connect", None))
        self.newConnectionBT.setText(_translate("CartoDBPlugin", "New", None))
        self.editConnectionBT.setText(_translate("CartoDBPlugin", "Edit", None))
        self.deleteConnectionBT.setText(_translate("CartoDBPlugin", "Delete", None))

