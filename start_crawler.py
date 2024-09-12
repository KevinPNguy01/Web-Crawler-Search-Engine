from configparser import ConfigParser
from argparse import ArgumentParser
from web_crawler.utils.config import Config
from web_crawler.crawler import Crawler

def main(config_file, restart):
    cparser = ConfigParser()
    cparser.read(config_file)
    config = Config(cparser)
    crawler = Crawler(config, restart)
    crawler.start()


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--restart", action="store_true", default=False)
    parser.add_argument("--config_file", type=str, default="web_crawler/config.ini")
    args = parser.parse_args()
    main(args.config_file, args.restart)
