import re
from crawler.tokenizer import *
from urllib.parse import urlparse, urldefrag, urljoin, parse_qs
from bs4 import BeautifulSoup

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content

    # Print error and return empty list if status is not 200.
    if (resp.status != 200):
        return []

    # Search for links in 'a' tags.
    soup = BeautifulSoup(resp.raw_response.content, "html.parser")
    parsed = urlparse(url)
    return [urljoin(parsed.netloc, urldefrag(tag["href"])[0]) for tag in soup.find_all("a", href=True)]

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        if not re.match(
            r"^.*\.(stat.uci.edu|informatics.uci.edu|cs.uci.edu|ics.uci.edu)",
            parsed.netloc
        ) or parsed.scheme not in set(["http", "https"]):
            return False
        for query in parse_qs(parsed.query):
            if query in set(["ical", "share", "action", "ucinetid"]):
                return False
            if re.match(r"afg\d+_page_id", query):
                return False
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1|ppsx|txt"
            + r"|thmx|mso|arff|rtf|jar|csv|bib"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", url.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise
