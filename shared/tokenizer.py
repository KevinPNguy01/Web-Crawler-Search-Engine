from typing import List, Dict, Tuple
from bs4 import BeautifulSoup
from collections import Counter
from nltk.util import ngrams
from nltk.stem import PorterStemmer
import re

def extract_text(soup: BeautifulSoup) -> List[str]:
    # Given content representing a webpage, return the textual content.

    [s.decompose() for s in soup(['style', 'code', 'script', '[document]'])]
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
def tokenize(text: str) -> List[str]:
    tokens = []
    token = ""
    for char in text:
        # A valid char can be encoded into ascii and is alphanumeric.
        try:
            # isalnum() is an O(1) operation since char is always of length 1.
            isValidChar = char.encode("ascii").isalnum()
        except:
            isValidChar = False
        if isValidChar:
            token += char
        # If invalid character is encountered and token is not empty, add it to list.
        elif token:
            tokens.append(token.lower())
            token = ""
    # Also add token if end of string is reached.
    if token:
        tokens.append(token.lower())
    return tokens

# This runs in O(n) with respect to the size of the file since it iterates through each line of the file once, 
# and iterates through each character of each line only once.
def tokenize_with_ngrams(text: List[str], stem=False) -> Dict[str, int]:
    stemmer = PorterStemmer()
    n_grams = []
    for string in text:
        tokens: List[str] = [token.lower() for token in re.findall(r'\b[a-zA-Z0-9]+\b', string) if not token.isnumeric() or len(token) <= 4]
        if stem:
            tokens = [stemmer.stem(token) for token in tokens]
        for token in tokens:
            n_grams.append((token.lower(),))
        n_grams.extend(n_gram for n_gram in ngrams(tokens, 2) if any(not token.isnumeric() for token in n_gram))
        n_grams.extend(n_gram for n_gram in ngrams(tokens, 3) if any(not token.isnumeric() for token in n_gram))
    # Convert all tokens to lower case and count their frequencies.
    frequencies = Counter(" ".join(token) for token in n_grams)
    return frequencies

# This runs in O(n) with respect to the number of tokens since it traverses each key token in the list only once.
def computeWordFrequencies(tokens: List[str]) -> Dict[str, int]:
    frequencies = {}
    for token in tokens:
        # Initialize frequency count for token to 0.
        if token not in frequencies:
            frequencies[token] = 0
        frequencies[token] += 1
    return frequencies