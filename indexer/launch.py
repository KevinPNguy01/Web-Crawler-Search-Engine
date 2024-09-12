from argparse import ArgumentParser
from inverted_index import InvertedIndex
from pathlib import Path

def main(restart, num_workers):
    index = InvertedIndex(Path("pages"), restart=restart, num_workers=num_workers)
    index.start()

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--restart", action="store_true", default=False)
    parser.add_argument("-n", type=int, default=1, help="The number of worker processes to spawn (default: 1)")
    args = parser.parse_args()
    main(args.restart, args.n)