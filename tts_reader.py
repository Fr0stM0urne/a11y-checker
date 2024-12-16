import subprocess, os, time, glob, re

def get_pid(appPkg):
    process = subprocess.Popen(['adb', 'shell', 'pidof', '-s', appPkg], stdout=subprocess.PIPE)
    pid = process.stdout.read().decode('utf-8').strip()
    return pid

def extract_whole_sentence(line):
    if "D talkback: Actors: act()" in line:
        if "speech= action=SPEAK  text=\"" in line:
            sentence = line.split("text=\"")[1].split("\"")[0]
            return sentence
    return None

def extract_single_word(line):
    if len(line.split("talkback:")) > 1:
        if line.split("talkback:")[1].startswith(" FeedbackFragmentsIterator: onFragmentRangeStarted ,  speak word = "):
            word = line.split("talkback:")[1].split("speak word = ")[1]
            return word[:-1]+' '
    return ''

def get_tts_word(pkg):
    # Clear logcat
    os.system('adb logcat -c')
    pid = '--pid=' + get_pid(pkg)
    process = subprocess.Popen(['adb', 'logcat', pid], stdout=subprocess.PIPE)
    sentence = ''
    last_word_time = time.time()  # Track the last spoken word's time
    timeout_threshold = 5
    while True:
        if glob.glob('state/tts.on') != []:
            line = process.stdout.readline().decode('utf-8')
            current_time = time.time()
            # Timeout calculation
            time_since_last_word = current_time - last_word_time
            remaining_time = max(0, timeout_threshold - time_since_last_word)
            
            if remaining_time > 0:
                print(f"TTS Timeout {remaining_time} ...")

            if time_since_last_word > timeout_threshold:
                os.system("rm -rf state/tts.on")
                yield None

            if not line:
                break

            word = extract_single_word(line)
            if word:
                print(word)
                last_word_time = current_time  # Reset the timer when a word is spoken
                sentence += word

            if "talkback: SpeechControllerImpl: No next item, stopping speech queue" in line:
                if sentence:  # Yield the sentence if speech ends
                    yield sentence
                    sentence = ''
        else:
            time.sleep(1)

def compile_a11y_tree_prompt(a11y_tree):
    a11y_tree_prompt = ""
    for idx, node in enumerate(a11y_tree):
        current_node = str(idx) +" "+ node['text']
        if node['content']:
            current_node += f", ({node['content']})"

        a11y_tree_prompt += f"{current_node}\n"
    return a11y_tree_prompt

def parse_ally_debug_tree(pkg):
    # Clear logcat
    os.system('adb logcat -c')
    pid = '--pid=' + get_pid(pkg)
    process = subprocess.Popen(['adb', 'logcat', pid], stdout=subprocess.PIPE)
    
    parsing = False
    while True:
        line = process.stdout.readline().decode('utf-8')
        if not line:
            break

        if "TreeDebug" in line:
            if "------------Node tree------------" in line:
                parsing = True
            if "------------Node tree traversal order----------" in line:
                parsing = False
                yield None
        
            if parsing:
                input_string = line
                # Extracting fields using regex
                action_match = re.search(r'action:([^)]+)', input_string)
                custom_action_match = re.search(r'custom action:([^)]+)', input_string)
                coordinates_match = re.search(r'\((\d+),\s*(\d+)\s*-\s*(\d+),\s*(\d+)\)', input_string)
                text_match = re.search(r'TEXT{([^}]+)}', input_string)
                content_match = re.search(r'CONTENT{([^}]+)}', input_string)

                # Storing extracted values
                action = action_match.group(1) if action_match else None
                custom_action = custom_action_match.group(1) if custom_action_match else None
                coordinates = coordinates_match.group(0) if coordinates_match else None
                text = text_match.group(1) if text_match else None
                content = content_match.group(1) if content_match else None


                if action is not None:
                    action = action.split('/')
                if custom_action is not None:
                    custom_action = custom_action.split('LABEL:')[1:]

                parsed_data = {
                    "action": action,
                    "custom_action": custom_action,
                    "coordinates": coordinates,
                    "text": text,
                    "content": content
                }
                
                if parsed_data["text"] is not None and parsed_data["coordinates"] is not None:
                    yield parsed_data

# def get_tts_word(pkg):
#     # Clear logcat
#     os.system('adb logcat -c')
#     pid = '--pid=' + get_pid(pkg)
#     process = subprocess.Popen(['adb', 'logcat', pid], stdout=subprocess.PIPE)
#     sentence = ''
#     while True:
#         line = process.stdout.readline().decode('utf-8')
#         if not line:
#             break
#         if "talkback: SpeechControllerImpl: No next item, stopping speech queue" in line:
#             yield sentence
#             sentence = ''
#         sentence += extract_single_word(line)

def get_tts_sentence(pkg):    
    # Clear logcat
    os.system('adb logcat -c')
    pid = '--pid=' + get_pid(pkg)
    process = subprocess.Popen(['adb', 'logcat', pid], stdout=subprocess.PIPE)
    while True:
        line = process.stdout.readline().decode('utf-8')
        if not line:
            break
        sentence = extract_whole_sentence(line)
        if sentence:
            print(sentence)

# Note: Needs verbose logging enabled in Talkback settings
if __name__ == '__main__':
    # pkg = 'com.google.android.marvin.talkback'
    # get_tts_sentence(pkg)
    tts_pkg = 'com.android.talkback4d'
    # os.system("touch state/tts.on")
    # tts_speech = ""
    # for sentence in get_tts_word(tts_pkg):
    #     if sentence:
    #         tts_speech += sentence
    #     else:
    #         print("TTS: ", tts_speech)
    # tts_speech = ""
    # os.system("touch state/tts.on")

    # Debug Tree Parsing
    a11y_tree = []
    for parsed_data in parse_ally_debug_tree(tts_pkg):
        if parsed_data:
            a11y_tree.append(parsed_data)
        else:
            print("End of tree.")
            prompt = compile_a11y_tree_prompt(a11y_tree)
            print(prompt)
        # if parsed_data["text"]:
            # print(parsed_data)