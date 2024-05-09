from pathlib import Path
from typing import Dict, Self
import json

class Posting: 
    @staticmethod
    def get_postings(file_path: Path) -> Dict[str, Self]:
        # Returns a map of tokens to postings for this file.
        with open(file_path) as file:
            data = json.load(file)
            print(data["url"])

    def __init__(self): 
        pass
                 

    pass

