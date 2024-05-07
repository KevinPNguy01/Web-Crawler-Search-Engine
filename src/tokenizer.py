from bs4 import BeautifulSoup

def extract_text(content: str) -> str:
    # Given content representing a webpage, return the textual content.

    soup = BeautifulSoup(content)
    [soup.extract(tag) for tag in ["script"]]
    pass