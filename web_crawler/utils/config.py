class Config(object):
    def __init__(self, config):
        self.user_agent = config["IDENTIFICATION"]["USERAGENT"].strip()
        self.save_file = config["LOCAL PROPERTIES"]["SAVE"]
        self.seed_urls = config["CRAWLER"]["SEEDURL"].split(",")
        self.root_domains = config["CRAWLER"]["ROOTDOMAINS"].split(",")
        self.time_delay = float(config["CRAWLER"]["POLITENESS"])