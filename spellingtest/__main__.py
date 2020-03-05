import argparse
import os.path
import pathlib
import random
import re
import sys
import textwrap
import traceback
import winsound

import requests
import win32com.client
from six.moves import input
from six.moves import tkinter
from six.moves import tkinter_filedialog


def get_word_data(word, dict_apikey):
    url = f"https://www.dictionaryapi.com/api/v3/references/collegiate/json/{word}?key={dict_apikey}"  # noqa
    r = requests.get(url)
    if r.status_code != 200:
        raise ValueError("Can't find word from dictionary")

    word_data = r.json()
    wav_files = []
    wav_data = []

    try:
        prs = word_data[0]["hwi"]["prs"]
        for i in prs:
            if "sound" in i:
                wav_files.append(i["sound"]["audio"])
    except Exception:
        print(f"Can't find wav_file on {word_data}")
        raise

    for wav_file in wav_files:
        pronounce_url = f"https://media.merriam-webster.com/soundc11/{wav_file[0]}/{wav_file}.wav"
        r = requests.get(pronounce_url)
        if r.status_code != 200:
            raise ValueError("Can't find pronounciation on {word_data}")
        wav_data.append(r.content)
    return (word_data, wav_data)


def get_example(word):
    url = 'http://sentence.yourdictionary.com/'
    r = requests.get(url + word)
    if r.status_code != 200:
        return
    matches = re.findall(r'\\"sentence\\":\\"(.+?)\\"', r.text)
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
            confirm = input("Are you sure? ")
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


def _play_wav(wav_data, msspeech):
    winsound.PlaySound(wav_data[0], winsound.SND_MEMORY)
    for w in wav_data[1:]:
        msspeech.say("or")
        winsound.PlaySound(w, winsound.SND_MEMORY)


def say_word(word, word_data, wav_data, msspeech):
    if word == word_data[0]["meta"]["id"].split(":")[0]:  # exact pronunciation
        _play_wav(wav_data, msspeech)
    else:
        msspeech.say(word)
        msspeech.say("stems from")
        _play_wav(wav_data, msspeech)


class MSSpeech(object):
    def __init__(self, rate):
        self._speak = win32com.client.Dispatch("SAPI.SpVoice")
        voices = [v for v in self._speak.GetVoices()]
        self._speak.Rate = rate
        self._speak.Voice = voices[0]

    def say(self, phrase):
        self._speak.Speak(phrase)


def main(argv=None):
    dict_apikey = get_dict_apikey()

    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser()
    parser.add_argument("wordlist", default='', nargs='*',
                        help="wordlist file(s), each containing the list of words. One word per-line")
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

    msspeech = MSSpeech(options.defrate)

    print('Total number of words: {}'.format(len(words)))
    got_wrong = {}
    numwords = 0
    for word in words:
        try:
            (word_data, wav_data) = get_word_data(word, dict_apikey)
            definition = (d for d in word_data[0]["shortdef"])
            examples = None
            numwords += 1
            while True:
                say_word(word, word_data, wav_data, msspeech)
                typed = get_word_or_command(numwords, len(words))
                if typed == word:
                    print('correct')
                    break
                elif typed == 'd':
                    try:
                        msspeech.say(next(definition))
                    except StopIteration:
                        definition = None
                        msspeech.say("no other meaning")
                elif typed == 'e':
                    if examples is None:
                        examples = get_example(word)
                    try:
                        msspeech.say(next(examples))
                    except StopIteration:
                        examples = None
                        msspeech.say("no other examples")
                elif typed == 'q':
                    got_wrong.setdefault(word, [])
                    got_wrong[word].append('q')
                    break
                elif typed == 'w':
                    pass  # loop back, say the word again
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
        except Exception:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print(f"ERROR: Exception in processing word: {word}")
            traceback.print_tb(exc_traceback)
            # continue to next word

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
