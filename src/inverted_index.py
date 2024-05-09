from pathlib import Path
from posting import Posting
from typing import Dict, List

class InvertedIndex:
    def __init__(self, source: Path) -> None:
        # Map of tokens to lists of Postings.
        self.postings: Dict[str, List[Posting]] = {}
        
        # Iterate through all json files in source directory.
        for id, file in enumerate(source.rglob("*.json")):
            # Add all postings from that file to this index's own dict.
            for token, posting in Posting.get_postings(file, id).items():
                self.postings.setdefault(token, [])
                self.postings.get(token).append(posting)