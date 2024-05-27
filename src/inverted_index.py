from pathlib import Path
from src.posting import Posting
from typing import List
import platform
import math

from src.frontier import Frontier
from src.worker import Worker
import platform
import os
import time
		
OS_WINDOWS = platform.system() == "Windows"		# Flag for if OS is Windows.

class InvertedIndex:
	def __init__(self, source: Path, restart=True) -> None:
		self.frontier = Frontier(source, restart)
		self.workers: List[Worker]
		self.index_save_path = Path("index.txt")        # File path for inverted index.
		
	def start_async(self) -> None:
		self.workers = [Worker(id, self.frontier) for id in range(5)]
		for worker in self.workers:
			worker.start()

	def start(self) -> None:
		start = time.time()
		try:
			self.start_async()
			while not self.frontier.to_be_read.empty():
				time.sleep(1)
			self.join()
		except KeyboardInterrupt:
			self.frontier.is_running = False
			self.join()
		print(time.time() - start, "seconds elapsed.")

	def join(self) -> None:
		for worker in self.workers:
			worker.join()
		self.save_to_file()
				
	def save_to_file(self) -> None:
		""" Combine the partial indices into one file. """
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
				idf = math.log(len(self.frontier.crawled) / len(postings))
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