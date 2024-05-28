from collections import defaultdict
import json
import streamlit as st 
from typing import Dict
from src.posting import Posting
from bs4 import BeautifulSoup
import difflib 
import time 


def get_postings(tokens: list[str], index_of_index: dict[str, int]) -> list[list[Posting]]:
    token_postings = []  # List to store postings for each token

    # Read the index.txt file to get postings for each token
    with open("index.txt", "r") as index:
        for token in tokens:
            index_position = index_of_index.get(token, -1)
            line = ":"
            if index_position > -1:
                index.seek(index_position)
                line = index.readline()
            token, postings_string = line.split(":", 1)
            postings = [Posting.from_string(p) for p in postings_string.split(";")]
            token_postings.append(postings)
    return token_postings


def filter(token_postings, least_frequent):
    results = []
    doc_tf_idf = defaultdict(float)

    # preprocessing document(id) -> posting mapping 
    # so it maps for a document 
    #               doc_id                   "education"                "innovation"
    # eg #1 which maps to www.uci.edu : [Posting(id=1, tf_idf=0.5), Posting(id=1, tf_idf=0.3)  ]
    
    doc_to_postings = defaultdict(list)
    for postings in token_postings:
        for posting in postings:
            doc_to_postings[posting.id].append(posting)
    
    
    #token_doc_ids = [
    #{1, 2},  # Document IDs containing "education"
    #{1, 3},  # Document IDs containing "research"
    #{1, 2, 3}  # Document IDs containing "innovation"]
    
    token_doc_ids = [set(posting.id for posting in postings) for postings in token_postings]

    for document in least_frequent:
        id = document.id
    
        #id id was == 1 
        #if all(1 in {1, 2}, 1 in {1, 3}, 1 in {1, 2, 3}):
        
        # finds the intersection 
        if all(id in doc_ids for doc_ids in token_doc_ids):
            # Accumulate TF-IDF scores for documents
            tf_idf_score = sum(posting.tf_idf for posting in doc_to_postings[id])
            # Assign accumulated TF-IDF scores to the document directly
            document.tf_idf = tf_idf_score
            results.append(document)

    return results


def collect_and_display_results(results, index_of_crawled, tokens, num_of_results = 5):
    temp = open("temp.txt", "w")

    # Read the crawled.txt file to fetch and display the top 5 results
    with open("crawled.txt", "r") as crawled_file:
        for index, posting in enumerate(sorted(results, key=lambda x: x.tf_idf, reverse=True)[:num_of_results], start=1):
            # Go to the position in the file where the filename for this document id is stored.
            crawled_file.seek(index_of_crawled[posting.id])
            path = crawled_file.readline().strip()
            with open(path, "r") as file:
                data = json.load(file)
                url = data["url"]
                soup = BeautifulSoup(data["content"], "html.parser")
                text = soup.get_text()
            contexts = []
            for token in tokens:
                pos = text.lower().find(token)  # The position in the text where the token appears.
                size = 32                       # How much context to grab before and after the token.
                # Extract and highlight context around the token.
                sentence_before = text[max(pos-size, 0):pos]
                token_text = f"**:blue-background[{text[pos:pos+len(token)]}]**"
                sentence_after = text[pos+len(token):pos+len(token)+size]
                full_sentence = f"{sentence_before}{token_text}{sentence_after}"
                contexts.append(full_sentence.replace("\n", "").replace("\r\n", "").replace("#", ""))
            # writing out relelvant infomration for our UI search engine.
            st.write(f"{index}.\t{soup.title.string}")
            st.write(f"{url}")
            for context in contexts:
                temp.write(f"{context}\n")
                st.markdown(f"...{context}...")


def read_index_files(file_name): 
    # might revert and delete  ? feels somewhat unecessary 
    # but I like a clean main function 
    # - Tyler May 26 
    index_dict = {}

    with open(file_name, "r") as file:
        if file_name == 'index_of_index.txt':
            for line in file:
                key, position = line.split(",")
                index_dict[key] = int(position)
        else:
            for line in file:
                id, position = line.split(",")
                index_dict[int(id)] = int(position)

    return index_dict 


# need to optimize this and will imrpove by 1.2 seconds 
# from 2.9 to 1.7
def correct_spelling(tokens,posting_keys):
    final = []
    
    # so we only load the keys of based off each token's first letter
    for token in tokens:
        first_letter = token[0]
        if first_letter in posting_keys:
            closest_match = difflib.get_close_matches(token, posting_keys[first_letter], n=1)
            if closest_match:
                final.append(closest_match[0])
            else:
                final.append(token)
        else:
            final.append(token)

    return final

def main():
    # Dictionaries to hold token positions and crawled positions
    index_of_index: Dict[str, int] = read_index_files("index_of_index.txt")
    index_of_crawled: Dict[int, int] = read_index_files("index_of_crawled.txt")

    # probably a better way to do this 
    with open("posting_keys.json", "r") as file:
        posting_keys = json.load(file)

    # Streamlit UI setup
    st.title("Search Engine")
    user_input = st.text_input("Enter a query: ")

    # When the search button is clicked
    if st.button("Search"):
        if user_input:
            start = time.time()
            # simply lowercasing our query as the orginal tokenizer lowercases all words
            tokens = user_input.lower().split()

            correct_tokens = correct_spelling(tokens, posting_keys)
            
            token_postings = get_postings(correct_tokens, index_of_index)

            # Find the list of postings with the smallest length (least frequent) 
            # this is to make it more efficient when finding the intersection 
            least_frequent = min(token_postings, key=len)

            # filtering out our results via tf_idf 
            results = filter(token_postings, least_frequent)
            collect_and_display_results(results, index_of_crawled, tokens)
            end = time.time()
            final = end - start 
            print(final)          

if __name__ == "__main__":
    main()