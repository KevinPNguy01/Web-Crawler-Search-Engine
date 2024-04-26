import os
import shelve
import json

from threading import Thread, RLock, Lock
from queue import Queue, Empty

from utils import get_logger, get_urlhash, normalize
from scraper import is_valid

from urllib.parse import urlparse, ParseResult
from typing import Dict
from datetime import datetime
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
from utils.download import download
from utils.config import Config

class Frontier(object):
    def __init__(self, config: Config, restart):
        self.logger = get_logger("FRONTIER")
        self.config = config
        self.is_running = True
        self.to_be_downloaded = Queue()
        self.found_links: Dict[str, bool] = {}

        self.last_crawls: Dict[str, datetime] = {}
        self.crawl_lock = Lock()
        
        self.robot_cache: Dict[str, RobotFileParser] = {}
        self.robots_lock = Lock()
        
        self.frequencies = {}
        self.frequencies_lock = Lock()
                        
        if restart:
            self.logger.info(f"Restarting from seed urls.")
            for url in self.config.seed_urls:
                self.add_url(url)
        else:
            self._parse_save_file()
            self._parse_frequency_file()

    def _parse_save_file(self):
        try:
            # Try to read save file.
            with open(self.config.save_file, "r") as f:
                self.found_links: Dict[str, bool] = json.load(f)
                
            # Add urls that have not been downloaded yet to the queue.
            [self.to_be_downloaded.put(url) for url, completed in self.found_links.items() if not completed]
            
            # Log statistics.
            total_count = len(self.found_links)
            tbd_count = self.to_be_downloaded.qsize()
            self.logger.info(f"Found {tbd_count} urls to be downloaded from {total_count} total urls discovered.")
            
        except:
            # Start from seed if save file couldn't be read.
            for url in self.config.seed_urls:
                self.add_url(url)
            self.logger.info(f"Couldn't read save {self.config.save_file}, starting from seed.")
        
    def _parse_frequency_file(self):
        try:
            # Try to read frequency save file.
            with open(self.config.frequencies_save_file, "r") as f:
                self.frequencies = json.load(f)
        except:
            # Start empty if read failed.
            self.frequencies = {}
            
    def create_robot(self, url: ParseResult) -> RobotFileParser:
        # Finds a robots.txt from the given url returns a RobotFileParser.
        
        # Construct robots.txt url and RobotFileParser object.
        robot_url = f"{url.scheme}://{url.netloc}/robots.txt"
        robot = RobotFileParser()
        robot.modified()
        
        # Try to download robots.txt and parse it.
        try:
            response = download(robot_url, self.config, self.logger)
            robot.parse(response.raw_response.content.decode().splitlines())
            self.logger.info(f"Downloaded {robot_url}.")
            return robot
        # Return default RobotFileParser if robots.txt doesn't exist.
        except:
            return robot

    def get_tbd_url(self):
        # Loop through list of urls looking for a domain that wasn't crawled recently.
        while True:
            # Parse the url and get the domain.
            try:
                url = self.to_be_downloaded.get(timeout=15)
            # Return None if the frontier is empty.
            except Empty:
                return None
            parsed = urlparse(url)
            domain = parsed.netloc
            
            # Set a flag and reserve an entry in the robot cache if the domain was not found in the cache.
            with self.robots_lock:
                if create_new_robot := (domain not in self.robot_cache):
                    self.robot_cache[domain] = None
            # Create a new robot without locking.
            if create_new_robot:
                self.robot_cache[domain] = self.create_robot(parsed)
                
            # If robot is None, it means the frontier is currently downloading it so fetch a different url.
            robot = self.robot_cache.get(domain)
            if robot is None:
                self.to_be_downloaded.put(url)
                continue

            # Do not download the url if it is disallowed by the robot.
            if not robot.can_fetch(self.config.user_agent, url):
                self.mark_url_complete(url)
                continue       

            # Get crawl delay from associated robot.
            crawl_delay = robot.crawl_delay(self.config.user_agent)
            if crawl_delay is None: 
                crawl_delay = 0
            # Lock last_crawls dict so that the times remain consistent.
            with self.crawl_lock:
                # Check how much time has passed since the domain was last crawled.
                time_elapsed = self.config.time_delay
                last_time = self.last_crawls.get(domain, datetime(1,1,1))
                time_elapsed = (datetime.now() - last_time).total_seconds()  

                # If sufficient time has elapsed, update the last crawled time and return url.
                if time_elapsed >= max(crawl_delay, self.config.time_delay):
                    # Update the last crawled time and return url.
                    self.last_crawls[domain] = datetime.now()
                    self.logger.info(f"Dispensed {url}.")
                    self.mark_url_complete(url)
                    return url
            # Else, add url back into the list of urls.
            self.to_be_downloaded.put(url)

    def add_url(self, url):
        # Skip url if it has been found already.
        url = normalize(url)
        if url in self.found_links: return
        
        self.found_links[url] = False
        self.to_be_downloaded.put(url)
    
    def mark_url_complete(self, url):
        self.found_links[url] = True
