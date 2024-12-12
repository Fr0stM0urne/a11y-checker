import subprocess, os, time, glob

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
    timeout_threshold = 3
    while True:
        if glob.glob('state/tts.on') != []:
            line = process.stdout.readline().decode('utf-8')
            current_time = time.time()
            # Timeout calculation
            time_since_last_word = current_time - last_word_time
            remaining_time = max(0, timeout_threshold - time_since_last_word)
            
            if remaining_time > 0:
                print(f"TTS Timeout {remaining_time:.1f} ...", end="\r")

            if time_since_last_word > timeout_threshold:
                if sentence:  # If a sentence is being built, yield it
                    yield sentence.strip()
                    sentence = ''
                os.system("rm -rf state/tts.on")
                yield None
                # print("No word spoken for n seconds.")  # Handle timeout event

            if not line:
                break

            word = extract_single_word(line)
            if word:
                last_word_time = current_time  # Reset the timer when a word is spoken
                sentence += word

            if "talkback: SpeechControllerImpl: No next item, stopping speech queue" in line:
                if sentence:  # Yield the sentence if speech ends
                    yield sentence.strip()
                    sentence = ''
        else:
            time.sleep(1)

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
    os.system("touch state/tts.on")
    tts_speech = ""
    for sentence in get_tts_word(tts_pkg):
        if sentence:
            tts_speech += sentence
        else:
            print("TTS: ", tts_speech)
    tts_speech = ""
    os.system("touch state/tts.on")