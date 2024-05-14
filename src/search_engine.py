import json

def main():
    try:
        with open("index.json", "r") as f:
            inverted_index = json.load(f)
        while True:
            line = input("Enter a query: ")
            tokens = line.split()
            token_postings = [inverted_index.get(token, []) for token in tokens]
            least_frequent = min(token_postings, key=len)
            results = []
            for document in least_frequent:
                id = document["id"]
                if all([any([posting["id"] == id for posting in postings]) for postings in token_postings]):
                    results.append(document)
            for index, posting in enumerate(results):
                print(f"{index}. {posting["url"]}")
    except KeyboardInterrupt:
        print("\nExit successful.")

if __name__ == "__main__":
    main()