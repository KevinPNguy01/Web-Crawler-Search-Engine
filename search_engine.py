from collections import defaultdict
import json
import streamlit as st 
from typing import Dict
from src.posting import Posting
from bs4 import BeautifulSoup

def main():
    try:
        index_of_index: Dict[str, int] = {}
        with open("index_of_index.txt", "r") as index_of_index_file:
            for line in index_of_index_file:
                token, position = line.split(",")
                index_of_index[token] = int(position)
        index_of_crawled: Dict[int, int] = {}
        with open("index_of_crawled.txt", "r") as index_of_crawled_file:
            for line in index_of_crawled_file:
                id, position = line.split(",")
                index_of_crawled[int(id)] = int(position)
        st.title("Search Engine")
        user_input = st.text_input("Enter a query: ")

        if st.button("Search"):
            if user_input:
                tokens = user_input.split()
                token_postings = [] # just a list of lists of postings
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
                least_frequent = min(token_postings, key=len) # finds the list in the postings with the smallest len 
                results = []

                doc_tf_idf = defaultdict(float)
                for document in least_frequent:
                    id = document.id
                    # checks if the website / id is present in all other lists in token_postings 
                    # where each list in the token_posting is another token 
                    if all([any([posting.id == id for posting in postings]) for postings in token_postings]):
                        results.append(document)

                        for postings in token_postings:
                            for posting in postings:
                                if posting.id == id:
                                    # add the tf_idf's of the tokens 
                                    doc_tf_idf[id] += posting.tf_idf

                for document in results:
                    document.tf_idf = doc_tf_idf[document.id]

                with open("crawled.txt", "r") as crawled_file:
                    for index, posting in enumerate(sorted(results, key= lambda x: x.tf_idf, reverse = True)[:5], start = 1):
                        crawled_file.seek(index_of_crawled[posting.id])
                        path = crawled_file.readline().strip()
                        with open(path, "r") as file:
                            data = json.load(file)
                            url = data["url"]
                            soup = BeautifulSoup(data["content"], "html.parser")
                            text = soup.get_text()
                        contexts = []
                        for token in tokens:
                            pos = text.lower().find(token)
                            size = 32
                            contexts.append(f"{text[max(pos-size, 0):pos]}**:blue-background[{text[pos:pos+len(token)]}]**{text[pos+len(token):pos+len(token)+size]}".replace("\n","").replace("\r","").replace("#",""))
                        st.write(f"{index}.\t{soup.title.string}")
                        st.write(f"{url}")
                        for context in contexts:
                            st.markdown(f"...{context}...")

            
    except KeyboardInterrupt:
        print("\nExit successful.")

if __name__ == "__main__":
    main()