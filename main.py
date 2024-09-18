import os
import sys
import time
import argparse

from threading import Thread

import subprocess
from io import BytesIO
from PIL import Image

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QMainWindow, QApplication, QLabel

from PySide6.QtWidgets import QWidget, QVBoxLayout, QProgressBar
from PySide6.QtCore import QMimeData
from PySide6.QtGui import QDragEnterEvent, QDropEvent

# - = - = - = - = - = - = -
modules_path = os.path.dirname(os.path.realpath(__file__)) # get currently running script path
# print(modules_path)
sys.path.append(modules_path)
import ffprobe
from render import dialog_boxes
# - = - = - = - = - = - = - = - = - = - = -

parser = argparse.ArgumentParser(
	prog = 'RetroSpectrum',
	description = 'Shows the spectrogram of an audio file. Similar to the Spek program',
	)

parser.add_argument('filename', metavar="<filename>", help='The media file to be opened') # positional argument
args = parser.parse_args()
media_file = args.filename

# - = - = - = - = - = - = - = - = - = - = -

supported_formats = ("8svx", ".aif", ".aifc", ".aiff", ".aiffc", ".al", ".amb", ".amr-nb", ".amr-wb", ".anb", ".au", ".avr", ".awb", ".caf", ".cdda", ".cdr", ".cvs", ".cvsd", ".cvu", ".dat", ".dvms", ".f32", ".f4", ".f64", ".f8", ".fap", ".flac", ".fssd", ".gsm", ".gsrt", ".hcom", ".htk", ".ima", ".ircam", ".la", ".lpc", ".lpc10", ".lu", ".mat", ".mat4", ".mat5", ".maud", ".mp2", ".mp3", ".nist", ".ogg", ".opus", ".paf", ".prc", ".pvf", ".raw", ".s1", ".s16", ".s2", ".s24", ".s3", ".s32", ".s4", ".s8", ".sb", ".sd2", ".sds", ".sf", ".sl", ".sln", ".smp", ".snd", ".sndfile", ".sndr", ".sndt", ".sou", ".sox", ".sph", ".sw", ".txw", ".u1", ".u16", ".u2", ".u24", ".u3", ".u32", ".u4", ".u8", ".ub", ".ul", ".uw", ".vms", ".voc", ".vorbis", ".vox", ".w64", ".wav", ".wavpcm", ".wv", ".wve", ".xa", ".xi") # need for drag-n-drop

class FileClass:
	def __init__(self, media_file):
		# - = - = - = - = - = - = - = - = - = - = -
		# Check file existance
		if os.path.isfile(media_file) is False:
			message = "Seems like file does not exist:\n" + media_file
			dialog_boxes.error_dialog_box(message)
		# - = - = - = - = - = - = - = - = - = - = -
		self.ffmpeg_text = ffprobe.get_ffprobe_string(media_file)
		# - = - = - = - = - = - = - = - = - = - = -
		self.filename = media_file
this_file = FileClass(media_file)

# - = - = - = - = - = - = - = - = - = - = -

class DrawClass():
	def __init__(self):
		self.default_variables = {
			"contrast": {"current": 80, "min": 20, "max": 180}, # -z num  Z-axis range in dB; default 120
			"channels": {"current": 1, "min": 1, "max": 2},		# remix
			"color":	{"current": 1, "min": 1, "max": 6},	 # -p num  Permute colours (1 - 6); default 1
			"maxdBFS":  {"current": 0, "min": -100, "max": 100}, # -Z num  Z-axis maximum in dBFS; default 0
				}
		self.variables = self.default_variables.copy()
draw = DrawClass()

# - = - = - = - = - = - = - = - = - = - = -


def make_spectrogram(width, height):
	# - = - = - = - = - = - = -
	print("Drawing...")

	# - Command generator = - = - = - = - = - =
	sox_command = [
		'sox', this_file.filename, '-n', # base command
	]

	# - = Сhannels
	if draw.variables["channels"]["current"] == 1:
		sox_command.append("remix")
		sox_command.append("1")
	# else no
	# - = - = - =

	# Required part
	sox_command.append("spectrogram")

	# - = Image dimentions (is set by the window size)
	# -144 because -x responses only for raw spectrogram, border with text takes 144 pixels
	sox_command.append("-x")
	sox_command.append(str(width-144))

	sox_command.append("-Y")
	sox_command.append(str(height))
	# - = - = - =

	# - = Comment shown
	# Spaces for when the rounding overlaps the text
	if render.redraw_required_message is None:
		sox_command.append("-c")
		sox_command.append("  Created by SoX and RetroSpectrum")
	else:
		sox_command.append("-c")
		sox_command.append("  " + render.redraw_required_message)
	# - = - = - =

	# - = Title text
	sox_command.append("-t")
	sox_command.append(this_file.ffmpeg_text)
	# - = - = - =

	# - = Contrast
	sox_command.append("-z")
	sox_command.append(str(draw.variables["contrast"]["current"]))
	# - = - = - =

	# - = Color
	sox_command.append("-p")
	sox_command.append(str(draw.variables["color"]["current"]))
	# - = - = - =

	# - = maxdBFS
	sox_command.append("-Z")
	sox_command.append(str(draw.variables["maxdBFS"]["current"]))
	# - = - = - =

	# - = End of command
	sox_command.append("-o")
	sox_command.append("-")
	# - = - = - =

	# - = - = - = - = - = - = - = - = - = - = -

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
	# - = - = - = - = - = - = - = - = -
	window_width = window_width_old = w.frameGeometry().width()
	window_height = window_height_old = w.frameGeometry().height()
	while True:
		window_width = w.frameGeometry().width()
		window_height = w.frameGeometry().height()
		if window_width != window_width_old or window_height != window_height_old:
			window_width_old = window_width
			window_height_old = window_height
			w.redraw_spectrogram()
			print(f"Redrawn for {window_width}x{window_height}")
		# - = - = - = - = - = - = - = - = -

		# - REDRAWER = - = - = - = - = - = -
		if render.redraw_required is True:
			w.redraw_spectrogram()
			render.redraw_required = False
		# - = - = - = - = - = - = - = - = -
		# - = Message ticks handler
		if render.redraw_required_message_ticks != 0:
			render.redraw_required_message_ticks -= 1
			if render.redraw_required_message_ticks == 0:
				render.redraw_required_message = None
				render.redraw_required = True
		# - = - = - = - = - = - = - = - = -
		time.sleep(0.1)

class RenderClass():
	def __init__(self):
		self.redraw_required = False
		self.redraw_required_message = None
		self.redraw_required_message_ticks = 0
render = RenderClass()

class MainWindow(QMainWindow):
	def __init__(self):
		super(MainWindow, self).__init__()
		self.title = "RetroSpectrum"
		self.setWindowTitle(self.title)
		self.setAcceptDrops(True)

		# Create widget
		render.label = QLabel(self)
		# Set photo for it
		render.pixmap = QPixmap()

		self.redraw_spectrogram()
		render.label.setScaledContents(True)

		# - = - = - = - = - = - = - = - = - = - = -
		# Drag-n-drop layout
		self.layout = QVBoxLayout()
		self.layout.addWidget(render.label)
		self.setLayout(self.layout)
		# - = - = - = - = - = - = - = - = - = - = -

		# Minimum sox image size
		self.setMinimumSize(100+144, 130)

		self.setCentralWidget(render.label)
		#self.resize(pixmap.width(), pixmap.height())

	def keyPressEvent(self, event):
		# Force redraw
		if event.key() == Qt.Key_Y:
			render.redraw_required = True

		# - = - = - = - = - = - = - = - = - = - = -
		# contrast
		if event.key() == Qt.Key_1:
			self.setting_change("contrast", "minus")
		if event.key() == Qt.Key_2:
			self.setting_change("contrast", "plus")
		# - = - = - = - = - = - = - = - = - = - = -
		# channels
		if event.key() == Qt.Key_S:
			self.setting_change("channels", "carousel")
		# - = - = - = - = - = - = - = - = - = - = -
		# channels
		if event.key() == Qt.Key_C:
			self.setting_change("color", "carousel")
		# - = - = - = - = - = - = - = - = - = - = -
		# maxdBFS
		if event.key() == Qt.Key_3:
			self.setting_change("maxdBFS", "minus")
		if event.key() == Qt.Key_4:
			self.setting_change("maxdBFS", "plus")
		# - = - = - = - = - = - = - = - = - = - = -

	def setting_change(self, setting, action):
		if setting not in draw.variables:
			raise ValueError("Specified setting not in draw.variables")
		elif action == "plus":
			if draw.variables[setting]["current"]+1 <= draw.variables[setting]["max"]:
				draw.variables[setting]["current"] = draw.variables[setting]["current"] + 1
			else:
				print(setting + " maximum!")
		elif action == "minus":
			if draw.variables[setting]["current"]-1 >= draw.variables[setting]["min"]:
				draw.variables[setting]["current"] = draw.variables[setting]["current"] - 1
			else:
				print(setting + " minimum!")
		elif action == "carousel":
			if draw.variables[setting]["current"]+1 <= draw.variables[setting]["max"]:
				draw.variables[setting]["current"] = draw.variables[setting]["current"] + 1
			else:
				draw.variables[setting]["current"] = draw.variables[setting]["min"]

		print("\n\n" + str(draw.variables))
		render.redraw_required = True
		if action == "plus":
			symbol = "+"
		elif action == "minus":
			symbol = "-"
		elif action == "carousel":
			symbol = ">"
		render.redraw_required_message = f"Setting \"{setting}\" changed: [{symbol}] {draw.variables[setting]['current']}"
		render.redraw_required_message += f" (min {draw.variables[setting]['min']} / max {draw.variables[setting]['max']})"
		render.redraw_required_message_ticks = 30

	# - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = -
	# Drag-n-drop support
	def dragEnterEvent(self, event: QDragEnterEvent):
		if event.mimeData().hasUrls():  # Check that the data contains URLs (files)
			urls = event.mimeData().urls()
			if len(urls) == 1 and urls[0].toString().endswith(supported_formats): # Checking the extension
				event.acceptProposedAction()  # We only accept audio files
			else:
				event.ignore() # Ignore if these are not audio files
		else:
			event.ignore()

	def dropEvent(self, event: QDropEvent):
		if event.mimeData().hasUrls():
			urls = event.mimeData().urls()
			if len(urls) == 1:
				audio_file = urls[0].toLocalFile()
				render.label.setText("Accepted. Processing..")
				global this_file
				this_file = FileClass(audio_file)
				render.redraw_required = True
				#progress_bar = QProgressBar()
				#progress_bar.setRange(0, 0)  # Устанавливаем бесконечный режим
				#self.layout.addWidget(progress_bar)
		event.acceptProposedAction()
	# - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = -

	def redraw_spectrogram(self):
		print("Redrawing..")
		render.width = self.frameGeometry().width()
		render.height = self.frameGeometry().height()
		render.pixmap.loadFromData(make_spectrogram(render.width, render.height))
		render.label.setPixmap(render.pixmap)
		#render.label.setFixedSize(self.sizeHint())
		print("Redraw complete!")

app = QApplication(sys.argv)
w = MainWindow()

tick_handler = Thread(target=def_tick_handler, daemon=True)
tick_handler.start()

w.show()
sys.exit(app.exec())
