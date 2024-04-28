import sys
from pathlib import Path
from typing import List, Dict, Tuple
from functools import cmp_to_key

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

# This runs in O(n) with respect to the number of tokens since it traverses each key token in the list only once.
def computeWordFrequencies(tokens: List[str]) -> Dict[str, int]:
    frequencies = {}
    for token in tokens:
        # Initialize frequency count for token to 0.
        if token not in frequencies:
            frequencies[token] = 0
        frequencies[token] += 1
    return frequencies


# This runs in O(n log n) with respect to the number of tokens since it uses Timsort to sort the dictionary items.
# Printing out the frequencies only takes O(n).
def printFrequencies(frequencies: Dict[str, int]) -> None:
    items = frequencies.items()
    items = sorted(items, key=cmp_to_key(compare))
    for items in items:
        print(f"{items[0]} => {items[1]}")
    if not items:
        print(0)

if __name__ == "__main__":
    if (len(sys.argv) < 2):
        print("You must specify an input file.")
    else:
        printFrequencies(computeWordFrequencies(tokenize(sys.argv[1])))