from collections import defaultdict
import json
import streamlit as st 
from typing import Dict
from src.posting import Posting
from bs4 import BeautifulSoup
import difflib 


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
    # Dictionary to store TF-IDF scores for documents
    doc_tf_idf = defaultdict(float)

    # Filter documents that contain all tokens
    for document in least_frequent:
        id = document.id
        if all([any([posting.id == id for posting in postings]) for postings in token_postings]):
            results.append(document)

            # Accumulate TF-IDF scores for documents
            for postings in token_postings:
                for posting in postings:
                    if posting.id == id:
                        doc_tf_idf[id] += posting.tf_idf

    # Assign accumulated TF-IDF scores to documents
    for document in results:
        document.tf_idf = doc_tf_idf[document.id]
    
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

def correct_spelling(tokens,posting_keys):
    # will find the closest match from our posting keys 
    corrected_tokens = [difflib.get_close_matches(token, posting_keys, n =1 )[0] for token in tokens]
    
    return corrected_tokens    


def main():
    # Dictionaries to hold token positions and crawled positions
    index_of_index: Dict[str, int] = read_index_files("index_of_index.txt")
    index_of_crawled: Dict[int, int] = read_index_files("index_of_crawled.txt")

    # Streamlit UI setup
    st.title("Search Engine")
    user_input = st.text_input("Enter a query: ")

    # When the search button is clicked
    if st.button("Search"):
        if user_input:
            # simply lowercasing our query as the orginal tokenizer lowercases all words
            tokens = user_input.lower().split()
            correct_tokens = correct_spelling(tokens, list(index_of_index.keys()))
            
            print(correct_tokens)
            token_postings = get_postings(correct_tokens, index_of_index)

            # Find the list of postings with the smallest length (least frequent) 
            # this is to make it more efficient when finding the intersection 
            least_frequent = min(token_postings, key=len)

            # filtering out our results via tf_idf 
            results = filter(token_postings, least_frequent)
            collect_and_display_results(results, index_of_crawled, correct_tokens)

if __name__ == "__main__":
    main()