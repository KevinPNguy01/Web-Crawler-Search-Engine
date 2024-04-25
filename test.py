from urllib.parse import urljoin, urlparse

parsed = urlparse("https://ics.uci.edu/~eppstein/pix/vienna/schoenbrunn/Columbary.html")
print(parsed.geturl())
print(urljoin(parsed.geturl(), "haha.txt"))