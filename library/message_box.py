from PyQt5 import QtWidgets, QtCore


class MessageBox(QtCore.QThread):
    def __init__(self):
        self.dialog = QtWidgets.QMessageBox()

    def warning_box(self, body ,title = "Warning"):
        self.dialog.setIcon(QtWidgets.QMessageBox.Warning)
        self.dialog.setText(str(body))
        # msg.setInformativeText("This is additional information")
        self.dialog.setWindowTitle(str(title))
        # msg.setDetailedText("The details are as follows:")
        # msg.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
        self.dialog.setStandardButtons(QtWidgets.QMessageBox.Ok)
        self.dialog.exec_()

    def question(self, body, title="Split Downloader"):
        self.dialog.setIcon(QtWidgets.QMessageBox.Question)
        self.dialog.setText(str(body))
        self.dialog.setWindowTitle(str(title))
        self.dialog.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        self.dialog.exec_()
        return self.dialog.clickedButton().text()

    def info_box(self, body ,title = "Info"):
        self.dialog.setIcon(QtWidgets.QMessageBox.Information)
        self.dialog.setText(str(body))
        # msg.setInformativeText("This is additional information")
        self.dialog.setWindowTitle(str(title))
        # msg.setDetailedText("The details are as follows:")
        self.dialog.setStandardButtons(QtWidgets.QMessageBox.Ok)
        self.dialog.exec_()