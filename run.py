import os, subprocess, IPython
import adbUI


# Get ADB devices
def get_devices():
    devices = subprocess.check_output("adb devices", shell=True).decode("utf-8")
    IPython.embed()
    # devices.split('\t')[0].split('\n')[1]
    
get_devices()