from threading import Thread, Lock
from datetime import datetime

from inspect import getsource
from utils.download import download
from utils import get_logger
from bs4 import BeautifulSoup
from crawler.tokenizer import *

import scraper
import time

mutex = Lock()

class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        self.id = worker_id
        # basic check for requests in scraper
        assert {getsource(scraper).find(req) for req in {"from requests import", "import requests"}} == {-1}, "Do not use requests in scraper.py"
        assert {getsource(scraper).find(req) for req in {"from urllib.request import", "import urllib.request"}} == {-1}, "Do not use urllib.request in scraper.py"
        super().__init__(daemon=True)
        
    def run(self):            
        global mutex
        while True:
            for i in range(3):
                with mutex:
                    tbd_url = self.frontier.get_tbd_url()
                if tbd_url:
                    break
                time.sleep(5)
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break
            resp = download(tbd_url, self.config, self.logger)
            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")
            scraped_urls = scraper.scraper(tbd_url, resp)
            with mutex:
                for scraped_url in scraped_urls:
                    self.frontier.add_url(scraped_url)
                self.frontier.mark_url_complete(tbd_url)
            if resp.status == 200 and "text" in resp.headers["Content-Type"] and resp.raw_response.content[:4] != b'%PDF':
                try:
                    soup = BeautifulSoup(resp.raw_response.content, "html.parser")
                    [s.extract() for s in soup(['style', 'script', '[document]', 'head', 'title', 'td', 'tr', 'code'])]
                    frequencies = computeWordFrequencies(tokenize(soup.getText()))
                except Exception as e:
                    frequencies = {}
                with self.frontier.frequencies_lock:
                    total_words = 0
                    for key in frequencies:
                        if key not in self.frontier.frequencies_save.keys():
                            self.frontier.frequencies_save[key] = 0
                        self.frontier.frequencies_save[key] += frequencies[key]
                        total_words += frequencies[key]
                    prev_longest_page = self.frontier.frequencies_save.get(f"[STATS] {tbd_url}", 0)
                    self.frontier.frequencies_save[f"[STATS] {tbd_url}"] = max(total_words, prev_longest_page)
                    self.frontier.frequencies_save.sync()
            time.sleep(self.config.time_delay)
