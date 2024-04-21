import re
import socket
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup, SoupStrainer

foundLinks = set([])
robot_cache = {}

socket.setdefaulttimeout(5)

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
    results = []

    # Print error and return empty list if status is not 200.
    if (resp.status != 200):
        print("Error:", resp.error)
        return results

    # Search for links in 'a' tags.
    soup = BeautifulSoup(resp.raw_response.content, "html.parser")
    for tag in soup.find_all("a"):
        # Skip tag if it doesn't have a link, has an invalid link, or has an already discovered link.
        try:
            link = tag["href"]
        except:
            continue
        if not is_valid(link) or link in foundLinks:
            continue
        
        parsed = urlparse(tag["href"])
        domain = parsed.netloc
        # Check robots.txt file. If it exists and url is disallowed, then skip.
        if domain not in robot_cache:
            robot = RobotFileParser(f"https://{domain}/robots.txt")
            robot_cache[domain] = robot
            try:
                robot.read()
            except:
                robot_cache[domain] = None
        if robot_cache[domain] and not robot_cache[domain].can_fetch("*", link):
            continue

        results.append(link)
        foundLinks.add(link)
    return results

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        if not re.match(
            r"^.*\.(stat.uci.edu|informatics.uci.edu|cs.uci.edu|ics.uci.edu)/",
            url.lower()
        ) or parsed.scheme not in set(["http", "https"]):
            return False
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise
