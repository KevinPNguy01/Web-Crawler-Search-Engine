from argparse import ArgumentParser
from src.inverted_index import InvertedIndex
from pathlib import Path
import cProfile

def main(restart):
    index = InvertedIndex(Path("DEV"), restart=restart)
    index.start()

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--restart", action="store_true", default=False)
    parser.add_argument("--profile", action="store_true", default=False)
    args = parser.parse_args()
    if args.profile:
        cProfile.run("main(args.restart)", sort="tottime")
    else:
        main(args.restart)