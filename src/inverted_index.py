from pathlib import Path
from src.posting import Posting
from typing import Dict, List, Set
from platform import system
import math
import json
import os
		
OS_WINDOWS = system() == "Windows"	# Flag for if OS is Windows.

def is_valid_html(file_path: Path) -> bool:
	""" Ensure the JSON file has the "content" field and contains HTML tags. """
	with open(file_path, 'r', encoding='utf-8') as f:
		data = json.load(f)
		content = data.get('content', '')
		return '<html' in content[:1024].lower()

class InvertedIndex:
	def __init__(self, source: Path, restart=True) -> None:
		# Declaring attributes.
		self.source: Path = source                      # Directory path containg webpages to index.
		self.index_save_path = Path("index.txt")        # File path for inverted index.
		self.crawled_save_path = Path("crawled.txt")    # File path for names of crawled files.
		self.postings: Dict[str, List[Posting]] = {}    # Map of tokens to lists of Postings that contain that token.
		self.crawled: Set[str] = set()                  # Set of crawled files to keep track of which files don't need to be crawled again.
		self.posting_count: int = 0						# The current number of postings.
		self.index_count = len(os.listdir("partial"))	# The current number of partial indices.
		self.document_count: int = 0					# The total number of valid documents.

		# If the restart flag was not selected and the save files exist, then load them into memory.
		if not restart and self.crawled_save_path.exists() and self.index_save_path.exists():
			self.read_save_files()
		# If the restart flag was selected or the save files don't exist, create them with empty contents.
		else:
			for file in os.listdir("partial"):
				os.remove(f"partial/{file}")
			self.index_count = 0
			with open(self.crawled_save_path, "w"), open(f"index_of_{self.crawled_save_path}", "w"):
				print("Starting from empty set.")
	 
	def read_crawled_file(self) -> None:
		""" Read and load crawled save file into memory. """
		with open(self.crawled_save_path, "r") as file:
			for file_path in file:
				self.crawled.add(file_path.strip())
			
	def read_save_files(self) -> None:
		""" Reads and loads save files into memory. """
		self.read_crawled_file()
		print(f"Loaded {len(self.postings)} tokens from {len(self.crawled)} pages.")
    
	def create_partial_index(self) -> None:
		""" Write the tokens and postings stored in memory into a partial index. """
		with open(f"partial/{self.index_count}.dat", "w") as index:
			for token, postings in sorted(self.postings.items()):
				# Each line of the index is of the form: 
				# 	<token>:<id_1>,<tf-idf_1>;<id_2>,<tf-idf_2>;<id_3>,<tf-idf_3>;
				# ex.
				#	research:0,3;4,2;7,3;
				#   computer:0,12;3,8;4,9;
				# The token "research" is found in documents 0, 4, 7 with tf-idfs of 3, 2, 3 respectively.
				# The token "computer" is found in documents 0, 3, 4 with tf-idfs of 12, 8, 9.
				line = f"{token}:" + ";".join(str(p) for p in postings) + "\n"
				index.write(line)
		# Update relevant variables.
		self.postings = {}
		self.posting_count = 0
		self.index_count += 1
	 
	def run(self):
		id = len(self.crawled)										# Start the id number with how many pages have been crawled already.
		file_position = os.path.getsize(self.crawled_save_path)		# The starting file position of the index of index is the size of the index.
  
		# Open the crawled save file to store file paths, and open a file to index that file for quick access of files by id.
		with open(self.crawled_save_path, "a") as crawled_file, open("index_of_crawled.txt", "a") as index_of_crawled_file:
			
			# Iterate through all json files in source directory.
			for file in self.source.rglob("*.json"):
				# Skip file if it has been crawled before.
				if str(file) in self.crawled:
					continue
				self.crawled.add(file.name)

				# Skip file if it contains invalid html.
				if not is_valid_html(file):
					continue
				self.document_count += 1

				# Add all postings from that file to this index's own dict.
				for token, posting in Posting.get_postings(file, id).items():
					self.postings.setdefault(token, []).append(posting)
					self.posting_count += 1
	 
				# Write the file path of this page to the crawled save file.
				line = f"{file}\n"
				crawled_file.write(line)
	
				# Each line of the index of crawled is of the form: 
				# 	<id>,<file_position>
				# ex.
				#	3,8753
				#   27,16536
				# The file path of document id 3 can be found at byte 8753 in the crawled save file.
				# The file path of document id 27 can be found at byte 16536.
				index_of_crawled_file.write(f"{id},{file_position}\n")
				file_position += len(line) + OS_WINDOWS
				id += 1
    
				# If there are more than 100,000 postings stored in memory, write them to a partial index.
				if self.posting_count > 100000:
					self.create_partial_index()
				
	def save_to_file(self) -> None:
		""" Combine the partial indices into one file. """
		# Store the remaining tokens into another partial index.
		self.create_partial_index()
		
		# Basically LeetCode #23
		indices = [open(f"partial/{file}") for file in os.listdir("partial")]
		lines = [index.readline().strip() for index in indices]
		tokens = [line.split(":", 1)[0] if line else None for line in lines]
		postings_strings = [line.split(":", 1)[-1] if line else None for line in lines]
		with open("index.txt", "w") as index:
			while any(token for token in tokens):
				min_token = min(token for token in tokens if token)
				postings: List[Posting] = []
				for i, token in enumerate(tokens):
					if token == min_token:
						[postings.append(Posting.from_string(p)) for p in postings_strings[i].split(";")]
						lines[i] = indices[i].readline().strip()
						tokens[i], postings_strings[i] = lines[i].split(":", 1) if lines[i] else (None, None)

				# Calculate tf-idf for each posting.
				idf = math.log(self.document_count / len(postings))
				for posting in postings:
					tf = posting.tf_idf
					td_idf = round(tf * idf, 3)
					posting.tf_idf = td_idf

				# Write to main index.
				index.write(f"{min_token}:" + ";".join(str(p) for p in postings) + "\n")
		self.index_index()
	
	def index_index(self) -> None:
		""" Reads through the index and creates an index for that index. """
		file_position = 0
		with open(self.index_save_path, "r") as index, open(f"index_of_{self.index_save_path}", "w") as index_of_index:
			for line in index:
				# Each line of the index of index is of the form: 
				# 	<token>,<file_position>
				# ex.
				#	research,0
				#   computer,2376
				# The token "research" can be found at byte 0 of the index.
				# The token "computer" can be found at byte 2376.
				token = line.split(":", 1)[0]
				index_of_index.write(f"{token},{file_position}\n")
				file_position += len(line) + OS_WINDOWS