import PyDictionary
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import sys

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def valid_to_merriam_webster(word):
    response = requests.get(
        "https://www.merriam-webster.com/dictionary/{}".format(word), verify=False
    )

    if "The word you've entered isn't in the dictionary" in response.text:
        return False

    return True


with open(sys.argv[1]) as f:
    words = [w.strip() for w in f.read().splitlines()]
dictionary = PyDictionary.PyDictionary()
for i, w in enumerate(words):
    if not dictionary.meaning(w):
        if not valid_to_merriam_webster(w):
            print("{} {}".format(i, w))
