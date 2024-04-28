from utils.config import Config
from configparser import ConfigParser
from urllib.parse import urlparse
from typing import Dict, Tuple
import json

def get_num_unique_pages(urls: Dict[str, Dict]) -> int:
    return len(urls)

def get_longest_page(urls: Dict[str, Dict]) -> Tuple[str, int]:
    result = ("", 0)
    for url, data in urls.items():
        length = data["length"]
        if length > result[1]:
            result = (url, length)
    return result

def get_most_common_words(tokens: Dict[str, int]) -> Dict[str, int]:
    stop_words = """
        a
        about
        above
        after
        again
        against
        all
        am
        an
        and
        any
        are
        aren't
        as
        at
        be
        because
        been
        before
        being
        below
        between
        both
        but
        by
        can't
        cannot
        could
        couldn't
        did
        didn't
        do
        does
        doesn't
        doing
        don't
        down
        during
        each
        few
        for
        from
        further
        had
        hadn't
        has
        hasn't
        have
        haven't
        having
        he
        he'd
        he'll
        he's
        her
        here
        here's
        hers
        herself
        him
        himself
        his
        how
        how's
        i
        i'd
        i'll
        i'm
        i've
        if
        in
        into
        is
        isn't
        it
        it's
        its
        itself
        let's
        me
        more
        most
        mustn't
        my
        myself
        no
        nor
        not
        of
        off
        on
        once
        only
        or
        other
        ought
        our
        ours
        ourselves
        out
        over
        own
        same
        shan't
        she
        she'd
        she'll
        she's
        should
        shouldn't
        so
        some
        such
        than
        that
        that's
        the
        their
        theirs
        them
        themselves
        then
        there
        there's
        these
        they
        they'd
        they'll
        they're
        they've
        this
        those
        through
        to
        too
        under
        until
        up
        very
        was
        wasn't
        we
        we'd
        we'll
        we're
        we've
        were
        weren't
        what
        what's
        when
        when's
        where
        where's
        which
        while
        who
        who's
        whom
        why
        why's
        with
        won't
        would
        wouldn't
        you
        you'd
        you'll
        you're
        you've
        your
        yours
        yourself
        yourselves
    """
    stop_words = set(stop_words.strip().split())
    result: Dict[str, int] = {}
    for token, count in tokens.items():
        if not token in stop_words and len(token) >= 2:
            result[token] = count
    return dict(sorted(result.items(), key=lambda item: item[1], reverse=True)[:50])

def get_subdomains(urls: Dict[str, Dict]) -> Dict[str, int]:
    domains = {}
    for url in urls:
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"
        if domain.endswith('.ics.uci.edu'):
            domains[domain] = domains.setdefault(domain, 0) + 1
    return dict(sorted(domains.items(), key=lambda item: urlparse(item[0]).netloc))

def main():
    cparser = ConfigParser()
    cparser.read("config.ini")
    config = Config(cparser)
    with open(config.save_file) as f:
        data = json.load(f)
    tokens = data["tokens"]
    urls = {k.replace(" ", ""): v for k, v in data["urls"].items()}
    
    num_unique_pages = get_num_unique_pages(urls)
    
    longest_page = get_longest_page(urls)
    
    common_words = get_most_common_words(tokens)
    width = max(len(word) for word in common_words)
    formatted_words = [f"\t{rank}. {word.rjust(width + (rank<10))} => {count}" for rank, (word, count) in enumerate(common_words.items(), start=1)]
    common_words_string = "\n".join(formatted_words)
    
    subdomains = get_subdomains(urls)
    width = max(len(subdomain) for subdomain in subdomains)
    formatted_subdomains = [f"\t{subdomain.rjust(width)}, {count}" for subdomain, count in subdomains.items()]
    subdomains_string = "\n".join(formatted_subdomains)

    with open("report.txt", "w") as f:
        for line in [
            f"Name: Kevin Nguy",
            f"UCI NetID: nguyk1",
            f"ID #: 82216949",
            f"",
            f"------------------------------Assignment 2: Web Crawler------------------------------\n",
            f"1. Number of unique pages found:",
            f"\t{num_unique_pages} pages.\n",
            f"2.The longest page found:",
            f"\t{longest_page[0]} with {longest_page[1]} words.\n",
            f"3. 50 most common words:",
            f"{common_words_string}\n",
            f"4. {len(subdomains)} subdomains found under ics.uci.edu:",
            f"{subdomains_string}"
            
        ]:
            f.write(f"{line}\n")
    
if __name__ == "__main__":
    main()