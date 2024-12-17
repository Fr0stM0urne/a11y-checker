import os, sys, subprocess, configparser, time, glob, IPython
from tts_reader import get_tts_word, parse_ally_debug_tree, compile_a11y_tree_prompt
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
    tts_pkg = config.get('a11y', 'tts_pkg')
    # task = "You are on PlayStore app. The app is already open. Install the top popular free game from the store."
    # task = "You are on Play Books app. The app is already open. Download the first popular book on the store."
    # task = "You are on the Uber Eats app. The app is already open. Order a pizza."
    # task = "You are on the clock app. The app is already open. Set an alarm for 6:00 AM."
    # task = "You are on the YouTube app. The app is already open. Search for and play a video on how to make a pizza."
    # task = "You are on the Calendar app. The app is already open. Create an event for a party tomorrow 19th December at 10:00 AM."
    # task = "You are on the notes app. The app is already open. Create a new note with the title 'Grocery List' and add 'Milk, Bread, Eggs' to the note."
    # task = "You are on the calculator app. The app is already open. Perform a calculation of 5 plus 5."
    # task = "You are on the Expedia app. The app is already open. Book a flight from New York to Los Angeles for tomorrow."
    # task = "You are on the Uber app. The app is already open. Book a ride to the nearest airport."
    task = "You are on the Settings app. The app is alread open. Search for Bluetooth and turn it on and connect to a device."
    # task = "You are on the Amazon app. The app is already open. Search for a book titled 'The Art of War' and add it to the cart."
    a11y_control_prompt = a11y_control_prompt.replace("<input>", task)
    a11y_tree = []
    contexted = False
    tree_process = Process(target=adb_device.ally_action, args=("print_node_tree",))
    tree_process.start()
    for parsed_data in parse_ally_debug_tree(tts_pkg):
        print(f"{parsed_data=}")
        if parsed_data:
            print(parsed_data)
            a11y_tree.append(parsed_data)
        else:
            a11y_tree_prompt = compile_a11y_tree_prompt(a11y_tree)
            print(a11y_tree_prompt)
            if not contexted:
                a11y_control_prompt = a11y_control_prompt.replace("<tts_output>", a11y_tree_prompt)
                llm_response = llm.send_message(a11y_control_prompt)
                contexted = True
            else:
                llm_response = llm.send_message("Screen Reader Output:\n"+a11y_tree_prompt)
            action_data = llm.parse_response(llm_response)
            time.sleep(1)
            if action_data['action'] == 'finish':
                print("Task completed.")
                exit()
            elif action_data['action'] == 'ally_action':
                adb_device.ally_action(action_data['data'])
            elif action_data['action'] == 'input_text':
                adb_device.input_text(action_data['data'])
            elif action_data['action'] == 'tap_element':
                # print("cpprs", a11y_tree[int(action_data['data'])]['coordinates'] )
                adb_device.a11y_tap(a11y_tree[int(action_data['data'])]['coordinates'])
            elif action_data['action'] == None:
                print("Error: No action defined.")
                exit()
            time.sleep(1)
            adb_device.ally_action("print_node_tree")
        tree_process.join()























    # Intercept TTS messages
    # print("Starting TTS logcat interception...")
    # tts_speech = ""
    # os.system("touch state/tts.on")
    # adb_device.launch_app("com.ubercab.eats")
    # contexted = False
    # adb_device.ally_action("first_in_screen")
    # for sentence in get_tts_word(tts_pkg):
    #     if sentence:
    #         tts_speech = tts_speech + " " + sentence
    #     else:
    #         print("\n")
    #         print("TTS: ", tts_speech)
    #         if not contexted:
    #             a11y_control_prompt = a11y_control_prompt.replace("<tts_output>", tts_speech)
    #             llm_response = llm.send_message(a11y_control_prompt)
    #             contexted = True
    #         else:
    #             llm_response = llm.send_message("Screen Reader Output: "+tts_speech)
    #         action_data = llm.parse_response(llm_response)
            
    #         tts_speech = ""
    #         os.system("touch state/tts.on")
    #         time.sleep(1)
    #         if action_data['action'] == 'finish':
    #             print("Task completed.")
    #             exit()
    #         elif action_data['action'] == 'ally_action':
    #             adb_device.ally_action(action_data['data'])
    #         elif action_data['action'] == 'input_text':
    #             adb_device.input_text(action_data['data'])
    #         elif action_data['action'] == None:
    #             print("Error: No action defined.")
    #             exit()


            
