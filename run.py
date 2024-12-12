import os, subprocess, IPython
from tts_reader import get_tts_word
from adb_a11y import adb_a11y

# Get ADB devices
def get_devices():
    adbOut = subprocess.check_output("adb devices", shell=True).decode("utf-8")
    devices = adbOut.split('attached\n')
    if len(devices) > 1:
        devices = devices[1].split('\tdevice\n')[:-1]
    else:
        print("Error: No devices attached")
        return None

    if len(devices) > 1:
        print("Error: Multiple devices attached")
        print(devices)
        return None
    
    print("Device found:", devices[0])
    return devices[0]

if __name__ == "__main__":
    adbDevice = adb_a11y(get_devices())
    pkg = 'com.android.talkback4d'
    get_tts_word(pkg)

