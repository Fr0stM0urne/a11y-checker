import subprocess, os

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
    while True:
        line = process.stdout.readline().decode('utf-8')
        if not line:
            break
        if "talkback: SpeechControllerImpl: No next item, stopping speech queue" in line:
            print(sentence)
            sentence = ''
        sentence += extract_single_word(line)

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
    pkg = 'com.android.talkback4d'
    # get_tts_sentence(pkg)
    get_tts_word(pkg)