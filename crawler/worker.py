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
            with mutex:
                tbd_url = self.frontier.get_tbd_url()
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
            if resp.status == 200:
                try:
                    soup = BeautifulSoup(resp.raw_response.content, "html.parser")
                    frequencies = computeWordFrequencies(tokenize(soup.body.stripped_strings))
                except Exception as e:
                    frequencies = {}
                with self.frontier.frequencies_lock:
                    for key in frequencies:
                        if key not in self.frontier.frequencies_save.keys():
                            self.frontier.frequencies_save[key] = 0
                        self.frontier.frequencies_save[key] += frequencies[key]
                    self.frontier.frequencies_save.sync()
            time.sleep(self.config.time_delay)
