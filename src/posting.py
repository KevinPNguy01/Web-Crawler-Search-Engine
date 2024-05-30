from typing import Dict, Self
from src.tokenizer import *
from bs4 import BeautifulSoup

class Posting: 
    @staticmethod
    def get_postings(soup: BeautifulSoup, id: int) -> Dict[str, Self]:
        # Returns a dict of tokens to postings for this file.
        # Extract text from webpage content.
        text = extract_text(soup)
        # Tokenize text.
        frequencies = tokenize(text)
        # Create postings for each token and return dict.
        return {token: Posting(id, frequency) for token, frequency in frequencies.items()}

    def __init__(self, id: int, tf_idf: float) -> Self: 
        self.id = id
        self.tf_idf = tf_idf

    def __str__(self) -> str:
        return f"{self.id},{self.tf_idf:.3f}"
        
    @classmethod
    def from_string(cls: Self, string: str) -> Self:
        data = string.split(",")
        id = int(data[0])
        tf_idf = float(data[1])
        return cls(id, tf_idf)