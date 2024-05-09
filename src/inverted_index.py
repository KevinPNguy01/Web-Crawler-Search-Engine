from pathlib import Path
from posting import Posting
from typing import Dict

class InvertedIndex:
    def __init__(self, source: Path) -> None:
        # Map of tokens to lists of Postings.
        self.token_map: Dict[str, Posting] = {}
        
        # Iterate through all json files in source directory.
        for file in source.rglob("*.json"):
            Posting.get_postings(file)