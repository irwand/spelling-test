# spelling-test

This program is to test student spelling skill. When the program starts, it
will ask for a word list file, which is a file that simply contains a list of
words, one word per line. The program then randomizes the words and pronounces
each word, as the user types the word. The program then checks spelling
correctness.

This currently only works for Windows 10, simply because we're using Microsoft
speech engine.

The code is freely available at https://github.com/irwand/spelling-test

# Build

## Download this code, create venv, install dependencies

1. install Python 3.6
2. git clone https://github.com/irwand/spelling-test.git
3. cd spelling-test
4. python -m venv venv
5. venv\Scripts\activate.bat
6. pip install -e .

## Fixup dependencies

1. Bug in win32com : https://github.com/nateshmbhat/pyttsx3/issues/6 . Change
   the last line of venv\Lib\site-packages\win32com\client\dynamic.py in
   \_GetDescInvokeType() to "return varkind"
2. Fix up PyDictionary warning. Edit
   venv\Lib\site-packages\PyDictionary\utils.py. Add ', features="html.parser"'
   into BeautifulSoup constructor argument.
3. Fix PyDictionary debug print when it can't find any meaning. Edit
   venv\Lib\site-packages\PyDictionary\core.py. In meaning(term) function,
   change print("Error: The Following Error occured:...) to a pass to disable the print.

## Build exe

1. pip install pyinstaller
2. pyinstaller spellingtest.spec
3. result is in dist/spellingtest.exe
