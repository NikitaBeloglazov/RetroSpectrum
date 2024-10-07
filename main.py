import os
import sys
import time
import copy
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

from PySide6.QtWidgets import QMenuBar, QFileDialog
from PySide6.QtGui import QAction, QKeySequence, QActionGroup

from PySide6.QtGui import QIcon

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
		self.base_filename = os.path.basename(media_file)

	def open_file(self, filename):
		""" Opens a new file and reinitializes class """

		# To be honest, I don't understand what this is and what kind of warning,
		# and what they're talking about in relevant issues.
		# https://github.com/pylint-dev/pylint/issues/6889
		# https://github.com/pylint-dev/pylint/issues/8082
		self.__init__(filename) # pylint: disable=unnecessary-dunder-call

		render.redraw_required = True
		render.progress_bar.setVisible(True)

file_controller = FileClass(media_file)

# - = - = - = - = - = - = - = - = - = - = -

class DrawClass():
	def __init__(self):
		self.default_variables = {
			"contrast": {"current": 80, "min": 20, "max": 180}, # -z num  Z-axis range in dB; default 120
			"channels": {"current": 1, "min": 1, "max": 2},		# remix
			"color":	{"current": 1, "min": 1, "max": 6},	 # -p num  Permute colours (1 - 6); default 1
			"maxdBFS":  {"current": 0, "min": -100, "max": 100}, # -Z num  Z-axis maximum in dBFS; default 0
				}
		self.variables = copy.deepcopy(self.default_variables)

	def reset(self):
		""" Resets variables to default values """
		self.variables = copy.deepcopy(self.default_variables)

draw = DrawClass()

# - = - = - = - = - = - = - = - = - = - = -


def make_spectrogram(width, height):
	# - = - = - = - = - = - = -
	print("Drawing...")

	# - Command generator = - = - = - = - = - =
	sox_command = [
		'sox', file_controller.filename, '-n', # base command
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
	sox_command.append(file_controller.ffmpeg_text)
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

	img_data = proc.stdout.read()

	print("Postprocessing..")
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

def def_tick_redraw_handler():
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

def def_tick_handler():
	while True:
		# - = - = - = - = - = - = - = - = -
		# - = Window title definer
		if render.redraw_required_message is not None:
			render.main_window.setWindowTitle(f"RetroSpectrum — {render.redraw_required_message} — {file_controller.base_filename}")
		else:
			render.main_window.setWindowTitle("RetroSpectrum — " + file_controller.base_filename)
		# - = - = - = - = - = - = - = - = -
		time.sleep(0.1)

class RenderClass():
	def __init__(self):
		self.redraw_required = False
		self.redraw_required_message = None
		self.redraw_required_message_ticks = 0
render = RenderClass()

class PaletteButtonsClass():
	def __init__(self, main_window):
		self.main_window = main_window
		self.color_switch = QAction("Switch to next", main_window)
		self.color_switch.setShortcut(QKeySequence("C"))
		self.color_switch.triggered.connect(lambda: self.set_color())

		self.colors_group = QActionGroup(main_window)
		self.colors_group.setExclusive(True)
		self.colors = []

		self.color_1 = QAction("Yellow - Red - Pink", main_window)
		self.color_1.setCheckable(True)
		self.color_1.setChecked(True)
		self.color_1.triggered.connect(lambda: self.set_color(1))
		self.colors.append(self.color_1)

		self.color_2 = QAction("Green - Blue", main_window)
		self.color_2.setCheckable(True)
		self.color_2.triggered.connect(lambda: self.set_color(2))
		self.colors.append(self.color_2)

		self.color_3 = QAction("Green - Brown", main_window)
		self.color_3.setCheckable(True)
		self.color_3.triggered.connect(lambda: self.set_color(3))
		self.colors.append(self.color_3)

		self.color_4 = QAction("Pink - Dark Green", main_window)
		self.color_4.setCheckable(True)
		self.color_4.triggered.connect(lambda: self.set_color(4))
		self.colors.append(self.color_4)

		self.color_5 = QAction("Blue - Green", main_window)
		self.color_5.setCheckable(True)
		self.color_5.triggered.connect(lambda: self.set_color(5))
		self.colors.append(self.color_5)

		self.color_6 = QAction("Blue - Magenta", main_window)
		self.color_6.setCheckable(True)
		self.color_6.triggered.connect(lambda: self.set_color(6))
		self.colors.append(self.color_6)

		self.color_reset = QAction("Reset", main_window)
		self.color_reset.triggered.connect(lambda: main_window.setting_change("color", "reset"))

		# Add to menu
		main_window.color_menu_bar.addAction(self.color_switch)
		main_window.color_menu_bar.addSeparator()

		for i in self.colors:
			self.colors_group.addAction(i)
			main_window.color_menu_bar.addAction(i)

		"""
		main_window.color_menu_bar.addAction(self.color_1)
		main_window.color_menu_bar.addAction(self.color_2)
		main_window.color_menu_bar.addAction(self.color_3)
		main_window.color_menu_bar.addAction(self.color_4)
		main_window.color_menu_bar.addAction(self.color_5)
		main_window.color_menu_bar.addAction(self.color_6)
		"""

		main_window.color_menu_bar.addSeparator()
		main_window.color_menu_bar.addAction(self.color_reset)

	def set_color(self, color_id=None):
		if color_id is not None:
			self.main_window.setting_change("color", "set", color_id)
		else:
			self.main_window.setting_change("color", "carousel")
		self.update()

	def update(self):
		for i in self.colors:
			i.setChecked(False)

		print(self.colors)

		self.colors[draw.variables["color"]["current"] - 1].setChecked(True)

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

		render.progress_bar = QProgressBar()
		render.progress_bar.setWindowTitle("RetroSpectrum - Processing..")
		render.progress_bar.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint | Qt.SubWindow | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
		render.progress_bar.setFixedSize(200, 38)
		render.progress_bar.setRange(0, 0)  # Infinite mode
		render.progress_bar.setVisible(False)

		# - = - = - = - = - = - = - = - = - = - = -
		# Drag-n-drop layout
		self.layout = QVBoxLayout()
		self.layout.addWidget(render.label)
		self.layout.addWidget(render.progress_bar) # progress_bar

		self.setLayout(self.layout)
		# - = - = - = - = - = - = - = - = - = - = -

		# - = - = - = - = - = - = - = - = - = - = -
		# Menubar (Alt/File menu under window title)
		self.menu_bar = self.menuBar()

		# - = - =

		# Add category "File"
		self.file_menu_bar = self.menu_bar.addMenu("File")

		open_action = QAction("Open", self)
		open_action.setShortcuts([QKeySequence("O"), QKeySequence("Ctrl+O")])
		open_action.triggered.connect(self.open_file)

		exit_action = QAction("Exit", self)
		exit_action.setShortcuts([QKeySequence("Esc"), QKeySequence("Ctrl+Q")])
		exit_action.triggered.connect(self.close)

		# Add to menu
		self.file_menu_bar.addAction(open_action)
		self.file_menu_bar.addSeparator()  # Разделитель
		self.file_menu_bar.addAction(exit_action)

		# - = - =

		# Add category "View"
		self.view_menu_bar = self.menu_bar.addMenu("View")

		# - = - =

		contrast = QAction("Contrast", self)
		contrast.triggered.connect(lambda: self.setting_change("contrast", "reset"))

		contrast_plus = QAction("+", self)
		contrast_plus.setShortcut(QKeySequence("2"))
		contrast_plus.triggered.connect(lambda: self.setting_change("contrast", "plus"))

		contrast_minus = QAction("-", self)
		contrast_minus.setShortcut(QKeySequence("1"))
		contrast_minus.triggered.connect(lambda: self.setting_change("contrast", "minus"))

		# Add to menu
		self.view_menu_bar.addAction(contrast)
		self.view_menu_bar.addAction(contrast_plus)
		self.view_menu_bar.addAction(contrast_minus)

		# - = - =
		self.view_menu_bar.addSeparator()
		# - = - =

		maxdBFS = QAction("maxdBFS", self)
		maxdBFS.triggered.connect(lambda: self.setting_change("maxdBFS", "reset"))

		maxdBFS_plus = QAction("+", self)
		maxdBFS_plus.setShortcut(QKeySequence("4"))
		maxdBFS_plus.triggered.connect(lambda: self.setting_change("maxdBFS", "plus"))

		maxdBFS_minus = QAction("-", self)
		maxdBFS_minus.setShortcut(QKeySequence("3"))
		maxdBFS_minus.triggered.connect(lambda: self.setting_change("maxdBFS", "minus"))

		# Add to menu
		self.view_menu_bar.addAction(maxdBFS)
		self.view_menu_bar.addAction(maxdBFS_plus)
		self.view_menu_bar.addAction(maxdBFS_minus)

		# - = - =
		self.view_menu_bar.addSeparator()
		# - = - =

		self.color_menu_bar = self.menu_bar.addMenu("Palette")
		PaletteButtonsClass(self)

		channels = QAction("Show multiple channels", self)
		channels.setCheckable(True)
		channels.setShortcut(QKeySequence("S"))
		channels.triggered.connect(lambda: self.setting_change("channels", "set", value=1+channels.isChecked()))

		# Add to menu
		self.view_menu_bar.addAction(channels)

		# - = - = - = - = - = - = - = - = - = - = -

		# Minimum sox image size
		self.setMinimumSize(100+144, 130)

		self.setCentralWidget(render.label)
		#self.resize(pixmap.width(), pixmap.height())

	def keyPressEvent(self, event):
		# Force redraw
		if event.key() == Qt.Key_Y:
			render.redraw_required = True
		if event.key() == Qt.Key_R:
			draw.reset()
			render.redraw_required = True
			render.redraw_required_message = "The settings have been reset"
			render.redraw_required_message_ticks = 30

		# - = - = - = - = - = - = - = - = - = - = -
		# channels
		#if event.key() == Qt.Key_C:
		#	self.setting_change("color", "carousel")
		# - = - = - = - = - = - = - = - = - = - = -

	def setting_change(self, setting, action, value=None):
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
		elif action == "reset":
			# Reset to default variables
			draw.variables[setting]["current"] = draw.default_variables[setting]["current"]
		elif action == "set":
			# Manually set value
			draw.variables[setting]["current"] = value

		print("\n\n" + str(draw.variables))
		render.redraw_required = True
		if action == "plus":
			symbol = "+"
		elif action == "minus":
			symbol = "-"
		elif action == "carousel" or action == "set":
			symbol = ">"
		elif action == "reset":
			symbol = "reset"

		render.redraw_required_message = f"Setting \"{setting}\" changed: [{symbol}] {draw.variables[setting]['current']}"
		render.redraw_required_message += f" (min {draw.variables[setting]['min']} / max {draw.variables[setting]['max']})"
		render.redraw_required_message_ticks = 30

	# - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = -
	# Drag-n-drop support
	def dragEnterEvent(self, event: QDragEnterEvent):
		if event.mimeData().hasUrls():  # Check that the data contains URLs (files)
			urls = event.mimeData().urls()
			if len(urls) == 1 and urls[0].toString().endswith(supported_formats): # Checking the extension
				event.acceptProposedAction()  # We accept only audio files
			else:
				event.ignore() # Ignore if these are not audio files
		else:
			event.ignore()

	def dropEvent(self, event: QDropEvent):
		if event.mimeData().hasUrls():
			urls = event.mimeData().urls()
			if len(urls) == 1:
				audio_file = urls[0].toLocalFile()
				global file_controller
				file_controller.open_file(audio_file)

		event.acceptProposedAction()
	# - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = -

	def open_file(self):
		# Open dialog
		file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*.*)")

		# Если файл выбран, сохраняем путь в переменную
		if file_path:
			print(f"File selected: {file_path}")
			global file_controller
			file_controller.open_file(file_path)

	def redraw_spectrogram(self):
		print("Redrawing..")
		render.width = self.frameGeometry().width()
		render.height = self.frameGeometry().height()
		render.pixmap.loadFromData(make_spectrogram(render.width, render.height))
		render.label.setPixmap(render.pixmap)
		#render.label.setFixedSize(self.sizeHint())
		if hasattr(render, 'progress_bar'):
			render.progress_bar.setVisible(False)
		print("Redraw complete!")

app = QApplication(sys.argv)

# - = - = - = - = - = - = - = - = -
# - = Pre-setting icon finder
QIcon.setFallbackSearchPaths([
	os.path.expanduser("~/.local/share/icons/"), # standart UNIX path
	"/usr/share/icons/",                         # standart UNIX path
	os.path.dirname(os.path.realpath(__file__)) + "/resources/"
	# get currently running script path, gather directly from module folder/etc
])
QIcon.setFallbackThemeName("hicolor")
# - = - = - = - = - = - = - = - = -
# - = Set icon
icon = QIcon.fromTheme("RetroSpectrum")
if not icon.isNull():
	app.setWindowIcon(icon)
else:
	print("Get RetroSpectrum icon failed, seems icon not found!")
# - = - = - = - = - = - = - = - = -

w = MainWindow()
render.main_window = w

tick_handler = Thread(target=def_tick_handler, daemon=True)
tick_handler.start()
tick_redraw_handler = Thread(target=def_tick_redraw_handler, daemon=True)
tick_redraw_handler.start()

w.show()
sys.exit(app.exec())
