from pathlib import Path
from src.posting import Posting
from typing import Dict, List, Set
import json

class InvertedIndex:
    def __init__(self, source: Path, restart=True) -> None:
        # Directory to read from.
        self.source: Path = source
        
        # Map of tokens to lists of Postings.
        self.postings: Dict[str, List[Posting]] = {}
        
        # Set of crawled files.
        self.crawled: Set[str] = set()
        
        self.crawled_save_path = Path("crawled.txt")
        self.index_save_path = Path("index.json")
        if not restart:
            # Load save files if they exist.
            if self.crawled_save_path.exists() and self.index_save_path.exists():
                with open(self.crawled_save_path, "r") as file:
                    # Add crawled files to set.
                    for file_name in file:
                        self.crawled.add(file_name.strip())
                with open(self.index_save_path) as file:
                    data: Dict[str, List[dict]] = json.load(file)
                    # Add lists of Postings to dict through list comprehension.
                    for token, postings in data.items():
                        self.postings[token] = [Posting(p["id"], p["url"], p["tf_idf"]) for p in postings]
                print(f"Loaded {len(self.postings)} tokens from {len(self.crawled)} pages.")
            else:
                print("Save file missing, starting from empty set.")
        else:
            print("Starting from empty set.")
            
        
    def run(self):
        # Iterate through all json files in source directory.
        for id, file in enumerate(self.source.rglob("*.json")):
            # Skip file if it has been crawled before.
            if file.name in self.crawled:
                continue
            self.crawled.add(file.name)
            
            # Add all postings from that file to this index's own dict.
            for token, posting in Posting.get_postings(file, id).items():
                self.postings.setdefault(token, [])
                self.postings.get(token).append(posting)
                
    def save_to_file(self) -> None:
        # Save crawled urls to file.
        with open(self.crawled_save_path, "w") as file:
            for file_name in self.crawled:
                file.write(f"{file_name}\n")
        
        # Save index data to file.
        with open(self.index_save_path, "w") as file:
            json.dump({token: [{"id": p.id, "url": p.url, "tf_idf": p.tf_idf} for p in postings] for token, postings in self.postings.items()}, file, indent=4)