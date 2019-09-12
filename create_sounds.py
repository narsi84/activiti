from gtts import gTTS
import string

chars = string.ascii_uppercase + string.digits

for char in chars:
	tts = gTTS(char)
	print(char)
	tts.save(f'assets_wav/{char}.wav')

sounds = {
	'learn': 'Learn mode! Press an item to learn more!',
	'settings': 'Enter the code on the game card. Then press "Enter".',
	'play': 'Play mode!',
	'game_not_found': 'No such game found',
}

for s in sounds:
	tts = gTTS(sounds[s])
	print(s)
	tts.save(f'assets_wav/{s}.wav')
