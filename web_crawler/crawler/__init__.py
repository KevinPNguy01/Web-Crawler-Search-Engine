from crawler.frontier import Frontier
from crawler.worker import Worker
from utils.config import Config
from utils import get_logger
import time
import json

class Crawler(object):
    def __init__(self, config: Config, restart, frontier_factory=Frontier, worker_factory=Worker):
        self.config = config
        self.logger = get_logger("CRAWLER")
        self.frontier = frontier_factory(config, restart)
        self.workers = list()
        self.worker_factory = worker_factory

    def start_async(self):
        self.workers = [
            self.worker_factory(worker_id, self.config, self.frontier)
            for worker_id in range(self.config.threads_count)]
        for worker in self.workers:
            worker.start()

    def start(self):
        try:
            self.start_async()
            # Crawler will stop when the queue of urls has been empty for 5 seconds.
            time.sleep(5)
            while not self.frontier.to_be_downloaded.empty():
                time.sleep(5)
            self.join()
        except KeyboardInterrupt:
            self.logger.info("Keyboard Interrupt caught, stopping crawler...")
            self.frontier.is_running = False
            self.join()

    def join(self):
        for worker in self.workers:
            worker.join()
        with open(self.config.save_file, "w") as f:
            data = {
                "urls": dict(sorted(self.frontier.discovered_urls.items(), key=lambda item: item[1]["length"], reverse=True)),
                "tokens": dict(sorted(self.frontier.frequencies.items(), key=lambda item: item[1], reverse=True))
            }
            json.dump(data, f, indent=4)