from pathlib import Path
from src.posting import Posting
from typing import Dict, List, Set
import json
import os

class InvertedIndex:
    def __init__(self, source: Path, restart=True) -> None:
        # Directory to read from.
        self.source: Path = source
        
        # Map of tokens to lists of Postings.
        self.postings: Dict[str, List[Posting]] = {}
        
        # Set of crawled files.
        self.crawled: Set[str] = set()
        
        self.crawled_save_path = Path("crawled.txt")
        self.index_save_path = Path("index.txt")
        if not restart:
            # Load save files if they exist.
            if self.crawled_save_path.exists() and self.index_save_path.exists():
                with open(self.crawled_save_path, "r") as file:
                    # Add crawled files to set.
                    for file_path in file:
                        self.crawled.add(file_path.rsplit("\\")[-1].strip())
                with open(self.index_save_path) as file:
                    # Add lists of Postings to dict through list comprehension.
                    for line in file:
                        token, postings_string = line.split(":", 1)
                        self.postings[token] = [Posting.from_string(p) for p in postings_string.split(";")[:-1]]
                print(f"Loaded {len(self.postings)} tokens from {len(self.crawled)} pages.")
            else:
                with open(self.crawled_save_path, "w"), open("index_of_crawled.txt", "w"):
                    print("Save file missing, starting from empty set.")
        else:
            with open(self.crawled_save_path, "w"), open("index_of_crawled.txt", "w"):
                print("Starting from empty set.")
            

     
    def run(self):
        id = len(self.crawled)
        with open(self.crawled_save_path, "a") as crawled_file, open("index_of_crawled.txt", "a") as index_of_crawled_file:
            position = os.path.getsize(self.crawled_save_path)
            # Iterate through all json files in source directory.
            for file in self.source.rglob("*.json"):
                # Skip file if it has been crawled before.

                if file.name in self.crawled:
                    continue

                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Ensure the JSON file has the "content" field and contains HTML tags
                content = data.get('content', '')
                if '<html' not in content[:1024].lower():
                    #print("FOUND A INVALID ")
                    continue

                self.crawled.add(file.name)
                line = f"{file}\n"
                crawled_file.write(line)
                index_of_crawled_file.write(f"{id},{position}\n")

                # Add all postings from that file to this index's own dict.
                for token, posting in Posting.get_postings(file, id).items():
                    self.postings.setdefault(token, [])
                    self.postings.get(token).append(posting)
                    
                id += 1
                position += len(line)+1
                
    def save_to_file(self) -> None:
        # Inverted index will be in the format:
        # <token>:<doc_id1>,<tf_tdf1>;<doc_id2>,<tf_tdf2>;<doc_id3>,<tf_tdf3>;
        with open(self.index_save_path, "w") as index, open("index_of_index.txt", "w") as index_of_index:
            position = 0
            for token, postings in self.postings.items():
                index_of_index.write(f"{token},{position}\n")
                line = f"{token}:"
                for posting in postings:
                    line += f"{posting.id},{posting.tf_idf};"
                line += "\n"
                index.write(line)
                position += len(line)+1
                
