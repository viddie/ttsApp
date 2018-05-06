import subprocess
import os
import wave
import time
import pafy

import sounddevice as sd
import soundfile as sf
import numpy as np

from googletrans import Translator
from gtts import gTTS

process = None
srcLang = "detect"
destLang = "none"
audioDevice = -1
volume = 1.0

lastAction = ""


toggleFullAudio = None
toggleFrequency = 0
toggleTitle = None
toggleStartTime = None
toggleOffset = 0
toggleDuration = None
toggleState = "none"        #none playing paused


def main():
    load()

    terminated = False
    retMessage = ""
    
    while terminated == False:

        showMenu(retMessage)
        option = input("Option: ")

        if(option == ""):
            confirm = input("\nDo you really want to exit?\nType <y> to confirm, type anything else to go back: ")
            if(confirm == "y"):
                terminated = True
                save()
        elif(option == "t"):
            retMessage = playTTS()
        elif(option == "w"):
            retMessage = playWav()
        elif(option == "p"):
            retMessage = togglePause()
        elif(option == "s"):
            retMessage = stopPlayback()
        elif(option == "f"):
            retMessage = fastForward()
        elif(option == "u"):
            retMessage = status()
        elif(option == "l"):
            retMessage = performLastAction()
        elif(option == "v"):
            retMessage = setPlaybackVolume()
        elif(option == "e"):
            retMessage = setPlaybackSpeed()
        elif(option == "y"):
            retMessage = downloadYoutubeAudio()
        elif(option == "c"):
            retMessage = setSrcLang()
        elif(option == "d"):
            retMessage = setDestLang()
        elif(option == "a"):
            retMessage = setAudioDevice()
        elif(option == "o"):
            retMessage = listSettings()
            


def playTTS():
    if(audioDevice == -1):
        return "Please setup an audio device first!"
    
    print("--(1) Text-To-Speech--")
    print("Enter any text that you want to have read out to the audio device (<Enter> to exit)")
    print("Language: {} -> {}\n".format(srcLang, destLang))

    exited = False
    while(exited == False):

        ttsText = input("Anything: ")

        if(ttsText == ""):
            exited = True
            return ""

        global lastAction
        lastAction = "tts:({}->{}){}".format(srcLang, destLang, ttsText)
        save()

        translator = Translator()

        if(srcLang == "detect"):
            fromLang = translator.detect(ttsText).lang
        else:
            fromLang = srcLang

        if(destLang == "none"):
            speakLang = srcLang
        else:
            ttsText = translator.translate(ttsText, src=fromLang, dest=destLang).text
            speakLang = destLang

        duration = play_tts(ttsText, audioDevice, language=speakLang)

        startToggle(duration)

        print("\nExecuting text-to-speech...\nText: '{}'\nDuration: {} seconds\n\n".format(ttsText, round(duration, 3)))


def playWav():
    if(audioDevice == -1):
        return "Please setup an audio device first!"
    
    print("--(1) Play Wav File--")
    print("Enter the filename of the file you want to play (<Enter> to exit)")
    print("(Hint: You don't need to write .wav at the end, but write .mp3 for mp3 files!)\n")

    exited = False
    while(exited == False):
        filenameUn = input("Filename: ")

        if(filenameUn == ""):
            exited = True
            return ""

        if(not filenameUn.endswith(".wav") and not filenameUn.endswith(".mp3")):
            filename = "{}.wav".format(filenameUn)
        else:
            filename = filenameUn

        try:
            file = open(filename, "r")
            file.close()
        except:
            return ""

        duration = play_wav(filename, audioDevice, playbackSpeed=speed, playbackVolume=volume)
        
        startToggle(duration)

        print("\nPlaying file '{}'\nDuration: {} seconds\n\n".format(filename, round(duration, 3)))

        global lastAction
        lastAction = "wav:{}".format(filename)
        save()


def togglePause():
    global toggleStartTime
    global toggleDuration
    global toggleState
    global toggleTitle
    global toggleOffset
    
    if(toggleState == "none"):        #none playing paused
        return "You can't pause here as no music is currently playing."

    elif(toggleState == "playing"):
        endTime = time.time()
        sd.stop()

        addedOffset = (endTime - toggleStartTime) * (toggleFrequency * speed)
        
        if(addedOffset + toggleOffset >= toggleFullAudio.size):
            stopToggle()
            return "You can't pause here as the music is already over."

        toggleOffset += addedOffset
        toggleState = "paused"
        return "Playback paused - {}s / {}s".format(round(toggleOffset / toggleFrequency, 1), round(toggleFullAudio.size / toggleFrequency, 1))
    
    elif(toggleState == "paused"):
        data = np.copy(toggleFullAudio)[int(toggleOffset):]
        data *= volume
        sd.play(data, toggleFrequency * speed, device=audioDevice)
        
        toggleStartTime = time.time()
        toggleState = "playing"

        return "Continued playing - {}s / {}s".format(round(toggleOffset / toggleFrequency, 1), round(toggleFullAudio.size / toggleFrequency, 1))

def startToggle(duration):
    global toggleStartTime
    global toggleDuration
    global toggleState
    global toggleOffset

    toggleStartTime = time.time()
    toggleDuration = duration
    toggleState = "playing"
    toggleOffset = 0

def stopToggle():
    global toggleStartTime
    global toggleDuration
    global toggleState
    global toggleOffset
    global toggleTitle

    toggleStartTime = None
    toggleDuration = None
    toggleState = "none"
    toggleOffset = 0
    toggleTitle = None

def stopPlayback():
    sd.stop()
    stopToggle()
    
    return "If there was something playing right now, it was stopped."



def performLastAction():
    global toggleTitle
    
    localAction = lastAction
    
    if(localAction.startswith("tts:")):#"tts:(de->en)Hallo das ist eine Nachricht"
        localAction = lastAction[5:]
        
        fromLang = localAction[0:localAction.find("->")]
        toLang = localAction[localAction.find("->")+2:localAction.find(")")]
        ttsText = localAction[localAction.find(")")+1:]
        
        translator = Translator()

        if(fromLang == "detect"):
            fromLang = translator.detect(ttsText).lang

        if(toLang == "none"):
            speakLang = fromLang
        else:
            ttsText = translator.translate(ttsText, src=fromLang, dest=toLang).text
            speakLang = toLang

        duration = play_tts(ttsText, audioDevice, language=speakLang)
        startToggle(duration)
        
        toggleTitle = "tts.wav"

        return "Executing text-to-speech...\nText: '{}'\nDuration: {} seconds".format(ttsText, round(duration, 3))
    
    elif(localAction.startswith("wav:")):#"wav:The Dawn - Dreamtale.wav"
        filename = localAction[4:]
        
        duration = play_wav(filename, audioDevice, playbackSpeed=speed, playbackVolume=volume)
        startToggle(duration)
        
        toggleTitle = filename

        return "Playing file '{}'\nDuration: {} seconds".format(filename, duration)



def setPlaybackVolume():
    global volume
    
    print("--(v) Playback Volume--")
    print("Enter the playback volume level (<Enter> to exit)\nCurrent volume: {}\n".format(volume))

    exited = False
    
    while exited == False:
        strIn = input("Volume Level: ")

        if(strIn == ""):
            exited = True
            returnMsg = ""
        else:
            try:
                num = float(strIn)
                if(num < 0):
                    raise Exception()
            except:
                print("{} is not a valid positive number")
            else:
                volume = num
                save()
                exited = True

                if(toggleState == "playing"):
                    togglePause()
                    togglePause()
                
                returnMsg = "Set playback volume level to <{}>".format(num)

    return returnMsg



def setPlaybackSpeed():
    global speed
    
    print("--(e) Playback Speed--")
    print("Enter the playback speed (<Enter> to exit)\nCurrent speed: {}\n".format(speed))

    exited = False
    
    while exited == False:
        strIn = input("Speed: ")

        if(strIn == ""):
            exited = True
            returnMsg = ""
        else:
            try:
                num = float(strIn)
                if(num < 0):
                    raise Exception()
            except:
                print("{} is not a valid positive number")
            else:
                if(toggleState == "playing"):
                    togglePause()
                    speed = num
                    togglePause()
                else:
                    speed = num
                save()
                exited = True
                returnMsg = "Set playback speed to <{}>".format(num)

    return returnMsg




def fastForward():
    global toggleOffset
    
    print("--(f) Fast Forward--")
    print("Enter fast forward expression (<Enter> to exit)\n(Hint: Regex -> [=]<num>[s/%])\n".format(speed))


    strIn = input("Speed: ")

    if(strIn == ""):
        return ""

    if(strIn.startswith("=")):
        relative = False
        strIn = strIn[1:]
    else:
        relative = True

    if(strIn.endswith("s")):
        unit = "seconds"
    elif(strIn.endswith("%")):
        unit = "percent"
    else:
        return "Invalid fast forward expression: End the input with 's' for seconds or '%' for percentage!"

    strIn = strIn[0:-1]

    if(strIn == ""):
        return "Please enter a number to fast forward to!"

    try:
        value = float(strIn)
    except:
        return "Invalid number given '{}'".format(strIn)

    togglePause()

    if(relative == True):
        if(unit == "seconds"):
            skippedFrames = value * toggleFrequency
        elif(unit == "percent"):
            skippedFrames = (value / 100) * toggleFullAudio.size

        newOffset = toggleOffset + skippedFrames
        
    else:
        if(unit == "seconds"):
            newOffset = value * toggleFrequency
        elif(unit == "percent"):
            newOffset = (value / 100) * toggleFullAudio.size

    if(newOffset < 0):
        togglePause()
        return "You are trying to skip to before the song even started o_o"
    elif(newOffset > toggleFullAudio.size):
        togglePause()
        return "The song would already be over if you skipped to there..."

    toggleOffset = newOffset
    togglePause()

    return "Fast forwarded!"
            
    


def status():
    if(toggleState == "none"):
        return "Nothing is playing atm!"

    elif(toggleState == "playing"):
        nowTime = time.time()

        addedOffset = (nowTime - toggleStartTime) * (toggleFrequency * speed)

        currentOffset = toggleOffset + addedOffset

        return "Currently playing '{}'\n - {}s / {}s".format(toggleTitle, round(currentOffset / toggleFrequency, 1), round(toggleFullAudio.size / toggleFrequency, 1))

    elif(toggleState == "paused"):
        return "Currently playing '{}'\n - {}s / {}s".format(toggleTitle, round(toggleOffset / toggleFrequency, 1), round(toggleFullAudio.size / toggleFrequency, 1))

    else:
        return "What the f happened here?"

def downloadYoutubeAudio():
    global srcLang
    
    print("--(y) Youtube Download--")
    print("Enter the youtube video url\n")

    exited = False

    try:
    
        while exited == False:
            strIn = input("Youtube url: ")

            if(strIn == ""):
                exited = True
                returnMsg = ""
            else:
                pafy.set_api_key("AIzaSyDVjran_F6QGMjqLNx6VUzhC1N6BbYJWDw")

                url = strIn
                video = pafy.new(url)            
                bestaudio = video.getbestaudio()

                
                extension = bestaudio.extension


                print("Video title: '{}'".format(video.title))
                strIn = input("Enter new title(<Enter> for no change, 'exit' to cancel): ")


                if(strIn == ""):
                    newTitle = video.title.lower()
                elif(strIn == "exit"):
                    exited = True
                    return "Canceled download of '{}'.".format(video.title)
                else:
                    newTitle = strIn

                

                pathToFile = "{}.{}".format(os.path.join(os.path.dirname(__file__), newTitle), extension)
                #input("Path: {}".format(pathToFile))
                
                bestaudio.download(filepath=pathToFile)

                p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "quiet", "-i",  "{}.{}".format(newTitle, extension), "-acodec", "pcm_s16le", "-ac", "1", "-ar", "16000", "{}.wav".format(newTitle)])

                while(p.poll() == None):
                    time.sleep(0.01)

                os.remove(pathToFile)

                exited = True
                return "Download complete!\nAudio from '{}' saved as '{}'".format(video.title, newTitle)
    except:
        return "A pafy exception occurred!"
            

    return "Some weird error happened here..."




def setSrcLang():
    global srcLang
    
    print("--(c) Source Language--")
    print("Enter the abbreviated source language you want to use(<Enter> to exit)\n(Hint: If you want to detect the language automatically, type 'detect')\n")

    exited = False
    
    while exited == False:
        strIn = input("Source Language: ")

        if(strIn == ""):
            exited = True
            returnMsg = ""
        elif(strIn == "detect"):
            exited = True
            srcLang = strIn
            returnMsg = "Set source language as <detect>"
        else:
            translator = Translator()
            try:
                strTrans = translator.translate("This is a sample text", dest=strIn)
            except:
                print("The language <{}> is not accepted by google translator, please try again...\n".format(strIn))
            else:
                srcLang = strIn
                save()
                exited = True
                returnMsg = "Set source language as <{}>".format(strIn)            

    return returnMsg

def setDestLang():
    global destLang
    
    print("--(d) Destination Language--")
    print("Enter the abbreviated destination language you want to use(<Enter> to exit)\n(Hint: If you don't want a translation, type 'none')\n")

    exited = False
    
    while exited == False:
        strIn = input("Destination Language: ")

        if(strIn == ""):
            exited = True
            returnMsg = ""
        elif(strIn == "none"):
            exited = True
            destLang = strIn
            returnMsg = "Set destination language as <none>"
        else:
            translator = Translator()
            try:
                strTrans = translator.translate("This is a sample text", dest=strIn)
            except:
                print("The language <{}> is not accepted by google translator, please try again...\n".format(strIn))
            else:
                destLang = strIn
                save()
                exited = True
                returnMsg = "Set destination language as <{}>".format(strIn)            

    return returnMsg


def setAudioDevice():
    global audioDevice
    
    print("--(a) Audio Device--")
    input("Hit enter to load a list of all audio devices, then select your desired output device (<Enter> to exit)\n(Hint: '>' marks your default input, '<' your default output device)")
    print(sd.query_devices())

    exited = False
    
    while exited == False:
        strIn = input("Audio Device: ")

        if(strIn == ""):
            exited = True
            returnMsg = ""
        else:
            try:
                num = int(strIn)
                if(num < 0):
                    raise Exception()
            except:
                print("{} is not a valid positive integer")
            else:
                audioDevice = num
                save()
                exited = True
                returnMsg = "Set audio device to <{}>".format(num)

    return returnMsg


def listSettings():
    returnMsg = "srcLang = {}\ndestLang = {}\naudioDevice = {}\nlastAction = {}\nvolume = {}\nspeed = {}".format(srcLang, destLang, audioDevice, "-None-" if lastAction == "" else lastAction, volume, speed)
    return returnMsg


def showMenu(postClearMsg=""):
    os.system('cls')
    print("Select what you want to do (<Enter> to exit):")
    print("")
    print("'t' - Write text for TTS")
    print("'w' - Play a .wav file")
    print("'p' - {} playback".format("Pause" if toggleState == "playing" else ("Unpause" if toggleState == "paused" else "Pause/Unpause")))
    print("'s' - Stop current playback")
    print("'f' - Fastforward playback")
    print("'l' - Play last playback")
    print("'v' - Set playback volume")
    print("'e' - Set playback speed")
    print("'c' - Set src language")
    print("'y' - Download audio from youtube")
    print("'d' - Set dest language")
    print("'a' - Set audio device")
    print("'o' - List all settings")
    print("")

    if(postClearMsg != ""):
        print(postClearMsg)
        print("")


def load():
    try:
        file = open("settings.txt", "r")
    except:
        file = open("settings.txt", "w")
        file.write("srcLang=detect\n")
        file.write("destLang=none\n")
        file.write("audioDevice=-1\n")
        file.write("lastAction=-None-\n")
        file.write("volume=1.0\n")
        file.write("speed=1.0\n")
        file.close()
        file = open("settings.txt", "r")


    for line in file:
        line = line.rstrip()
        (varName, varVal) = line.split("=", 1)

        if(varName == "srcLang"):
            global srcLang
            srcLang = varVal
            
        elif(varName == "destLang"):
            global destLang
            destLang = varVal
            
        elif(varName == "audioDevice"):
            global audioDevice
            try:
                num = int(varVal)
            except:
                num = -1
            audioDevice = num
            
        elif(varName == "lastAction"):
            global lastAction
            if(varVal == "-None-"):
                lastAction = ""
            else:
                lastAction = varVal
            
        elif(varName == "volume"):
            global volume
            try:
                num = float(varVal)
            except:
                num = -1
            volume = num
            
        elif(varName == "speed"):
            global speed
            try:
                num = float(varVal)
            except:
                num = -1
            speed = num
                
        else:
            print("Variable '{}' with value '{}' is invalid.".format(varName, varVal))
    file.close()



def save():
    file = open("settings.txt", "w")
    file.write("srcLang={}\n".format(srcLang))
    file.write("destLang={}\n".format(destLang))
    file.write("audioDevice={}\n".format(audioDevice))
    file.write("lastAction={}\n".format("-None-" if lastAction == "" else lastAction))
    file.write("volume={}\n".format(volume))
    file.write("speed={}\n".format(speed))
    file.close()
        

def play_tts(string, device, language="de"):
    tts = gTTS(text=string, lang=language)
    tts.save("tts.mp3")

    return play_wav("tts.mp3", device, playbackSpeed=speed, playbackVolume=volume)

def play_wav(filename, device, noDuration=False, playbackSpeed=1, playbackVolume=1):
    global duration
    global starTime
    global toggleFullAudio
    global toggleFrequency
    
    if(filename.endswith(".mp3")):#"asd.dsd.mp3" -> ".".join(str.split(".")[0:-2])
        if(len(filename.split(".")) > 2):
            wavFilename = "{}.wav".format(".".join(filename.split(".")[0:-2]))
        else:
            wavFilename = "{}.wav".format(filename.split(".")[0])
        
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "quiet", "-i",  filename, "-acodec", "pcm_s16le", "-ac", "1", "-ar", "16000", wavFilename])

        while(p.poll() == None):
            time.sleep(0.01)

        filename = wavFilename

    if(not filename.endswith(".wav")):
        print("Unsupported filetype of file '{}'".format(filename))
        return

    data, fs = sf.read(filename, dtype="float64")
    toggleFullAudio = np.copy(data)
    toggleFrequency = fs
    sd.play(data * playbackVolume, int(fs * playbackSpeed), device=audioDevice)

    global toggleTitle
    toggleTitle = filename

    return get_duration_wav(filename)


def get_duration_wav(wav_filename):
    f = wave.open(wav_filename, 'r')
    frames = f.getnframes()
    rate = f.getframerate()
    duration = frames / float(rate * speed)
    f.close()
    return duration



#Sound transformations

'''def speedx(sound_array, factor):
     """Multiplies the sound's speed by some `factor` """
    indices = np.round( np.arange(0, len(sound_array), factor) )
    indices = indices[indices < len(sound_array)].astype(int)
    return sound_array[ indices.astype(int) ]'''


#data, fs = sf.read("despacito frenchcore.wav", dtype="float32")
#data = data[232000:]
#sd.play(data, fs, device=8)

#print("Titel: despacito frenchcore.wav\ntype(data) '{}' data '{}'\ntype(fs) '{}' fs '{}'\n\n".format(type(data), data, type(fs), fs))
#print("ndim '{}' shape '{}' size '{}' dtype '{}'".format(data.ndim, data.shape, data.size, data.dtype))
#input()

main()
