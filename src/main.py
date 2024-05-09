from inverted_index import InvertedIndex
from pathlib import Path

if __name__ == "__main__":
    index = InvertedIndex(Path("asterix_ics_uci_edu"))
    index.save_to_file("index.json")