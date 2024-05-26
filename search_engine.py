from collections import defaultdict
import json
import streamlit as st 
from typing import Dict
from src.posting import Posting
from bs4 import BeautifulSoup


def get_postings(index_file: str, tokens: list[str], index_of_index: dict[str, int]) -> list[list[Posting]]:
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
            postings = [Posting.from_string(p) for p in postings_string.split(";")[:-1]]
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

def collect_and_display_results(results, index_of_crawled, tokens):
    temp = open("temp.txt", "w")

    # Read the crawled.txt file to fetch and display the top 5 results
    with open("crawled.txt", "r") as crawled_file:
        for index, posting in enumerate(sorted(results, key=lambda x: x.tf_idf, reverse=True)[:5], start=1):
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


def main():
    # Dictionaries to hold token positions and crawled positions
    index_of_index: Dict[str, int] = {}
    index_of_crawled: Dict[int, int] = {}

    # Read the index_of_index.txt file to populate the index_of_index dictionary
    with open("index_of_index.txt", "r") as index_of_index_file:
        for line in index_of_index_file:
            token, position = line.split(",")
            index_of_index[token] = int(position)

    # Read the index_of_crawled.txt file to populate the index_of_crawled dictionary
    with open("index_of_crawled.txt", "r") as index_of_crawled_file:
        for line in index_of_crawled_file:
            id, position = line.split(",")
            index_of_crawled[int(id)] = int(position)

    # Streamlit UI setup
    st.title("Search Engine")
    user_input = st.text_input("Enter a query: ")

    # When the search button is clicked
    if st.button("Search"):
        if user_input:
            # simply lowercasing our query as the orginal tokenizer lowercases all words
            tokens = user_input.lower().split()
            token_postings = get_postings('index.txt', tokens, index_of_index)

            # Find the list of postings with the smallest length (least frequent) 
            # this is to make it more efficient when finding the intersection 
            least_frequent = min(token_postings, key=len)
            
            results = filter(token_postings, least_frequent)
            collect_and_display_results(results, index_of_crawled, tokens)


if __name__ == "__main__":
    main()
