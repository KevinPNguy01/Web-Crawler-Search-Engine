from multiprocessing import Process, Queue, Value
from typing import Set, List, Tuple, TextIO
from pathlib import Path
from src.worker import Worker
from src.webpage import WebPage
import platform
import shutil
import math
import os
		
OS_WINDOWS = platform.system() == "Windows"		# Flag for if OS is Windows.

class InvertedIndex:
	def __init__(self, source: Path, restart=True, num_workers=1) -> None:
		self.source: Path = source                      		# Folder path containg documents to index.
		self.index_folder = Path("indices")						# Folder path for indices.
		self.partial_index_folder = Path("partial_indices")		# Folder path for partial indices.
		self.index_save_path = Path("index.txt")        		# File path for inverted index.
		self.crawled_save_path = Path("crawled.txt")    		# File path for names of crawled files.

		self.workers: List[Process] = []				# List of worker processes.
		self.num_workers = max(1, min(100, num_workers))
		self.finished_workers = 0						# The number of workers that finished processing.
		self.q_in: Queue[Tuple[str, int]] = Queue()		# Queue storing tuples of (file_path, doc_id) for workers to tokenize and process.
		self.q_out: Queue[Tuple[str, int]] = Queue()	# Queue storing tuples of (file_path, doc_id, title) for the main process to save to file.
		self.running = Value("i", 1)					# Flag to indicate to workers whether to keep working or not.
		
		self.crawled: Set[str] = set()				# Set of crawled files to keep track of which files don't need to be crawled again.
		self.crawled_file: TextIO = None			# File to the crawled save file.
		self.index_of_crawled_file: TextIO = None	# File to the index of the crawled save file.

		# If the restart flag was selected or the crawled save file doesn't exist, start indexing from nothing. Otherwise, read the crawled save file.
		if restart or not Path(f"{self.index_folder}/{self.crawled_save_path}").exists():
			self.create_save_files()
		else:
			self.read_save_files()

		# Open the crawled save file and the index for it. These can be written into while the workers are working.
		self.crawled_file = open(f"{self.index_folder}/{self.crawled_save_path}", "a", encoding="utf-8")
		self.index_of_crawled_file = open(f"{self.index_folder}/index_of_{self.crawled_save_path}", "a", encoding="utf-8")

	def create_save_files(self):
		""" Initializes the directory for partial indices, and creates new save files. """

		# Delete the indices and partial indices folder and create empty ones.
		for folder in (self.index_folder, self.partial_index_folder):
			if os.path.exists(folder):
				shutil.rmtree(folder)
			os.makedirs(folder)

		# Open a new file for the crawled save file, and a new index file for it.
		for file in (f"{self.index_folder}/{self.crawled_save_path}", f"{self.index_folder}/index_of_{self.crawled_save_path}"):
			with open(file, "w"):
				pass

	def read_save_files(self) -> None:
		""" Read the crawled save file to get the pages that have already been crawled. """
		
		# Each line of the crawled save file is a file path for a document already crawled.
		with open(f"{self.index_folder}/{self.crawled_save_path}", "r", encoding="utf-8") as file:
			for file_path in file:
				if file_path.startswith(self.source.name):
					self.crawled.add(file_path.strip())
	def start(self) -> None:
		""" Starts indexing. """
		try:
			self.spawn_processes()		
			self.enqueue_documents()	# Documents get enqueued for workers to process
			self.dequeue_documents()	# Documents that finished processing get saved to file.
		except KeyboardInterrupt:
			pass

		self.running.value = 0			# Signal to workers to stop working.
		self.dequeue_documents()		# Output queue needs to be empty for workers to exit.
		self.join_workers()				# Join workers first to free up resources.
		self.empty_input_queue()		# Input queue needs to be empty for the main process to exit.
		self.save_to_file()
		self.index_index()

	def spawn_processes(self) -> None:
		""" Create workers and spawn a process for each one. """
		
		for id in range(self.num_workers):
			worker = Worker(id, self.partial_index_folder, self.q_in, self.q_out, self.running)
			p = Process(target=worker)
			self.workers.append(p)
			p.start()

	def join_workers(self) -> None:
		print("Joining workers...")
		for worker in self.workers:
			worker.join()
		print(f"All workers joined.")

	def enqueue_documents(self) -> None:
		""" Iterates through the documents and adds them to the input queue. """

		# Iterate through every .json file in the source folder, starting the id at the number of documents already crawled.
		id = len(self.crawled)
		for id, file_path in enumerate(self.source.rglob("*.json")):

			# Skip the file if it has been crawled previously.
			if str(file_path) in self.crawled or os.path.getsize(file_path) > 10000000:
				continue

			# Enqueue the file path with its assigned id.
			self.q_in.put((file_path, id))
			id += 1

		# Enqueue None values to signal to the workers there is no work left to be done.
		for _ in range(len(self.workers)):
			self.q_in.put(None)

	def dequeue_documents(self) -> None:
		""" Dequeues the documents processed by the workers and updates the crawled save file. """

		file_position = os.path.getsize(f"{self.index_folder}/{self.crawled_save_path}")	# Start the file position at the size of the crawled save file.

		# The main process keeps checking the queue until all of its workers have finished.
		while self.finished_workers < len(self.workers):

			# If the item from the queue is not None, process the document and id. A None value means a worker has finished.
			if doc_info := self.q_out.get():
				file_position += self.update_crawled_list(*doc_info, file_position)
			else:
				self.finished_workers += 1

	def empty_input_queue(self) -> None:
		""" Empties the input queue to allow the main process to join. """

		print("Clearing input queue...")
		while not self.q_in.empty():
			self.q_in.get()
		print("Cleared input queue.")

	def update_crawled_list(self, id: int, file_path: Path, url: str, title: str, file_position: int) -> int:
		""" Updates the crawled save file, as well as the index for it. 
		
		Arguments:\n
		file_path -- The document path to be written to the crawled save file. \n
		id -- The document id. \n
		file_position -- The current position in the crawled save file. \n

		Return: The number of bytes written to the crawled save file.
		"""

		# Write the file path of this document to the crawled save file.
		line = f"{file_path}\n{url}\n{title}\n"
		self.crawled_file.write(line)
		self.crawled.add(file_path.name)

		# Each line of the index of crawled is of the form: 
		# 	<id>,<file_position>
		# ex.
		#	3,8753
		#   27,16536
		# The file path of document id 3 can be found at byte 8753 in the crawled save file.
		# The file path of document id 27 can be found at byte 16536.
		self.index_of_crawled_file.write(f"{id},{file_position}\n")
		return len(line.encode("utf-8")) + OS_WINDOWS * line.count("\n")
		
	def save_to_file(self) -> None:
		""" Combine the partial indices into one file. """
		print("Saving to file. Do not quit...")

		# Since the partial indices are in alphabetical order, we are essentially merging n sorted lists.
		indices = [open(f"{self.partial_index_folder}/{file}") for file in os.listdir(self.partial_index_folder)]	# Open every partial index.
		lines = [index.readline().strip() for index in indices]														# Read the first line from every file.

		# Get the first token and list of postings from each file.
		tokens: List[str] = [None for _ in indices]
		postings_strings: List[str] = [None for _ in indices]
		for i, line in enumerate(lines):
			tokens[i], postings_strings[i] = line.split(":", 1) if line else (None, None)	

		with open(f"{self.index_folder}/index.txt", "w") as index:
			while any(token for token in tokens):						# Loop until the end of every file has been reached.											
				min_token = min(token for token in tokens if token)		# The minimum token alphabetically out of all the documents.
				postings: List[List[str, str]] = []						# A list containing pairs of strings. The first string is the doc id, and the second is the frequency. 

				# For each token that is the minimum token, add its postings to one list.
				for i, token in enumerate(tokens):
					if token == min_token:
						lines[i] = indices[i].readline().strip()		# For each file that had the minimum token, read the next line.
						postings += [p.split(",", 1) for p in postings_strings[i].split(";")]
						tokens[i], postings_strings[i] = lines[i].split(":", 1) if lines[i] else (None, None)

				# Skip n-grams that have less than a certain number of postings.
				if min_token.find(" ") > -1 and len(postings) < 10:
					continue

				# Calculate tf-idf for each posting and write to the main index.
				index.write(f"{min_token}:")									# Write the token.
				idf = math.log(len(self.crawled) / len(postings))
				for i in range(len(postings)):
					doc_id, tf = postings[i]
					tf_idf = int(tf) * idf
					index.write(f"{";" if i else ""}{doc_id},{tf_idf:.3f}")		# Write the posting.
				index.write("\n")

		print("Saved to file.")
	
	def index_index(self) -> None:
		""" Reads through the index and creates an index for that index. """

		file_position = 0
		with open(f"{self.index_folder}/{self.index_save_path}", "r") as index, open(f"{self.index_folder}/index_of_{self.index_save_path}", "w") as index_of_index:
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
				file_position += len(line) + OS_WINDOWS * line.count("\n")
