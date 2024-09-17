import sys
import time
import argparse

from threading import Thread

import subprocess
from io import BytesIO
from PIL import Image

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QMainWindow, QApplication, QLabel, QSizePolicy

# - = - = - = - = - = - = - = - = - = - = -
parser = argparse.ArgumentParser(
	prog = 'RetroSpectrum',
	description = 'Shows the spectrogram of an audio file. Similar to the Spek program',
	)

parser.add_argument('filename', metavar="<filename>", help='The media file to be opened') # positional argument
args = parser.parse_args()
media_file = args.filename
# - = - = - = - = - = - = - = - = - = - = -

def make_spectrogram(width, height):
	print("Drawing...")
	sox_command = [
		'sox', media_file, '-n', 'remix', '1', 'spectrogram', '-x', str(width-144), '-Y', str(height), '-z', '80', '-o', '-', '-p', '1',
	]
	proc = subprocess.Popen(sox_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	print("Postprocessing..")

	img_data = proc.stdout.read()

	try:
		with Image.open(BytesIO(img_data)) as img:
			b = BytesIO()
			img.save(b, 'png')
			return b.getvalue()
	except IOError as e:
		print(f"Error opening generated image: {e}")

	# Check errors
	stderr = proc.stderr.read().decode()
	if stderr:
		print(f"sox error occures: {stderr}")

def def_tick_handler():
	while True:
		if render.redraw_required is True:
			w.redraw_spectrogram()
			render.redraw_required = False
		time.sleep(0.1)

class RenderClass():
	def __init__(self):
		self.redraw_required = False
render = RenderClass()

class MainWindow(QMainWindow):
	def __init__(self):
		super(MainWindow, self).__init__()
		self.title = "Image Viewer"
		self.setWindowTitle(self.title)

		# Create widget
		render.label = QLabel(self)
		# Set photo for it
		render.pixmap = QPixmap()

		self.redraw_spectrogram()
		render.label.setScaledContents(True)

		# Minimum sox image size
		self.setMinimumSize(100+144, 130)

		self.setCentralWidget(render.label)
		#self.resize(pixmap.width(), pixmap.height())

	def resizeEvent(self, event):
		print("Window has been resized")
		print(f"Window size: {self.width()} x {self.height()}")
		#render.label.setText("Window side detected. Press 'Y' to redraw the spectrogram")
		render.redraw_required = True
		super(MainWindow, self).resizeEvent(event)

	def keyPressEvent(self, event):
		if event.key() == Qt.Key_Y:
			self.handle_y_key_press()

	def handle_y_key_press(self):
		render.redraw_required = True

	def redraw_spectrogram(self):
		print("Redrawing..")
		render.width = self.frameGeometry().width()
		render.height = self.frameGeometry().height()
		render.pixmap.loadFromData(make_spectrogram(render.width, render.height))
		render.label.setPixmap(render.pixmap)
		#render.label.setFixedSize(self.sizeHint())
		print("Redraw complete!")

tick_handler = Thread(target=def_tick_handler, daemon=True)
tick_handler.start()

app = QApplication(sys.argv)
w = MainWindow()
w.show()
sys.exit(app.exec())

