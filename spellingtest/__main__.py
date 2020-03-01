import argparse
import os.path
import pathlib
import random
import re
import sys
import textwrap
import winsound

import PyDictionary
import requests
import win32com.client
from six.moves import input
from six.moves import tkinter
from six.moves import tkinter_filedialog


def say_with_rate(speak, voice, rate, phrase):
    speak.Rate = rate
    speak.Voice = voice
    speak.Speak(phrase)


def get_word_data(word, dict_apikey):
    url = f"https://www.dictionaryapi.com/api/v3/references/collegiate/json/{word}?key={dict_apikey}"  # noqa
    r = requests.get(url)
    if r.status_code != 200:
        raise ValueError("Can't find word from dictionary")

    word_data = r.json()

    try:
        prs = word_data[0]["hwi"]["prs"]
        for i in prs:
            if "sound" in i:
                wav_file = i["sound"]["audio"]
    except Exception:
        print(f"Can't find wav_file on {word_data}")
        raise

    pronounce_url = f"https://media.merriam-webster.com/soundc11/{wav_file[0]}/{wav_file}.wav"
    r = requests.get(pronounce_url)
    if r.status_code != 200:
        raise ValueError("Can't find pronounciation on {word_data}")
    pronounce = r.content
    return (word_data, pronounce)


def get_example(examples, word):
    url = 'http://sentence.yourdictionary.com/'
    r = requests.get(url + word)
    if r.status_code != 200:
        return
    matches = re.findall(r'class=\'li_content\'>(.+?)</div>', r.text)
    for m in matches:
        yield re.sub(r'<.+?>', '', m)


def get_word_or_command(count, total):
    while True:
        typed = input('({}/{}) Type word or <Enter> for help> '.format(count, total))
        typed = typed.strip()
        if typed == '':
            print(textwrap.dedent("""\
                Please type the word or one of these commands:
                'w' to say the word again, in different voice,
                'd' to say the next definition from the dictionary,
                'e' to say the next example usage sentence,
                'g' to give up on this word,
                'q' to quit."""))  # noqa
        elif typed == 'q':
            confirm = input("Are you sure?")
            if confirm.strip().lower() in ["y", "yes"]:
                break
        else:
            break
    return typed.lower()


def get_dict_apikey():
    apikeyfile = "dict_api.key"
    dict_apikey_path = pathlib.Path.cwd() / apikeyfile
    if dict_apikey_path.exists():
        return dict_apikey_path.read_text().strip()

    dict_apikey_path = pathlib.Path(sys.executable).parent / apikeyfile
    if dict_apikey_path.exists():
        return dict_apikey_path.read_text().strip()

    dict_apikey_path = pathlib.Path(sys.argv[0]).parent / apikeyfile
    if dict_apikey_path.exists():
        return dict_apikey_path.read_text().strip()

    home = pathlib.Path(os.path.expanduser("~"))
    dict_apikey_path = home / apikeyfile
    if dict_apikey_path.exists():
        return dict_apikey_path.read_text().strip()

    raise ValueError(f"could not find {apikeyfile}")


def main(argv=None):
    dict_apikey = get_dict_apikey()

    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser()
    parser.add_argument("wordlist", default='', nargs='*',
                        help="wordlist file(s), each containing the list of words. One word per-line")
    parser.add_argument("--voiceindex", type=int, default=0, help="voice index")
    parser.add_argument("--wordrate", type=int, default=-2, help="voice index")
    parser.add_argument("--defrate", type=int, default=0, help="voice index")
    parser.add_argument("--maxtry", type=int, default=3, help="max try")
    parser.add_argument("--missed-file", type=pathlib.Path,
                        help="File name to be appended with missed words. The file must already exist."
                        "By default it's _missed.txt file in the same directory as the first wordlist file.")
    options = parser.parse_args(argv)

    if not options.wordlist:
        tkgui = tkinter.Tk()
        tkgui.withdraw()
        options.wordlist = [tkinter_filedialog.askopenfilename(title='Choose a wordlist file')]
        tkgui.update()
        tkgui.destroy()

    words = []
    for wl in options.wordlist:
        with open(wl) as f:
            words.extend([w.strip().lower() for w in f.readlines() if w.strip()])
    words = list(set(words))  # uniquify

    random.shuffle(words)

    speak = win32com.client.Dispatch("SAPI.SpVoice")
    voices = [v for v in speak.GetVoices()]

    dictionary = PyDictionary.PyDictionary()

    print('Total number of words: {}'.format(len(words)))
    got_wrong = {}
    voiceindex = options.voiceindex
    numwords = 0
    for word in words:
        (word_data, pronounce) = get_word_data(word, dict_apikey)
        definition = (d for d in word_data[0]["shortdef"])
        examples = None
        numwords += 1
        while True:
            winsound.PlaySound(pronounce, winsound.SND_MEMORY)
            typed = get_word_or_command(numwords, len(words))
            if typed == word:
                print('correct')
                voiceindex = options.voiceindex
                break
            elif typed == 'd':
                try:
                    say_with_rate(speak, voices[options.voiceindex], options.defrate, next(definition))
                except StopIteration:
                    definition = None
                    say_with_rate(speak, voices[options.voiceindex], options.defrate, "no other meaning")
            elif typed == 'e':
                if examples is None:
                    examples = get_example(dictionary, word)
                try:
                    say_with_rate(speak, voices[options.voiceindex], options.defrate, next(examples))
                except StopIteration:
                    examples = None
                    say_with_rate(speak, voices[options.voiceindex], options.defrate, "no other examples")
            elif typed == 'q':
                got_wrong.setdefault(word, [])
                got_wrong[word].append('q')
                break
            elif typed == 'w':
                voiceindex += 1
            elif typed == 'g':
                got_wrong.setdefault(word, [])
                got_wrong[word].append(typed)
                print('the word is {}'.format(word))
                break
            else:
                got_wrong.setdefault(word, [])
                got_wrong[word].append(typed)
                if len(got_wrong[word]) >= options.maxtry:
                    print('wrong, the word is {}'.format(word))
                    break
                print('wrong, try again')
        if typed == 'q':
            break

    if got_wrong:
        print("These are the words you got wrong:")
        for k in sorted(got_wrong.keys()):
            print('{} - typed {}'.format(k, str(got_wrong[k])))
        print("You got {:.1f}% of {} words".format(
            (1 - (len(got_wrong.keys()) * 1.0 / numwords)) * 100.0,
            numwords))

        if options.missed_file is None:
            missed_file = pathlib.Path(options.wordlist[0]).parent / '_missed.txt'
        if missed_file.exists():
            with missed_file.open('a') as f:
                for k in sorted(got_wrong.keys()):
                    f.write(k + '\n')
    else:
        print("Congratulations! You got 100% from {} words".format(numwords))

    input('press <Enter> to quit program...')


if __name__ == '__main__':
    sys.exit(main())
