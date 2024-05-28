from pathlib import Path
from src.posting import Posting
from typing import List
import platform
import math
from src.worker import Worker
import platform
import os
import time
import multiprocessing
from typing import Set
import signal
		
OS_WINDOWS = platform.system() == "Windows"		# Flag for if OS is Windows.

class InvertedIndex:
	def __init__(self, source: Path, restart=True) -> None:
		self.workers: List[Worker]
		self.index_save_path = Path("index.txt")        # File path for inverted index.
		self.workers = []
		self.m = multiprocessing.Manager()
		self.q_in = self.m.Queue()
		self.q_out = self.m.Queue()
		self.running = self.m.Value("i", 1)
		self.total_documents = 0
		self.lock = multiprocessing.Lock()
		self.is_running = True
		self.crawled: Set[str] = set()                  # Set of crawled files to keep track of which files don't need to be crawled again.
		self.document_count: int = 0					# The total number of valid documents.
		self.source: Path = source                      # Directory path containg webpages to index.
		self.crawled_save_path = Path("crawled.txt")    # File path for names of crawled files.
		self.crawled_file = None
		self.index_of_crawled_file = None
		#self.crawled_file_lock = Lock()
		self.file_position = 0
		self.current_id = 0

		# If the restart flag was not selected and the save files exist, then load them into memory.
		if not restart and self.crawled_save_path.exists():
			self.read_save_files()
		# If the restart flag was selected or the save files don't exist, create them with empty contents.
		else:
			for file in os.listdir("partial"):
				os.remove(f"partial/{file}")
			self.index_count = 0
			with open(self.crawled_save_path, "w"), open(f"index_of_{self.crawled_save_path}", "w"):
				print("Starting from empty set.")

		self.crawled_file = open(self.crawled_save_path, "a")
		self.index_of_crawled_file = open(f"index_of_{self.crawled_save_path}", "a")

	def read_crawled_file(self) -> None:
		""" Read and load crawled save file into memory. """
		with open(self.crawled_save_path, "r") as file:
			for file_path in file:
				self.crawled.add(file_path.strip())
		self.file_position = os.path.getsize(self.crawled_save_path)
		self.current_id = len(self.crawled)
		self.total_documents = self.current_id
			
	def read_save_files(self) -> None:
		""" Reads and loads save files into memory. """
		self.read_crawled_file()
		print(f"Loaded {len(self.crawled)} pages.")

	def update_crawled_list(self, file_path: Path, id: int) -> None:
		self.crawled.add(file_path.name)
		# Write the file path of this page to the crawled save file.
		line = f"{file_path}\n"
		self.crawled_file.write(line)

		# Each line of the index of crawled is of the form: 
		# 	<id>,<file_position>
		# ex.
		#	3,8753
		#   27,16536
		# The file path of document id 3 can be found at byte 8753 in the crawled save file.
		# The file path of document id 27 can be found at byte 16536.
		self.index_of_crawled_file.write(f"{id},{self.file_position}\n")
		self.file_position += len(line) + OS_WINDOWS
		
	def start_async(self) -> None:
		for id in range(10):
			worker = Worker(id, self.lock, self.q_in, self.q_out, self.running)
			p = multiprocessing.Process(target=worker)
			p.start()
			self.workers.append(p)

	def start(self) -> None:
		try:
			self.start_async()

			for file in self.source.rglob("*.json"):
				if str(file) in self.crawled:
					continue
				self.q_in.put((file, self.current_id))
				self.current_id += 1

			while not self.q_in.empty():
				time.sleep(1)
			self.join()
		except KeyboardInterrupt:
			self.running.value = 0
			self.join()

	def join(self) -> None:
		for worker in self.workers:
			worker.join()
		self.save_to_file()
				
	def save_to_file(self) -> None:
		""" Combine the partial indices into one file. """
		print("Saving to file. Do not quit...")
		time.sleep(1)
		while not self.q_out.empty():
			file_path, id = self.q_out.get()
			self.update_crawled_list(file_path, id)
			self.total_documents += 1

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
						[postings.append(p.split(",", 1)) for p in postings_strings[i].split(";")]
						lines[i] = indices[i].readline().strip()
						tokens[i], postings_strings[i] = lines[i].split(":", 1) if lines[i] else (None, None)

				# Calculate tf-idf for each posting.
				idf = math.log(self.total_documents / len(postings))
				for i in range(len(postings)):
					postings[i][1] = float(postings[i][1]) * idf

				# Write to main index.
				index.write(f"{min_token}:" + ";".join(f"{p[0]},{p[1]:.3f}" for p in postings) + "\n")
		self.index_index()

		print("Saved to file.")
	
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