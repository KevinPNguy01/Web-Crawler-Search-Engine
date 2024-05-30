import search_engine
import json

def main():
    # Read index files
    index_of_index = search_engine.read_index_files("index_of_index.txt")
    index_of_crawled = search_engine.read_index_files("index_of_crawled.txt")

    # Open the roadmap and results file
    with open("roadmap.txt", "r") as query_file:
        queries = [line.strip() for line in query_file if line.strip()]

    # Clear the results file initially
    with open("query_results.txt", "w", encoding="utf-8") as result_file:
        result_file.write("")

    for query in queries:
        search_engine.run(query, index_of_index, index_of_crawled, t=1)

if __name__ == "__main__":
    main()
