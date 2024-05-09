from pathlib import Path
from posting import Posting
from typing import Dict, List
import json

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
                
    def save_to_file(self, dest: Path) -> None:
        index: Dict[str, List[dict]] = {}
        with open(dest, "w") as file:
            json.dump({token: [{"id": p.id, "url": p.url, "tf_idf": p.tf_idf} for p in postings] for token, postings in self.postings.items()}, file, indent=4)