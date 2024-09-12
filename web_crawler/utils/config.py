class Config(object):
    def __init__(self, config):
        self.user_agent = config["IDENTIFICATION"]["USERAGENT"].strip()
        self.threads_count = int(config["LOCAL PROPERTIES"]["THREADCOUNT"])
        self.save_file = config["LOCAL PROPERTIES"]["SAVE"]
        self.download_path = config["LOCAL PROPERTIES"]["DOWNLOADPATH"]
        self.seed_urls = config["CRAWLER"]["SEEDURL"].split(",")
        self.root_domains = config["CRAWLER"]["ROOTDOMAINS"].split(",")
        self.time_delay = float(config["CRAWLER"]["POLITENESS"])