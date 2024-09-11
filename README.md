# CS 121 Search Engine 

## A fully functional search engine written in Python

This project is based on Professor Knone's Martin's Assignment 3 which is to create a search engine. Every part of this README.md will show you how to do the following:

* Create an index from the given webpages
* Launch the GUI application 
* Perform a query within the GUI 
* Automatically write out a report for a set of queries 

## Setup and Installation 

You will need to install the following libraries beforehand using pip install or brew.

## Libraries to install 

1. `beautifulsoup4`
2. `msgspec`
3. `lxml`
4. `nltk`
5. `openai`

This can all be installed with one simple command below:

```pip install beautifulsoup4 msgspec lxml nltk openai```

Once installed you're ready to create your index! 

## Creating an index

To create your index navigate to the directory of the project and enter into the terminal the following command.
```python3 launch.py```

Indexing can be stopped partway through by pressing ctrl+c once.
Simply rerun the command to resume indexing.
If you would like to restart the index for any reason add ```--restart``` as an argument for the command .


**NOTE: The creation of the index utilizes multiprocessing for faster indexing.**
**The number of worker processes can be set by passing ```-n``` followed by an integer.** 
```python3 launch.py -n 10 --restart```
This command creates the index from the start, and spawns 10 worker processes.
After your index has been created you may now start the application!

## Running the GUI Application 

To start the application type in the following command in the same directory    
```streamlit run search_engine.py```

You will promptly be redirected to the application via a webpage 
![Main Page GUI](images/gui.png)

Simply type in any query and page results will pop up, you may continue to enter new queries over and over until you decide to exit the program 

to end the Streamlit application, within your IDE, navigate to your terminal and enter the following key combination ```ctrl + c```

## Writing a report with multiple queries

If you would like to evaulate the peformance of the search engine against multiple queries navigate to the ```query.txt``` file where you'll find an empty file, for each line is it's own query. 

After saving the file naviagete to the ```write_report.py``` file and simply run the file either in the terminal ```python3 write_report.py``` or launching via the IDE. 

Afterwards a new file will be created named ```query_results.txt``` with the top 5 results for each query alongside the runtime.
