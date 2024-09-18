""" Module that responsible for contolling ffmpeg/ffprobe checks and calls. """
import ffmpeg

def get_ffprobe_string(filename):
	""" Uses ffprobe to get audio info string for title """
	# - = - = - = - = - = -
	try:
		# Gets ffprobe output
		probe = ffmpeg.probe(filename)
	except ffmpeg.Error as e:
		print("Some ffprobe error occured:")
		print(e.stderr)
		return None
	# - = - = - = - = - = -
	for i in probe["streams"]:
		if "codec_type" in i:
			if i["codec_type"] == "audio":

				# - = - = - = - = - = -
				# Get bitrate
				if "bit_rate" in i:
					bitrate = i['bit_rate'] # use stream bitrate unstead file bitrate
				else:
					bitrate = probe['format']['bit_rate'] # use file bitrate
				kbit_s = round(int(bitrate)/1000)
				# - = - = - = - = - = -

				text = f"{i['codec_long_name']}, {kbit_s} kbit/s, {i['sample_rate']}Hz"

				# - = - = - = - = - = -
				# Get bits
				bits = None
				if "bits_per_raw_sample" in i:
					bits = i["bits_per_raw_sample"]
				elif "bits_per_sample" in i:
					bits = i["bits_per_sample"]
				if bits is not None and str(bits) != "0" :
					text += f", {str(bits)} bits"
				# - = - = - = - = - = -
				# Get channels count
				if "channels" in i:
					text += f", {str(i['channels'])} channels"
				# - = - = - = - = - = -
				return text
	return "Some ffprobe error occured:("
