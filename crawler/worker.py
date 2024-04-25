from threading import Thread, Lock
from inspect import getsource
from utils.download import download, download2
from utils import get_logger
from bs4 import BeautifulSoup
from crawler.tokenizer import *
from crawler.frontier import Frontier
from utils.config import Config
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse, ParseResult
from utils.download import download, download2
from datetime import datetime
from typing import Dict

import scraper
import time

class Worker(Thread):
    def __init__(self, worker_id: int, config: Config, frontier: Frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        self.id = worker_id
        
        self.frequencies: Dict[str, int] = {}
        self.page_lengths: Dict[str, int] = {}
        # basic check for requests in scraper
        assert {getsource(scraper).find(req) for req in {"from requests import", "import requests"}} == {-1}, "Do not use requests in scraper.py"
        assert {getsource(scraper).find(req) for req in {"from urllib.request import", "import urllib.request"}} == {-1}, "Do not use urllib.request in scraper.py"
        super().__init__(daemon=True)
        
    def run(self):            
        while self.frontier.is_running:            
            # If a url was not fetched, then the frontier is empty and the thread can be stopped.
            if not (tbd_url := self.frontier.get_tbd_url()):
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break
            
            # Parse the url and get the domain.
            url = urlparse(tbd_url)
                
            # Download the url and scrape it for links.
            try:
                resp = download(url.geturl(), self.config, self.logger)
                self.logger.info(f"Downloaded {tbd_url}, status <{resp.status}>, using cache {self.config.cache_server}.")
                scraped_urls = scraper.scraper(tbd_url, resp)
            except:
                continue
            
            # Add the scraped urls to the frontier.
            for scraped_url in scraped_urls:                
                self.frontier.add_url(scraped_url)
            self.frontier.mark_url_complete(tbd_url)
            
            if resp.status == 200 and "Content-Type" in resp.headers and "text" in resp.headers["Content-Type"] and resp.raw_response.content[:4] != b'%PDF':
                try:
                    soup = BeautifulSoup(resp.raw_response.content, "html.parser")
                    [s.extract() for s in soup(['style', 'script', '[document]', 'head', 'title', 'td', 'tr', 'code'])]
                    frequencies = computeWordFrequencies(tokenize(soup.getText()))
                except Exception as e:
                    frequencies = {}
                self.frequencies = {k: self.frequencies.get(k, 0) + frequencies.get(k, 0) for k in set(self.frequencies) | set(frequencies)}
                self.page_lengths[f"[STATS] {url.geturl()}"] = sum(frequencies.values())
            time.sleep(self.config.time_delay)
            
        with self.frontier.frequencies_lock:
            self.logger.info("Syncing statistics...")
            for key, value in self.frequencies.items():
                self.frontier.frequencies_save[key] = self.frontier.frequencies_save.setdefault(key, 0) + value
            for key, value in self.page_lengths.items():
                self.frontier.frequencies_save[key] = value
            self.frontier.frequencies_save.sync()
            self.logger.info(f"Synced {len(self.frequencies)} words and {len(self.page_lengths)} links.")