import streamlit as st 
from src.posting import Posting
from typing import Dict 
import cython_function 

def display_results(collected_data):
    temp = open("temp.txt", "w")

    for index, title, url, contexts in collected_data:
        st.write(f"{index}.\t{title}")
        st.write(f"{url}")
        for context in contexts:
            temp.write(f"{context}\n")
            st.markdown(f"...{context}...")
    
    temp.close()

def main():
    # Dictionaries to hold token positions and crawled positions
    index_of_index: Dict[str, int] = cython_function.read_index_files("index_of_index.txt")
    index_of_crawled: Dict[int, int] = cython_function.read_index_files("index_of_crawled.txt")
    # Streamlit UI setup
    st.title("Search Engine")
    user_input = st.text_input("Enter a query: ")

    # When the search button is clicked
    if st.button("Search"):
        if user_input:
            # simply lowercasing our query as the orginal tokenizer lowercases all words
            tokens = user_input.lower().split()

            # need to optimize this 
            correct_tokens = cython_function.correct_spelling(tokens, list(index_of_index.keys()))
            
            token_postings = cython_function.get_postings(correct_tokens, index_of_index)
            # Find the list of postings with the smallest length (least frequent) 
            # this is to make it more efficient when finding the intersection 
            least_frequent = min(token_postings, key=len)

            # filtering out our results via tf_idf 
            results = cython_function.filter(token_postings, least_frequent)
            data = cython_function.collect_results(results, index_of_crawled, correct_tokens)
            display_results(data)
if __name__ == "__main__":
    main()