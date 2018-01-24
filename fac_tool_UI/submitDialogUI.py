# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'submitDialogUI.ui'
#
# Created: Tue Jan 23 20:38:39 2018
#      by: PyQt4 UI code generator 4.11.3
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

class Ui_submitDialog(object):
    def setupUi(self, submitDialog):
        submitDialog.setObjectName(_fromUtf8("submitDialog"))
        submitDialog.resize(280, 160)
        submitDialog.setMinimumSize(QtCore.QSize(280, 160))
        submitDialog.setMaximumSize(QtCore.QSize(280, 160))
        self.pbSubmit = QtGui.QPushButton(submitDialog)
        self.pbSubmit.setGeometry(QtCore.QRect(110, 120, 75, 23))
        self.pbSubmit.setObjectName(_fromUtf8("pbSubmit"))
        self.pbCancel = QtGui.QPushButton(submitDialog)
        self.pbCancel.setGeometry(QtCore.QRect(190, 120, 75, 23))
        self.pbCancel.setObjectName(_fromUtf8("pbCancel"))
        self.leVerify = QtGui.QLineEdit(submitDialog)
        self.leVerify.setGeometry(QtCore.QRect(50, 60, 181, 31))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.leVerify.setFont(font)
        self.leVerify.setObjectName(_fromUtf8("leVerify"))
        self.label = QtGui.QLabel(submitDialog)
        self.label.setGeometry(QtCore.QRect(70, 30, 121, 21))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.label.setFont(font)
        self.label.setObjectName(_fromUtf8("label"))
        self.widget = QtGui.QWidget(submitDialog)
        self.widget.setGeometry(QtCore.QRect(0, 0, 281, 161))
        self.widget.setObjectName(_fromUtf8("widget"))

        self.retranslateUi(submitDialog)
        QtCore.QMetaObject.connectSlotsByName(submitDialog)

    def retranslateUi(self, submitDialog):
        submitDialog.setWindowTitle(_translate("submitDialog", "Verify", None))
        self.pbSubmit.setText(_translate("submitDialog", "submit", None))
        self.pbCancel.setText(_translate("submitDialog", "cancel", None))
        self.label.setText(_translate("submitDialog", "verify code:", None))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    submitDialog = QtGui.QDialog()
    ui = Ui_submitDialog()
    ui.setupUi(submitDialog)
    submitDialog.show()
    sys.exit(app.exec_())

