# TTSApp

### This is a little text-to-speech/audio playing script in python.

## Features of text-to-speech:

 - Write text and let text-to-speech say it for you
 - Say a given text in any language supported by google translate
 - Auto language detection if no other language specified
 - Optionally text translation to a different language before being played
 
## Features of audio player:

 - Play any .wav or .mp3 file (.mp3 will be converted to .wav) that is in the same folder as the ttsApp.py
 - Play/Pause/Stop at any time
 - Set audio output device (Great in combination with Virtual Audio Cable & Voicemeeter Banana, so you are able to play audio and talk at the same time)
 - Set playback speed (Warning: No sound stretching, a faster speed means higher pitch!)
 - Set playback volume (Good for cancer mixes FeelsGoodMan Clap)
 - Download audio from a youtube video through the script and convert it to .wav (Warning: Download is slow af, not recommended for longer audio)
 - Easily replay any of the last actions
 
 
## Installation

You need [python 3.0+](https://www.python.org/downloads/) as well as these dependencies:

 - [pafy](https://github.com/mps-youtube/pafy)
 - [sounddevice](https://python-sounddevice.readthedocs.io/en/0.3.10/)
 - [numpy](http://www.numpy.org/)
 - [googletrans](https://pypi.org/project/googletrans/)
 - [gtts](https://github.com/pndurette/gTTS)
 
1. After downloading and installing python, shift + rightclick on your desktop (or any folder) > "Open PowerShell here"
2. Install the dependencies via pip:
```
pip install pafy
pip install sounddevice
pip install numpy
pip install googletrans
pip install gtts
```