from argparse import ArgumentParser
from src.inverted_index import InvertedIndex
from pathlib import Path

def main(restart):
    index = InvertedIndex(Path("DEV"), restart=restart)
    try:
        index.run()
    except KeyboardInterrupt:
        pass
    index.save_to_file()

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--restart", action="store_true", default=False)
    args = parser.parse_args()
    main(args.restart)