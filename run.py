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
    os.system("touch state/tts.on")
    tts_speech = ""
    a11y_control_prompt = a11y_control_prompt.replace("<input>", "You are on Uber Eats app. The app is already open. Add a pizza to the cart.")
    # adb_device.launch_app("com.ubercab.eats")
    contexted = False
    for sentence in get_tts_word(tts_pkg):
        if sentence:
            tts_speech += sentence
        else:
            print("TTS: ", tts_speech)
            if not contexted:
                a11y_control_prompt = a11y_control_prompt.replace("<tts_output>", tts_speech)
                llm_response = llm.send_message(a11y_control_prompt)
                contexted = True
            else:
                llm_response = llm.send_message("Screen Reader Output: "+tts_speech)
            action_data = llm.parse_response(llm_response)
            if action_data['action'] == 'finish':
                print("Task completed.")
                exit()
            elif action_data['action'] == 'ally_action':
                adb_device.ally_action(action_data['data'])
            elif action_data['action'] == 'input_text':
                adb_device.input_text(action_data['data'])
            elif action_data['action'] == None:
                print("Error: No action defined.")
                exit()

            tts_speech = ""
            os.system("touch state/tts.on")
            
