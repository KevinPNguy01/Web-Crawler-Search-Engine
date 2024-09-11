from search_engine import SearchEngine
import time

def main():
    # Create search engine
    search_engine = SearchEngine()

    # Open the roadmap and results file
    with open("query.txt", "r") as query_file:
        queries = [line.strip() for line in query_file if line.strip()]

    # Clear the results file initially
    with open("query_results.txt", "w", encoding="utf-8") as result_file:
        result_file.write("")

    with open("query_results.txt", "a", encoding="utf-8") as f: 
        for query in queries:
            f.write(f"Query: {query}\n")
            f.write("Results:\n")

            start_time = time.time()
            for webpage in search_engine.search(query):
                path, url, title = webpage
                f.write(f"Title: {title}\nURL: {url}\n\n")

            end_time = time.time()
            f.write(f"Time taken: {end_time - start_time:.3f} seconds\n")
            f.write("\n" + "="*50 + "\n\n")

if __name__ == "__main__":
    main()
