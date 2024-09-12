<div style="display: flex; justify-content: center; align-items: center;">
    <svg fill="currentColor" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" id="Layer_1" x="0px" y="0px" width="100px" height="100px" viewBox="0 0 100 100" enable-background="new 0 0 100 100" xml:space="preserve">
        <path d="M97.635,56.061c-9.252-6.534-19.894-9.792-28.337-11.415c6.792-3.236,14.602-8.856,21.461-18.627  c1.036-1.477,0.68-3.514-0.797-4.55c-1.478-1.037-3.515-0.68-4.551,0.796c-6.633,9.449-14.177,14.48-20.394,17.165  c3.778-4.709,7.831-12.14,11.353-23.886c0.519-1.728-0.463-3.549-2.19-4.067c-1.731-0.517-3.55,0.462-4.067,2.191  c-5.449,18.175-11.796,24.271-15.279,26.31c-0.507-1.304-1.309-2.367-2.288-3.037c0.11-0.384,0.178-0.797,0.178-1.233  c0-1.611-0.828-2.953-1.944-3.335l-0.36,3.807c-0.094-0.007-0.187-0.019-0.282-0.019s-0.188,0.012-0.283,0.019l-0.36-3.807  c-1.116,0.383-1.944,1.724-1.944,3.335c0,0.436,0.067,0.849,0.177,1.233c-0.979,0.67-1.781,1.733-2.288,3.037  c-3.483-2.039-9.829-8.134-15.279-26.31c-0.519-1.729-2.344-2.708-4.067-2.191c-1.729,0.518-2.709,2.339-2.191,4.067  c3.503,11.684,7.532,19.099,11.293,23.813c-6.224-2.7-13.759-7.723-20.336-17.091c-1.037-1.477-3.075-1.833-4.55-0.796  c-1.477,1.036-1.833,3.074-0.796,4.55c6.862,9.774,14.674,15.396,21.468,18.63c-8.442,1.621-19.084,4.874-28.342,11.412  c-1.474,1.04-1.825,3.079-0.784,4.553c0.637,0.9,1.646,1.382,2.671,1.382c0.651,0,1.309-0.194,1.881-0.599  c9.217-6.509,20.247-9.434,28.335-10.75c-6.757,5.944-14.83,17.129-21.636,38.173c-0.555,1.716,0.386,3.558,2.103,4.113  c0.334,0.107,0.673,0.159,1.006,0.159c1.379,0,2.66-0.88,3.107-2.263c6.005-18.563,12.795-28.591,18.342-34.011  c-0.487,1.842-0.765,3.813-0.765,5.878c0,9.765,5.927,17.682,13.239,17.682c7.311,0,13.238-7.917,13.238-17.682  c0-2.064-0.278-4.038-0.766-5.88c5.546,5.42,12.337,15.45,18.341,34.013c0.447,1.383,1.729,2.263,3.107,2.263  c0.333,0,0.672-0.052,1.006-0.159c1.717-0.556,2.658-2.397,2.104-4.113c-6.814-21.067-14.905-32.254-21.671-38.193  c8.08,1.309,19.115,4.233,28.37,10.769c0.573,0.404,1.23,0.599,1.882,0.599c1.025,0,2.035-0.481,2.671-1.382  C99.459,59.14,99.108,57.101,97.635,56.061z"/>
    </svg>
    <svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" fill="currentColor" class="bi bi-plus" viewBox="0 0 16 16">
        <path d="M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4"/>
    </svg>
    <svg xmlns="http://www.w3.org/2000/svg" width="80" height="80" fill="currentColor" class="bi bi-search" viewBox="0 0 16 16">
        <path d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001q.044.06.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1 1 0 0 0-.115-.1zM12 6.5a5.5 5.5 0 1 1-11 0 5.5 5.5 0 0 1 11 0"/>
    </svg>
</div>

<h1 align="center">Web Crawler + Search Engine</h1>
<h3> Web Crawling </h3>
<ul>
    <li><strong>Multithreading</strong>: Utilizes multiple threads to crawl multiple domains in parallel.</li>
    <li><strong>Stores Web Pages</strong>: Saves web page content into json files to be indexed later.</li>
    <li><strong>Politeness</strong>: Adheres to robots.txt and enforces a minimum delay between requests to the same domain.</li>
    <li><strong>Pauseable</strong>: Allows crawling to be stopped and resumed at any time without loss of progress.</li>
    <li><strong>Customizeable</strong>: Uses a config file to configure seed url, allowable domains, and minimum politeness.</li>
</ul>

<h3> Indexing </h3>
<ul>
    <li><strong>Multiprocessing</strong>: Utilizes multiple processes to index multiple web pages at once.</li>
    <li><strong>Partial Indexing</strong>: Indexed content is regularly written to files and combined at the end, minimizing memory usage.</li>
    <li><strong>N-gram Indexing</strong>: Breaks text into n-grams, enabling more flexible and precise query matching.</li>
    <li><strong>Pauseable</strong>: Allows indexing to be stopped and resumed at any time without loss of progress.</li>
</ul>

<h3> Searching </h3>
<ul>
    <li><strong>Ranking</strong>: Results are ranked by a combination of keyword frequency and placement in the webpage.</li>
    <li><strong>AI Summary</strong>: Generates concise summaries of search results using OpenAI's GPT-3.5.</li>
    <li><strong>Fast Results</strong>: Results take only a few milliseconds for an index of 55,000 web pages. </li>
</ul>