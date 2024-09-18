""" The component that contains all dialog boxes. """
import sys
from PySide6.QtWidgets import QApplication, QMessageBox

def ok_dialog_box(message, title="Information"):
	""" Calls a simple window with a message and an OK button """
	# Init Qt
	app = QApplication(sys.argv)

	# Make dialog box
	msg_box = QMessageBox()
	msg_box.setText(message)
	msg_box.setStandardButtons(QMessageBox.Ok)
	msg_box.setWindowTitle(title)

	# Show it
	msg_box.exec()

	# Shutdown Qt
	app.shutdown()

def error_dialog_box(message, title="Error"):
	""" Calls a simple window with a message and an OK button """
	# Init Qt
	app = QApplication(sys.argv)

	# Make dialog box
	msg_box = QMessageBox()
	msg_box.setText(message)
	msg_box.setIcon(QMessageBox.Critical)
	msg_box.setStandardButtons(QMessageBox.Ok)
	msg_box.setWindowTitle(title)

	# Show it
	msg_box.exec()

	# Shutdown Qt
	app.shutdown()


