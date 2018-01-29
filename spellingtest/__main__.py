import argparse
import random
import sys
import textwrap
import tkinter
from tkinter.filedialog import askopenfilename

import PyDictionary
from six.moves import input
import win32com.client


def say_with_rate(speak, voice, rate, phrase):
    speak.Rate = rate
    speak.Voice = voice
    speak.Speak(phrase)


def get_def(dictionary, word):
    o = dictionary.meaning(word)
    if not o:
        return
    for k, v in o.items():
        for i in v:
            yield "{}, {}".format(k, i)


def get_word_or_command():
    while True:
        typed = input('Type word or <Enter> for help> ')
        typed = typed.strip()
        if typed == '':
            print(textwrap.dedent("""\
                Please type the word or one of these commands:
                'w' to say the word again, in different voice,
                'd' to say the next definition from the dictionary,
                'q' to quit."""))
        else:
            break
    return typed


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser()
    parser.add_argument("wordlist", default='', nargs='?',
                        help="wordlist file, containing the list of words. One word per-line")
    parser.add_argument("--voiceindex", type=int, default=0, help="voice index")
    parser.add_argument("--wordrate", type=int, default=-2, help="voice index")
    parser.add_argument("--defrate", type=int, default=0, help="voice index")
    parser.add_argument("--maxtry", type=int, default=3, help="max try")
    options = parser.parse_args(argv)

    if not options.wordlist:
        tkgui = tkinter.Tk()
        tkgui.withdraw()
        options.wordlist = askopenfilename(title='Choose a wordlist file')
        tkgui.update()
        tkgui.destroy()

    with open(options.wordlist) as f:
        words = [w.strip() for w in f.readlines()]

    random.shuffle(words)

    speak = win32com.client.Dispatch("SAPI.SpVoice")
    voices = [v for v in speak.GetVoices()]

    dictionary = PyDictionary.PyDictionary()

    got_wrong = {}
    voiceindex = options.voiceindex
    numwords = 0
    for word in words:
        definition = None
        while True:
            say_with_rate(speak, voices[voiceindex % len(voices)], options.wordrate, word)
            typed = get_word_or_command()
            if typed == word:
                print('correct')
                voiceindex = options.voiceindex
                break
            elif typed == 'd':
                if definition is None:
                    definition = get_def(dictionary, word)
                try:
                    say_with_rate(speak, voices[options.voiceindex], options.defrate, next(definition))
                except StopIteration:
                    definition = None
                    say_with_rate(speak, voices[options.voiceindex], options.defrate, "no other meaning")
            elif typed == 'q':
                got_wrong.setdefault(word, [])
                got_wrong[word].append('q')
                break
            elif typed == 'w':
                voiceindex += 1
            else:
                got_wrong.setdefault(word, [])
                got_wrong[word].append(typed)
                if len(got_wrong[word]) >= options.maxtry:
                    print('wrong, the word is {}'.format(word))
                    break
                print('wrong, try again')
        numwords += 1
        if typed == 'q':
            break

    if got_wrong:
        print("These are the words you got wrong:")
        for k in sorted(got_wrong.keys()):
            print('{} - typed {}'.format(k, str(got_wrong[k])))
        print("You got {:.1f}% of {} words".format(
            (1 - (len(got_wrong.keys()) * 1.0 / numwords)) * 100.0,
            numwords))
    else:
        print("Congratulations! You got 100% from {} words".format(numwords))

    input('press <Enter> to quit program...')


if __name__ == '__main__':
    sys.exit(main())
