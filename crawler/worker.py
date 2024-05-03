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
        
    def save_page(self, response: Response):
        # Parse the URL to extract domain and path.
        parsed_url = urlparse(response.url)
        domain = parsed_url.netloc
        path = parsed_url.path
        
        if parsed_url.query:
            path += '?' + parsed_url.query

        # Create directory structure based on domain and path.
        directory = os.path.join('pages', domain, os.path.dirname(path).lstrip("/"))
        os.makedirs(directory, exist_ok=True)

        # Generate filename from the last part of the path.
        filename = os.path.join(directory, os.path.basename(path).lstrip("/"))
        if not filename.endswith(".html"):
            filename += ".html"

        # Write page content to file.
        with open(filename, 'wb') as f:
            f.write(response.raw_response.content)

        self.logger.info(f"Page saved to: {filename}")
        
    def should_scrape(self, resp: Response):
        # Returns whether the worker should scrape this page.
        
        # The response must have all the appropriate data.
        valid_response = resp and resp.status and resp.url and resp.raw_response and resp.raw_response.content and resp.raw_response.url
        if not valid_response:
            return False
        # The response must have status 200.
        valid_status = resp.status == 200
        if not valid_status: 
            return False
        # Must be at least 256 bytes.
        valid_size = len(resp.raw_response.content) >= 256
        if not valid_size:
            return False
        # Must have html tag in first 256 bytes.
        valid_content = b'<HTML' in resp.raw_response.content[:256] or b'<html' in resp.raw_response.content[:256]
        
        return valid_content
    
    def process_url(self, tbd_url: str) -> bool:
        # Processes one url from the frontier.
        
        # Try to download the url, setting the response to None if an exception was caught.
        try:
            resp = download(tbd_url, self.config, self.logger)
            self.logger.info(f"Downloaded {tbd_url}, status <{resp.status}>, using cache {self.config.cache_server}.")
            #self.save_page(resp, tbd_url)
        except Exception as e:
            resp = None
            self.logger.error(f"Error Downloading {tbd_url}: {e}")
            return
        
        if self.should_scrape(resp):
            # Add the scraped urls to the frontier.
            for scraped_url in scraper.scraper(tbd_url, resp):                
                self.frontier.add_url(scraped_url)
        
            # Tokenize the page content and get their frequencies.
            soup = BeautifulSoup(resp.raw_response.content, "html.parser")
            [s.extract() for s in soup(['style', 'script', '[document]', 'head', 'title', 'td', 'tr', 'code'])]
            frequencies = computeWordFrequencies(tokenize(soup.getText()))
            
            # Add them to this worker's frequencies dictionary, as well as store the length of this page.
            for key, value in frequencies.items():
                self.frequencies[key] = self.frequencies.setdefault(key, 0) + value
            self.page_lengths[tbd_url] = sum(frequencies.values())
            
    def main(self):
        while self.frontier.is_running:
            # If a url was not fetched, then the frontier is empty and the thread can be stopped.
            if not (tbd_url := self.frontier.get_tbd_url()):
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break
            # Try to process the url. If something went wrong, the worker can recover and process the next one.    
            try:
                self.process_url(tbd_url)
            except Exception as e:
                self.logger.error(f"{type(e).__name__} caught while processing {tbd_url}: {e}.")
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