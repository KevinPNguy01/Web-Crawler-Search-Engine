from collections import defaultdict
import difflib
import json
import streamlit as st
from typing import Dict, List
from src.posting import Posting
from bs4 import BeautifulSoup
import time
from thefuzz import fuzz
import nltk
import cProfile
import re
from src.webpage import WebPage
from nltk.stem import PorterStemmer
import nltk 
from pathlib import Path
import re

def stem_tokens(tokens: List[str]) -> List[str]:
    stemmer = PorterStemmer()
    return [stemmer.stem(token) for token in tokens]

# need to modify this 


def get_postings(tokens: List[str], index_of_index: Dict[str, int]) -> List[List[Posting]]:
    token_postings = []  # List to store postings for each token

    with open("indices/index.txt", "r") as index:
        for token in tokens:
            index_position = index_of_index.get(token, -1)
            if index_position > -1:
                index.seek(index_position)
                line = index.readline()
                token, postings_string = line.split(":", 1)
                postings = [Posting.from_string(p) for p in postings_string.split(";")]
                token_postings.append(postings)
                
               
    return token_postings

def filter(token_postings, tokens, index_of_crawled):
    results = []
    doc_tf_idf = defaultdict(float)
    doc_to_postings = defaultdict(list)

    for postings in token_postings:
        for posting in postings:
            doc_to_postings[posting.id].append(posting)
    
    token_doc_ids = [set(posting.id for posting in postings) for postings in token_postings]
    
    # Find common document IDs that appear in all token_doc_ids sets
    if token_doc_ids:
        common_doc_ids = set.intersection(*token_doc_ids)
    else:
        common_doc_ids = set()

    for doc_id in common_doc_ids:
        # tells you what byte come in 
        tf_idf_score = calc_doc_relevance(doc_to_postings[doc_id])
        document = Posting(id=doc_id, tf_idf=tf_idf_score)
        results.append(document)
    return results

def calc_doc_relevance(postings: List[Posting]) -> float:
    # inital tf_idf from the summings 
    tf_idf_score = sum(posting.tf_idf for posting in postings)
    return tf_idf_score

def collect_and_display_results(results: List[Posting], index_of_crawled: Dict[int, int], tokens: List[str], num_of_results: int = 5):
    with open("indices/crawled.txt", "r", encoding="utf-8") as crawled_file:
        for index, posting in enumerate(sorted(results, key=lambda x: x.tf_idf, reverse=True)[:num_of_results], start=1):
            crawled_file.seek(index_of_crawled[posting.id])
            path = Path(crawled_file.readline().strip())
            webpage = WebPage.from_path(path)
        
            st.subheader(webpage.title, anchor=False)
            st.write(webpage.url)
            st.markdown(webpage.get_context(tokens))
            st.markdown("---")
            #st.write(webpage.get_summary())

            
def collect_results_to_file(results: List[Posting], index_of_crawled: Dict[int, int], tokens: List[str], start_time: float, query: str, num_of_results: int = 5):
    with open("query_results.txt", "a", encoding="utf-8") as f: 
        f.write(f"Query: {query}\n")
        f.write("Results:\n")

        with open("indices/crawled.txt", "r", encoding="utf-8") as crawled_file:
            for index, posting in enumerate(sorted(results, key=lambda x: x.tf_idf, reverse=True)[:num_of_results], start=1):
                crawled_file.seek(index_of_crawled[posting.id])
                path = crawled_file.readline().strip()
                title = crawled_file.readline().strip()
                url = crawled_file.readline().strip()

                f.write(f"Title: {title}\nURL: {url}\n\n")

            end_time = time.time()
            f.write(f"Time taken: {end_time - start_time:.3f} seconds\n")
            f.write("\n" + "="*50 + "\n\n")


def read_index_files(file_name: str) -> Dict:
    index_dict = {}

    with open(f"indices/{file_name}", "r") as file:
        for line in file:
            key, position = line.split(",")
            if file_name == 'index_of_index.txt':
                index_dict[key] = int(position)
            else:
                index_dict[int(key)] = int(position)

    return index_dict

def correct_spelling(tokens: List[str], posting_keys: Dict[str, List[str]]) -> List[str]:
    return tokens 

    #corrected_tokens = []
    #for token in tokens:
        #first_letter = token[0]
        #if first_letter in posting_keys:
            #possible_tokens = posting_keys[first_letter]
            #best_match = difflib.get_close_matches(token, possible_tokens, n=1)
            #corrected_tokens.append(best_match[0] if best_match else token)
        #else:
            #corrected_tokens.append(token)
    #return corrected_tokens
    return tokens
    corrected_tokens = []
    for token in tokens:
        first_letter = token[0]
        if first_letter in posting_keys:
            possible_tokens = posting_keys[first_letter]
            best_match = difflib.get_close_matches(token, possible_tokens, n=1)
            corrected_tokens.append(best_match[0] if best_match else token)
        else:
            corrected_tokens.append(token)
    return corrected_tokens

# type denotes if running on directly search_engine or on the write_report 
# 0 = on search_egnine 1 = write_report
def run(user_input, index_of_index, index_of_crawled, t = 0):
    start = time.time()
    tokens = [token.lower() for token in re.findall(r'\b[a-zA-Z0-9]+\b', user_input) if not token.isnumeric() or len(token) <= 4]
    token_length = len(tokens)

    corrected_tokens = correct_spelling(tokens, None)
    stemmed_tokens = stem_tokens(corrected_tokens)

    if token_length <= 2:
        corrected_tokens = [" ".join(ngram) for ngram in nltk.ngrams(corrected_tokens, 1)]
        stemmed_tokens = [" ".join(ngram) for ngram in nltk.ngrams(stemmed_tokens, 1)]
        if " ".join(corrected_tokens) == " ".join(stemmed_tokens):
            stemmed_tokens = []
    elif token_length == 3: 
        corrected_tokens = [" ".join(ngram) for ngram in nltk.ngrams(corrected_tokens, 2)]
        stemmed_tokens = []
    else:
        corrected_tokens = [" ".join(ngram) for ngram in nltk.ngrams(corrected_tokens, 3)]
        stemmed_tokens = []

    normal_postings = get_postings(corrected_tokens, index_of_index)
    stemmed_postings = get_postings(stemmed_tokens, index_of_index)

    normal_results = filter(normal_postings, corrected_tokens, index_of_crawled)
    stemmed_results = filter(stemmed_postings, stemmed_tokens, index_of_crawled)

    combined_results = {posting.id: posting for posting in normal_results + stemmed_results}.values()

    if combined_results and t == 0:
        collect_and_display_results(combined_results, index_of_crawled, corrected_tokens + stemmed_tokens)
    elif combined_results and t == 1: 
        collect_results_to_file(combined_results, index_of_crawled, corrected_tokens + stemmed_tokens, start, user_input)
    else:
        print("No matching tokens found")

    end = time.time()
    if t == 0:
        st.write(f"Search completed in {end - start:.3f} seconds")



def main():
    index_of_index = read_index_files("index_of_index.txt")
    index_of_crawled = read_index_files("index_of_crawled.txt")

    st.title("Search Engine")
    user_input = st.text_input("Enter a query: ")

    if st.button("Search"):
        st.write("running")
        if user_input:
            run(user_input, index_of_index, index_of_crawled)


if __name__ == "__main__":
    main()
