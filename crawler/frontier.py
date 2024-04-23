import os
import shelve
import socket

from threading import Thread, RLock, Lock
from queue import Queue, Empty

from utils import get_logger, get_urlhash, normalize
from scraper import is_valid

from urllib.parse import urlparse
from typing import Dict
from datetime import datetime
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup

class Frontier(object):
    def __init__(self, config, restart):
        self.logger = get_logger("FRONTIER")
        self.config = config
        self.to_be_downloaded = list()

        self.last_crawls : Dict[str, datetime] = {}
        self.mutex = RLock()
        self.found_links = set([])
        self.robot_cache = {}
        self.frequencies = {}
        self.frequencies_lock = Lock()

        socket.setdefaulttimeout(5)
        
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
        self.frequencies_save = shelve.open(self.config.frequencies_save_file)
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
                self.to_be_downloaded.append(url)
                tbd_count += 1
        self.logger.info(
            f"Found {tbd_count} urls to be downloaded from {total_count} "
            f"total urls discovered.")
        
    def _parse_frequency_file(self):
        for word, frequency in self.frequencies_save.items():
            self.frequencies[word] = frequency

    def get_tbd_url(self):
        try:
            # Loop through list of urls looking for a domain that wasn't crawled recently.
            while True:
                # Parse the url and get the domain.
                url = self.to_be_downloaded.pop()
                parsed = urlparse(url)
                domain = parsed.netloc

                # If the domain was crawled before, check how much time has passed.
                time_elapsed = self.config.time_delay
                if domain in self.last_crawls:
                    last_time = self.last_crawls[domain]
                    time_elapsed = (datetime.now() - last_time).total_seconds()

                    # If the time passed was less than the time delay, then put it back into the list of urls.
                    if time_elapsed < self.config.time_delay:
                        self.to_be_downloaded.insert(0, url)

                # If sufficient time has elapsed, then break out of loop.
                if time_elapsed >= self.config.time_delay:
                    break

            # Update the last crawled time and return url.
            self.last_crawls[domain] = datetime.now()
            return url
        except IndexError:
            print("Index Error\n")
            return None

    def add_url(self, url):
        # Skip url if it has been found already.
        if url in self.found_links:
            return

        url = normalize(url)
        urlhash = get_urlhash(url)

        # Parse url and get domain.
        parsed = urlparse(url)
        domain = parsed.netloc

        # Check robots.txt file. If it exists and url is disallowed, then skip.
        if domain not in self.robot_cache:
            robot = RobotFileParser(f"https://{domain}/robots.txt")
            self.robot_cache[domain] = robot
            try:
                robot.read()
            except:
                self.robot_cache[domain] = None
        if self.robot_cache[domain] and not self.robot_cache[domain].can_fetch("*", url):
            return
        self.found_links.add(url)
        
        if urlhash not in self.save:
            self.save[urlhash] = (url, False)
            self.save.sync()
            self.to_be_downloaded.append(url)
    
    def mark_url_complete(self, url):
        urlhash = get_urlhash(url)
        if urlhash not in self.save:
            # This should not happen.
            self.logger.error(
                f"Completed url {url}, but have not seen it before.")

        self.save[urlhash] = (url, True)
        self.save.sync()
