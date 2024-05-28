from typing import List, Dict, Tuple
from bs4 import BeautifulSoup
from functools import cmp_to_key
from collections import Counter
import re

def extract_text(content: str) -> str:
    # Given content representing a webpage, return the textual content.

    soup = BeautifulSoup(content, "xml")
    
    # Remove specific html tags.
    [s.extract() for s in soup(['style', 'script', '[document]', 'head', 'code'])]
    
    return soup.get_text()

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
    tokens = re.findall(r'\b[a-zA-Z0-9]+\b', text)
    # Convert all tokens to lower case and count their frequencies.
    frequencies = Counter(token.lower() for token in tokens)
    return frequencies