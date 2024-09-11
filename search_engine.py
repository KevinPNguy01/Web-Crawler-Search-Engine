from collections import defaultdict
import streamlit as st
from typing import Dict, List, Tuple, Set
from src.posting import Posting
import time
import nltk
import re
from src.webpage import WebPage
from nltk.stem import PorterStemmer
import nltk 

class SearchEngine:
    def __init__(self):
        self.index_of_index: Dict[str, int] = self.read_index_files("index_of_index.txt")       # Read the the index of the index.
        self.index_of_crawled: Dict[str, int] = self.read_index_files("index_of_crawled.txt")   # Read the index of the crawled.
        self.crawled_file = open("indices/crawled.txt", "r", encoding="utf-8")

        self.prev_tokens: List[str] = []    # The tokens used for the last search query

    def read_index_files(self, file_name: str) -> Dict[str, int]:
        """ Open the given file name and read the index into a dict. """
        index_dict = {}
        with open(f"indices/{file_name}", "r") as file:
            for line in file:
                key, position = line.split(",")
                index_dict[key] = int(position)
        return index_dict
    
    def search(self, query: str) -> List[Tuple[str]]:
        """ Return the search results for the given query.
            Returns a list of tuples.
            Each tuple consists of (file_path, url, title) for each search result.
        """

        self.prev_tokens = self.tokenize(query)
        webpages = self.get_results(self.prev_tokens)

        # If no webpages were found, rerun the search but with the stemmed version of each token, and without n-grams.
        if not webpages:
            stemmer = PorterStemmer()
            # Each token will be lowercase, stemmed, alphanumeric, and if it is a number, no larger than 4 digits.
            self.prev_tokens = [stemmer.stem(token.lower()) for token in re.findall(r'\b[a-zA-Z0-9]+\b', query) if not token.isnumeric() or len(token) <= 4]
            webpages = self.get_results(self.prev_tokens)
        return webpages

    def tokenize(self, query: str) -> List[str]:
        """ Returns a list of tokens for the given query. """

        # Each token will be lowercase, alphanumeric, and if it is a number, no larger than 4 digits.
        tokens = [token.lower() for token in re.findall(r'\b[a-zA-Z0-9]+\b', query) if not token.isnumeric() or len(token) <= 4]

        # Get stemmed version of each token.
        stemmer = PorterStemmer()
        stemmed_tokens = [stemmer.stem(token) for token in tokens]

        # Generate n-grams where n is 1 less than the number of tokens in the query, with minimum 1 and maximum 3.
        n = min(max(1, len(tokens) - 1), 3) 
        tokens = list(nltk.ngrams(tokens, n))                                                   # The tokens are the n-grams.
        tokens += [ngram for ngram in nltk.ngrams(stemmed_tokens, n) if ngram not in tokens]    # Add all stemmed n-grams.
        tokens = [" ".join(ngram) for ngram in tokens]                                          # Convert n-grams to space-separated strings.

        return tokens
        
    def get_results(self, tokens: List[str]) -> List[Tuple[str]]:
        """ Return the search results for the given tokens.
            Returns a list of tuples.
            Each tuple consists of (file_path, url, title) for each search result.
        """

        postings = self.get_postings(tokens)    # Get a list of postings for each token.
        results = self.aggregate(postings)      # Merge postings with common ids and their scores

        # Get the top 5 webpages based on their aggregate tf_idf scores.
        webpages = []
        for posting in sorted(results, key=lambda x: x.tf_idf, reverse=True)[:5]:
            # Seek to the file position where information for this document is stored and retrieve it.
            self.crawled_file.seek(self.index_of_crawled[str(posting.id)])
            path = self.crawled_file.readline().strip()
            url = self.crawled_file.readline().strip()
            title = self.crawled_file.readline().strip()
            webpages.append((path, url, title))
        return webpages

    def get_postings(self, tokens: List[str]) -> List[List[Posting]]:
        """ Returns a list of lists of postings for each given token. """

        token_postings: List[List[Posting]] = []    # List to store postings for each token.

        with open("indices/index.txt", "r") as index:
            for token in tokens:
                # If the token exists in the index, retrieve its postings and add it to a list.
                if index_position := self.index_of_index.get(token):
                    index.seek(index_position)
                    token, postings_string = index.readline().split(":", 1)
                    token_postings.append([Posting.from_string(p) for p in postings_string.split(";")])
                
        return token_postings

    def aggregate(self, token_postings: List[List[Posting]]) -> List[Posting]:
        """ Combines the list of list of postings, returning a single list of postings.
        Each posting stores the doc id, and its total tf-idf summed from all the tokens it had a posting for.
        """

        doc_to_postings: Dict[str, List[Posting]] = defaultdict(list)   # Stores doc ids as strings, mapped to a list of its associated postings.
        # Add all postings to its appropriate list based on its id.
        for postings in token_postings:
            for posting in postings:
                doc_to_postings[posting.id].append(posting)

        # Sum up each documents postings scores into a single posting add it to a list.
        results = []
        for doc_id in doc_to_postings.keys():
            tf_idf_score = sum(posting.tf_idf for posting in doc_to_postings[doc_id])
            results.append(Posting(doc_id, tf_idf_score))
        return results

def display_results(results: List[Tuple[str]], tokens: List[str]) -> None:
    """ Display the given results
    results is a tuple containing (file_path, url, title) for each webpage result.
    tokens is the tokens the search engine used to get the results.
    """

    summaries = []   # A list of streamlit containers to write contents of the page into.
    contexts = []    # A list of streamlit containers to write summaries of the page into.
    paths: List[str] = []                                   # A list of file paths for each search result.

    # Display the page title and url for each result.
    for i, webpage_tuple in enumerate(results):
        path, url, title = webpage_tuple
        paths.append(path)
        st.subheader(title, anchor=False)
        st.write(url)
        contexts.append(st.empty())
        summaries.append(st.empty())
        st.markdown("---")

    webpages = [WebPage.from_path(path) for path in paths]  # Create a WebPage for each path.

    # Get relevant page content for each result and display it.
    for i, webpage in enumerate(webpages):
        with contexts[i].container():
            st.write(webpage.get_context(tokens))

    # Get an AI summary for each result and display it.
    for i, webpage in enumerate(webpages):
        with summaries[i].container():
            # If either API throws an exception, do not do the summary.
            try:
                st.write_stream(webpage.get_summary())
            except:
                pass

def main():
    search_engine = SearchEngine()
    st.title("Search Engine")
    user_input = st.text_input("Enter a query: ")

    if st.button("Search") and user_input:

        # Retrieve results and record how long it took.
        start = time.time()
        results = search_engine.search(user_input)
        elapsed_time = round((time.time() - start) * 1000)
        st.write(f"Search completed in {elapsed_time} ms.")

        display_results(results, search_engine.prev_tokens)

if __name__ == "__main__":
    main()