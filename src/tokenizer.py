from typing import List, Dict, Tuple
from bs4 import BeautifulSoup
from bs4.element import Comment
from functools import cmp_to_key
from collections import Counter
from nltk.util import ngrams
import json
import re

def extract_text(content: str) -> List[str]:
    # Given content representing a webpage, return the textual content.

    soup = BeautifulSoup(content, "lxml")
    [s.decompose() for s in soup(['style', 'script', '[document]', 'head', 'title'])]
    return [re.sub(r'\s+',' ', string) for string in soup.stripped_strings if string]

# Custom comparison function that sorts by frequency descending, and then alphabetically.
# This runs in O(n) since all operations are O(1) and does not depend on size of input.
def compare(item1: Tuple[str, int], item2: Tuple[str, int]) -> int:
    token1, count1 = item1
    token2, count2 = item2
    # If frequencies are the same, sort alphabetically.
    if count1 == count2:
        return -1 if token1 < token2 else 1
    # Sort higher frequencies first.
    return -1 if count1 > count2 else 1

# This runs in O(n) with respect to the size of the file since it iterates through each line of the file once, 
# and iterates through each character of each line only once.
def tokenize(text: List[str]) -> List[str]:
    n_grams = []
    for string in text:
        tokens: List[str] = [token.lower() for token in re.findall(r'\b[a-zA-Z0-9]+\b', string) if not token.isnumeric() or len(token) <= 4]
        for token in tokens:
            n_grams.append((token.lower(),))
        n_grams.extend(n_gram for n_gram in ngrams(tokens, 2) if any(not token.isnumeric() for token in n_gram))
        n_grams.extend(n_gram for n_gram in ngrams(tokens, 3) if any(not token.isnumeric() for token in n_gram))
    # Convert all tokens to lower case and count their frequencies.
    frequencies = Counter(" ".join(token) for token in n_grams)
    return frequencies

if __name__ == "__main__":
    with open("DEV\\aiclub_ics_uci_edu\\8ef6d99d9f9264fc84514cdd2e680d35843785310331e1db4bbd06dd2b8eda9b.json", "r") as f:
        data = json.load(f)
        print(tokenize(extract_text(data["content"])))