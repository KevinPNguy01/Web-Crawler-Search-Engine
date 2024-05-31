from collections import defaultdict
import streamlit as st
from typing import Dict, List, Generator
from src.posting import Posting
import time
import nltk
import re
from src.webpage import WebPage
from nltk.stem import PorterStemmer
import nltk 
from pathlib import Path

class SearchEngine:
    def __init__(self):
        self.index_of_index: Dict[str, int] = self.read_index_files("index_of_index.txt")
        self.index_of_crawled: Dict[str, int] = self.read_index_files("index_of_crawled.txt")
        self.crawled_file = open("indices/crawled.txt", "r", encoding="utf-8")

    def read_index_files(self, file_name: str) -> Dict[str, int]:
        index_dict = {}
        with open(f"indices/{file_name}", "r") as file:
            for line in file:
                key, position = line.split(",")
                index_dict[key] = int(position)
        return index_dict
    
    def search(self, query: str) -> List[WebPage]:
        tokens = self.tokenize(query)
        webpages = self.get_results(tokens)
        return webpages

    def tokenize(self, query: str) -> List[str]:
        tokens = [token.lower() for token in re.findall(r'\b[a-zA-Z0-9]+\b', query) if not token.isnumeric() or len(token) <= 4]
        stemmer = PorterStemmer()
        stemmed_tokens = [stemmer.stem(token) for token in tokens]

        n = min(max(1, len(tokens) - 1), 3)
        tokens = list(nltk.ngrams(tokens, n))
        tokens += [ngram for ngram in nltk.ngrams(stemmed_tokens, n) if ngram not in tokens]
        tokens = [" ".join(ngram) for ngram in tokens]

        return tokens
        
    def get_results(self, tokens: List[str]) -> List[WebPage]:
        postings = self.get_postings(tokens)
        results = self.filter(postings)
        webpages = []
        for posting in sorted(results, key=lambda x: x.tf_idf, reverse=True)[:5]:
            self.crawled_file.seek(self.index_of_crawled[str(posting.id)])
            path = Path(self.crawled_file.readline().strip())
            webpage = WebPage.from_path(path)
            webpage.get_context(tokens)
            webpages.append(webpage)
        return webpages

    def get_postings(self, tokens: List[str]) -> List[List[Posting]]:
        token_postings = []  # List to store postings for each token

        with open("indices/index.txt", "r") as index:
            for token in tokens:
                index_position = self.index_of_index.get(token, -1)
                if index_position > -1:
                    index.seek(index_position)
                    line = index.readline()
                    token, postings_string = line.split(":", 1)
                    postings = [Posting.from_string(p) for p in postings_string.split(";")]
                    token_postings.append(postings)
                
        return token_postings

    def filter(self, token_postings: List[List[Posting]]) -> List[Posting]:
        results = []
        doc_to_postings = defaultdict(list)

        for postings in token_postings:
            for posting in postings:
                doc_to_postings[posting.id].append(posting)
        
        token_doc_ids = [set(posting.id for posting in postings) for postings in token_postings]
        
        # Find common document IDs that appear in all token_doc_ids sets
        common_doc_ids = set()
        if token_doc_ids:
            common_doc_ids = set.intersection(*token_doc_ids)

        for doc_id in common_doc_ids:
            # tells you what byte come in 
            tf_idf_score = sum(posting.tf_idf for posting in doc_to_postings[doc_id])
            document = Posting(doc_id, tf_idf_score)
            results.append(document)
        return results

def display_results(results: List[WebPage]) -> None:
    for webpage in results:
        st.subheader(webpage.title, anchor=False)
        st.write(webpage.url)
        st.markdown(webpage.context)
        #st.write(webpage.get_summary())
        st.markdown("---")

def main():
    search_engine = SearchEngine()

    st.title("Search Engine")
    user_input = st.text_input("Enter a query: ")

    if st.button("Search"):
        if user_input:
            start = time.time()
            results = search_engine.search(user_input)
            elapsed_time = round((time.time() - start) * 1000)
            st.write(f"Search completed in {elapsed_time} ms.")
            display_results(results)

if __name__ == "__main__":
    main()