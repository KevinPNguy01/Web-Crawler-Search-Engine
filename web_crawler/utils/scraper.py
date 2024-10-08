from urllib.parse import urlparse, urldefrag, urljoin, parse_qs, unquote
from web_crawler.utils.response import Response
from bs4 import BeautifulSoup
from typing import List
from web_crawler.utils.config import Config

import re

def scraper(resp: Response, config: Config) -> List[str]:
    # Returns a list of links found inside the given url that are valid to crawl.
    links = extract_next_links(resp)
    return [link for link in links if is_valid(link, config)]

def extract_next_links(resp: Response) -> List[str]:
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content

    # Search for links in 'a' tags.
    soup = BeautifulSoup(resp.raw_response.content, "html.parser")
    return [urldefrag(urljoin(resp.raw_response.url, tag["href"]))[0] for tag in soup.find_all("a", href=True)]

def is_valid_scheme(scheme: str) -> bool:
    # Returns whether the given scheme is valid to crawl.
    
    return scheme in {"http", "https"}

def is_valid_domain(domain: str, root_domains: List[str]) -> bool:
    # Returns whether the given domain is valid to crawl.
    
    # It must end with one of four valid domains.
    return any([domain.endswith(valid_domain) for valid_domain in root_domains])

def is_valid_path(path: str) -> bool:
    # Returns whether the given path is valid to crawl.
    
    # An empty path is valid.
    if not path:
        return True
    
    # If there are duplicate segments in the path, it is invalid.
    segment_list = path.strip("/").split("/")
    segment_set = set(segment_list)
    if len(segment_list) != len(segment_set):
        return False
    
    # Highly repetitive auto-generated pages are invalid.
    if "doku.php" in segment_set:
        return False
    
    return not re.match(
        r".*\.(css|js|bmp|gif|jpe?g|ico|java|rb|json|xml|yaml"
        + r"|png|tiff?|mid|mp2|mp3|mp4|sql|c|cpp|py|js|sh|ts"
        + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf|bat|yml"
        + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names|ps1|scss|sass"
        + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso|nb|swift"
        + r"|epub|dll|cnf|tgz|sha1|ppsx|txt|war|r|z|data|jsx|tsx"
        + r"|thmx|mso|arff|rtf|jar|csv|bib|odc|php|data-original"
        + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", path.lower())
    
def is_valid_query(query: str) -> bool:
    # Returns whether the given query is valid to crawl.
    
    for param in parse_qs(query):
        if param in {"ical", "share", "action", "ucinetid", "image"}:
            return False
        if re.match(r"afg\d+_page_id", param):
            return False
        if any([keyword in param for keyword in {"filter"}]):
            return False
    return True

def is_valid(url: str, config: Config) -> bool:
    # Returns whether the given url is valid to crawl.
    
    parsed_url = urlparse(url)
    return all((
        is_valid_scheme(parsed_url.scheme),
        is_valid_domain(parsed_url.netloc, config.root_domains),
        is_valid_path(parsed_url.path),
        is_valid_query(parsed_url.query)
    ))