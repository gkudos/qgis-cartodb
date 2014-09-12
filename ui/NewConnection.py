# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/NewConnection.ui'
#
# Created: Thu Sep 11 17:55:06 2014
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

class Ui_NewConnection(object):
    def setupUi(self, NewConnection):
        NewConnection.setObjectName(_fromUtf8("NewConnection"))
        NewConnection.resize(436, 165)
        self.verticalLayout = QtGui.QVBoxLayout(NewConnection)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.title = QtGui.QLabel(NewConnection)
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.title.setFont(font)
        self.title.setObjectName(_fromUtf8("title"))
        self.verticalLayout.addWidget(self.title)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.form = QtGui.QFormLayout()
        self.form.setObjectName(_fromUtf8("form"))
        self.label = QtGui.QLabel(NewConnection)
        font = QtGui.QFont()
        font.setPointSize(11)
        font.setBold(False)
        font.setWeight(50)
        self.label.setFont(font)
        self.label.setObjectName(_fromUtf8("label"))
        self.form.setWidget(0, QtGui.QFormLayout.LabelRole, self.label)
        self.userTX = QtGui.QLineEdit(NewConnection)
        self.userTX.setObjectName(_fromUtf8("userTX"))
        self.form.setWidget(0, QtGui.QFormLayout.FieldRole, self.userTX)
        self.label_2 = QtGui.QLabel(NewConnection)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.form.setWidget(1, QtGui.QFormLayout.LabelRole, self.label_2)
        self.apiKeyTX = QtGui.QLineEdit(NewConnection)
        self.apiKeyTX.setObjectName(_fromUtf8("apiKeyTX"))
        self.form.setWidget(1, QtGui.QFormLayout.FieldRole, self.apiKeyTX)
        self.verticalLayout.addLayout(self.form)
        spacerItem1 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem1)
        self.buttonBox = QtGui.QDialogButtonBox(NewConnection)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Save)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(NewConnection)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), NewConnection.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), NewConnection.reject)
        QtCore.QMetaObject.connectSlotsByName(NewConnection)

    def retranslateUi(self, NewConnection):
        NewConnection.setWindowTitle(_translate("NewConnection", "New CartoDB Connection", None))
        self.title.setText(_translate("NewConnection", "New Connection", None))
        self.label.setText(_translate("NewConnection", "CartoDB User:", None))
        self.label_2.setText(_translate("NewConnection", "Carto DB Api Key:", None))

