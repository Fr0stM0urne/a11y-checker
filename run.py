import os, sys, subprocess, configparser, time, glob, IPython
from tts_reader import get_tts_word
from adb_a11y import adb_a11y
from llms import openai_gpt, google_gemini, anthropic_claude
from prompts import a11y_control_prompt
from multiprocessing import Process

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

def show_usage():
    print(f"Usage: python3 {sys.argv[0]}")
    print("--- config.ini ---")
    llmList = ["openai", "google", "anthropic"]
    print("<llm_provider> = "+", ".join(llmList))
    sys.exit(1)

def read_config():
    try:
        config = configparser.ConfigParser()
        config.read('config.ini')
        os.system("rm -rf state")
        os.system("mkdir state")
        return config
    except Exception as e:
        print(f"Error reading config: {str(e)}")
        show_usage()

def setup_llm(llm_provider, llm):
    if llm_provider == 'openai':
        llm = openai_gpt(llm)
    elif llm_provider == 'google':
        llm = google_gemini(llm)
    elif llm_provider == 'anthropic':
        llm = anthropic_claude(llm)
    else:
        show_usage()
    return llm

if __name__ == "__main__":
    adb_device = adb_a11y(get_devices())
    config = read_config()
    llm = setup_llm(config.get('a11y', 'llm_provider'), config.get('a11y', 'llm'))
    # Intercept TTS messages
    print("Starting TTS logcat interception...")
    tts_pkg = config.get('a11y', 'tts_pkg')
    
    for sentence in get_tts_word(tts_pkg):
        print(sentence)

    print(llm.send_message(a11y_control_prompt + "Please give 3 random ally action"))

