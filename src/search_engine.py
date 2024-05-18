from collections import defaultdict
import json
import streamlit as st 

def main():
    try:
        with open("index.json", "r") as f:
            inverted_index = json.load(f)

        st.title("Search Engine")
        user_input = st.text_input("Enter a query: ")

        if st.button("Search"):
            if user_input:
                tokens = user_input.split()
                token_postings = [inverted_index.get(token, []) for token in tokens] # just a list of lists of postings
                least_frequent = min(token_postings, key=len) # finds the list in the postings with the smallest len 
                results = []

                doc_tf_idf = defaultdict(float)
                for document in least_frequent:
                    id = document["id"]
                    # checks if the website / id is present in all other lists in token_postings 
                    # where each list in the token_posting is another token 
                    if all([any([posting["id"] == id for posting in postings]) for postings in token_postings]):
                        results.append(document)

                        for postings in token_postings:
                            for posting in postings:
                                if posting["id"] == id:
                                    # add the tf_idf's of the tokens 
                                    doc_tf_idf[id] += posting["tf_idf"]


                for document in results:
                    document["tf_idf"] = doc_tf_idf[document["id"]]

                for index, posting in enumerate(sorted(results, key= lambda x: x["tf_idf"], reverse = True)[:5], start = 1):
                    st.write(f"{index}. {posting['url']}")

            
    except KeyboardInterrupt:
        print("\nExit successful.")

if __name__ == "__main__":
    main()