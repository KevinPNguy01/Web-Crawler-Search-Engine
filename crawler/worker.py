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
from utils.response import Response

import socket
import scraper
import time
import os

class Worker(Thread):
    def __init__(self, worker_id: int, config: Config, frontier: Frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        self.id = worker_id
        
        # Store dict for word frequencies, and dict for number of words in each page.
        self.frequencies: Dict[str, int] = {}
        self.page_lengths: Dict[str, int] = {}
                
        # basic check for requests in scraper
        assert {getsource(scraper).find(req) for req in {"from requests import", "import requests"}} == {-1}, "Do not use requests in scraper.py"
        assert {getsource(scraper).find(req) for req in {"from urllib.request import", "import urllib.request"}} == {-1}, "Do not use urllib.request in scraper.py"
        super().__init__(daemon=True)
        
    def save_page(self, response: Response, url: str):
        # Parse the URL to extract domain and path.
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        path = parsed_url.path
        
        if parsed_url.query:
            path += '?' + parsed_url.query

        # Create directory structure based on domain and path.
        directory = os.path.join('pages', domain, os.path.dirname(path).lstrip("/"))
        os.makedirs(directory, exist_ok=True)

        # Generate filename from the last part of the path.
        filename = os.path.join(directory, os.path.basename(path).lstrip("/") or 'index.html')
        if not filename.endswith(".html"):
            filename += ".html"

        # Write page content to file.
        with open(filename, 'wb') as f:
            f.write(response.raw_response.content)

        self.logger.info(f"Page saved to: {filename}")
        
    def main(self):
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
                #self.save_page(resp, url.geturl())
                scraped_urls = scraper.scraper(tbd_url, resp)
            except Exception as e:
                self.logger.error(f"Error Downloading {tbd_url}: {e}")
                continue
            
            # Add the scraped urls to the frontier.
            for scraped_url in scraped_urls:                
                self.frontier.add_url(scraped_url)
            
            if resp.status == 200 and "Content-Type" in resp.headers and "text" in resp.headers["Content-Type"] and resp.raw_response.content[:4] != b'%PDF':
                try:
                    soup = BeautifulSoup(resp.raw_response.content, "html.parser")
                    [s.extract() for s in soup(['style', 'script', '[document]', 'head', 'title', 'td', 'tr', 'code'])]
                    frequencies = computeWordFrequencies(tokenize(soup.getText()))
                except:
                    frequencies = {}
                for key, value in frequencies.items():
                    self.frequencies[key] = self.frequencies.setdefault(key, 0) + value
                self.page_lengths[url.geturl()] = sum(frequencies.values())
            time.sleep(self.config.time_delay)
        
    def sync(self):
        # Synchronizes the statistics collected by this worker thread with its frontier.
        
        # Acquire mutex for frontier's frequencies data structure.
        with self.frontier.frequencies_lock:
            # Add this worker's word frequencies to frontier.
            for key, value in self.frequencies.items():
                self.frontier.frequencies[key] = self.frontier.frequencies.setdefault(key, 0) + value
            # Add this worker's links and associated token counts to frontier.
            for key, value in self.page_lengths.items():
                self.frontier.discovered_urls[key] = {
                    "downloaded": True,
                    "length": self.page_lengths[key]
                }
            self.logger.info(f"Contributed {len(self.frequencies)} tokens and {len(self.page_lengths)} links.")
        
    def run(self):            
        self.main()    
        self.sync()