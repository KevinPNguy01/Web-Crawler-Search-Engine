from pathlib import Path
from typing import Dict, Self
from src.tokenizer import *
import json

class Posting: 
    @staticmethod
    def get_postings(file_path: Path, id: int) -> Dict[str, Self]:
        # Returns a dict of tokens to postings for this file.
        with open(file_path) as file:
            data = json.load(file)
            print(f"{id} - {data['url']}")
            # Extract text from webpage content.
            text = extract_text(data["content"])
            # Tokenize text.
            frequencies = computeWordFrequencies(tokenize(text))
            # Create postings for each token and return dict.
            return {token: Posting(id, data["url"], frequency) for token, frequency in frequencies.items()}
        
        

    def __init__(self, id: int, url: str, tf_idf: float) -> Self: 
        self.id = id
        self.url = url
        self.tf_idf = tf_idf