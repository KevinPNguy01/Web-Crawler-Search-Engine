import os
import logging
from hashlib import sha256
from urllib.parse import urlparse, unquote
from pathlib import Path

def get_logger(name, filename=None):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    path = str(Path(__file__).parent.parent / "logs")
    if not os.path.exists(path):
        os.makedirs(path)
    fh = logging.FileHandler(f"{path}/{filename if filename else name}.log")
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter(
       "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


def get_urlhash(url):
    parsed = urlparse(url)
    # everything other than scheme.
    return sha256(
        f"{parsed.netloc}/{parsed.path}/{parsed.params}/"
        f"{parsed.query}/{parsed.fragment}".encode("utf-8")).hexdigest()

def normalize(url: str):
    url = unquote(url.lower()).replace("http://", "https://")
    if url.endswith("/"):
        return url.rstrip("/")
    return url
