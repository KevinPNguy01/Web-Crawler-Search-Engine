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
        self.found_links = set([])

        self.last_crawls: Dict[str, datetime] = {}
        self.crawl_lock = Lock()
        
        self.robot_cache: Dict[str, RobotFileParser] = {}
        self.robots_lock = Lock()
        
        self.frequencies = {}
        self.frequencies_lock = Lock()
                
        if not os.path.exists(self.config.save_file) and not restart:
            # Save file does not exist, but request to load save.
            self.logger.info(
                f"Did not find save file {self.config.save_file}, "
                f"starting from seed.")
        elif os.path.exists(self.config.save_file) and restart:
            # Save file does exists, but request to start from seed.
            self.logger.info(
                f"Found save file {self.config.save_file}, deleting it.")
            os.remove(self.config.save_file)
        
        if os.path.exists(self.config.frequencies_save_file) and restart:
            os.remove(self.config.frequencies_save_file)
        # Load existing save file, or create one if it does not exist.
        self.save = shelve.open(self.config.save_file)
        if restart:
            for url in self.config.seed_urls:
                self.add_url(url)
        else:
            # Set the frontier state with contents of save file.
            self._parse_save_file()
            if not self.save:
                for url in self.config.seed_urls:
                    self.add_url(url)

            self._parse_frequency_file()

    def _parse_save_file(self):
        ''' This function can be overridden for alternate saving techniques. '''
        total_count = len(self.save)
        tbd_count = 0
        for url, completed in self.save.values():
            if not completed and is_valid(url):
                self.to_be_downloaded.put(url)
                tbd_count += 1
        self.logger.info(
            f"Found {tbd_count} urls to be downloaded from {total_count} "
            f"total urls discovered.")
        
    def _parse_frequency_file(self):
        with open(self.config.frequencies_save_file, "a"):
            pass
        with open(self.config.frequencies_save_file, "r") as f:
            self.frequencies = json.load(f)
            
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
        urlhash = get_urlhash(url)
        
        self.found_links.add(url)
        if urlhash not in self.save:
            self.save[urlhash] = (url, False)
            self.save.sync()
            self.to_be_downloaded.put(url)
    
    def mark_url_complete(self, url):
        urlhash = get_urlhash(url)
        if urlhash not in self.save:
            # This should not happen.
            self.logger.error(
                f"Completed url {url}, but have not seen it before.")

        self.save[urlhash] = (url, True)
        self.save.sync()
