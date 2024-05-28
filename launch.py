from argparse import ArgumentParser
from src.inverted_index import InvertedIndex
from pathlib import Path
import cProfile
import pstats
import io

def main(restart):
    index = InvertedIndex(Path("DEV"), restart=restart)
    index.start()

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--restart", action="store_true", default=False)
    parser.add_argument("--profile", action="store_true", default=False)
    args = parser.parse_args()
    if args.profile:
        stream = io.StringIO()
        profiler = cProfile.Profile()
        profiler.enable()
        main(args.restart)
        profiler.disable()
        p = pstats.Stats(profiler, stream=stream).sort_stats("tottime")
        p.print_stats(20)
        print(stream.getvalue())
    else:
        main(args.restart)