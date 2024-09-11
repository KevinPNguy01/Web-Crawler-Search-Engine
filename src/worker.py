from pathlib import Path
from src.posting import Posting
from typing import Dict, List
import os
from multiprocessing import Queue, Value
import signal
import ctypes
from src.webpage import WebPage

def is_valid_html(content: str) -> bool:
	""" Ensure the JSON file has the "content" field and contains HTML tags. """
	return '<html' in content[:1024].lower()

class Worker:
	def __init__(self, worker_id: int, folder: Path, q_in: Queue, q_out: Queue, running: ctypes.c_int):
		self.worker_id = worker_id
		self.folder = folder		# Folder to create partial indices in.
		self.q_in = q_in			# Queue to receive documents to process.
		self.q_out = q_out			# Queue to send back processed documents.
		self.running = running

		self.postings: Dict[str, List[Posting]] = {}    # Map of tokens to lists of Postings that contain that token.
		self.posting_count: int = 0						# The current number of postings.
		self.index_count = 0							# The current number of partial indices.

		self.page_hashes: Dict[int, str] = {}
		self.duplicate_pages: Dict[str, int] = {}

		# Count the number of partial indices associated with this worker id.
		for file in os.listdir(self.folder):
			if file.startswith(f"w{self.worker_id:02}"):
				self.index_count += 1

	def __call__(self):
		""" Called when the worker process is started. """
		signal.signal(signal.SIGINT, signal.SIG_IGN)
		try:
			self.run()
		except KeyboardInterrupt:
			pass
		self.exit()

	def run(self):
		# Run until the main thread signals to stop, or if a None Value is encountered.
		while self.running.value and (doc_and_id := self.q_in.get()):
			self.process_document(*doc_and_id)

			# If there are more than 100,000 postings stored in memory, write them to a partial index.
			if self.posting_count > 100000:
				self.create_partial_index()

	def exit(self):
		""" Called when the worker exits due to reaching the end of the queue or from KeyboardInterrupt. """

		self.create_partial_index()		# Write the rest of the postings to a partial index.
		self.merge_indices()			# Merge this workers indices.
		#self.print_duplicate()      # write out duplicate webpages and their paths to a file 
		self.q_out.put(None)			# Signal to the main process that this worker is done.
		print(f"Worker {self.worker_id} exited.")

	def create_partial_index(self) -> None:
		""" Write the tokens and postings stored in memory into a partial index. """

		with open(f"{self.folder}/w{self.worker_id:02}-i{self.index_count}.dat", "w") as index:
			for token, postings in sorted(self.postings.items()):
				# Each line of the index is of the form: 
				# 	<token>:<id_1>,<tf-idf_1>;<id_2>,<tf-idf_2>;<id_3>,<tf-idf_3>;
				# ex.
				#	research:0,3;4,2;7,3;
				#   computer:0,12;3,8;4,9;
				# The token "research" is found in documents 0, 4, 7 with tf-idfs of 3, 2, 3 respectively.
				# The token "computer" is found in documents 0, 3, 4 with tf-idfs of 12, 8, 9.
				line = f"{token}:" + ";".join(f"{p.id},{p.tf_idf}" for p in postings) + "\n"
				index.write(line)

		# Update relevant variables.
		self.postings = {}
		self.posting_count = 0
		self.index_count += 1

	def merge_indices(self) -> None:
		""" Combine the partial indices into one file. """
		print(f"Worker {self.worker_id:02} - Merging indices...")

		# Since the partial indices are in alphabetical order, we are essentially merging n sorted lists.
		indices = [open(f"{self.folder}/{file}") for file in os.listdir(self.folder) if file.startswith(f"w{self.worker_id:02}")]	# Open every partial index belonging to this worker.
		lines = [index.readline().strip() for index in indices]																	# Read the first line from every file.

		# Get the first token and list of postings from each file.
		tokens: List[str] = [None for _ in indices]
		postings_strings: List[str] = [None for _ in indices]
		for i, line in enumerate(lines):
			tokens[i], postings_strings[i] = line.split(":", 1) if line else (None, None)	

		with open(f"{self.folder}/w{self.worker_id:02}.dat", "w") as index:
			while any(token for token in tokens):						# Loop until the end of every file has been reached.											
				min_token = min(token for token in tokens if token)		# The minimum token alphabetically out of all the documents.
				postings: List[List[str, str]] = []						# A list containing pairs of strings. The first string is the doc id, and the second is the frequency. 

				# For each token that is the minimum token, add its postings strings to one list.
				postings: List[str] = []
				for i, token in enumerate(tokens):
					if token == min_token:
						lines[i] = indices[i].readline().strip()		# For each file that had the minimum token, read the next line.
						postings.append(postings_strings[i])
						tokens[i], postings_strings[i] = lines[i].split(":", 1) if lines[i] else (None, None)
				index.write(f"{min_token}:" + ";".join(postings) + "\n")

		for file in indices:
			file.close()
		for file in os.listdir(self.folder):
			if file.startswith(f"w{self.worker_id:02}-"):
				os.remove(f"{self.folder}/{file}")
		os.rename(f"{self.folder}/w{self.worker_id:02}.dat", f"{self.folder}/w{self.worker_id:02}-0.dat")
		print(f"Worker {self.worker_id:02} - Merged indices.")


	def is_duplicate(self, page_hash: str, page_path) -> bool:
		if page_hash in self.page_hashes.keys():
			return True
		self.page_hashes[page_hash] = page_path
		return False
	
	def compute_hash(self,page_content: List[str]) : 
		raw_text = ' '.join(page_content)

		""" this function will return a hash value for a given document 
		for each character in the hash we multily by the prime 
		+ ord(char) gives us the ascii value of the character

		% 2^32 to make sure it says within a 32 bit unsigned (no negative) integer and sets the range 
		# so lets us have hash values in the range  0 - 8,388,607

		we multiply by 31 (prime) becuase it less likely produces patterns (so no accidental matches)
		and lets us produce a unique hash number 
		"""

		hash_value = 0
		prime = 31  # A small prime number for multiplication
		for char in raw_text:
			hash_value = (hash_value * prime + ord(char)) % (2**32)  # Use a large prime modulus to avoid overflow
		return hash_value
	
	def process_document(self, file_path: Path, id: int) -> None:
		""" Processing the given document, extracting the postings from it. """

		# Load webpage from file path.
		webpage = WebPage.from_path(file_path)

		# Skip file if it contains invalid html.
		if not is_valid_html(webpage.content):
			return
		
		text_content = webpage.get_text()
		page_hash = self.compute_hash(text_content)

		if self.is_duplicate(page_hash, file_path):
			self.duplicate_pages[file_path] = page_hash
			return

		# Add all postings from that file to this worker's own dict.
		for token, posting in Posting.get_postings(webpage.soup, id).items():
			self.postings.setdefault(token, []).append(posting)
			self.posting_count += 1
		self.q_out.put((id, file_path, webpage.url, webpage.title))
		print(f"Worker {self.worker_id:02} - {id} - {file_path}")

	def print_duplicate(self):
		for key,value in self.duplicate_pages.items():
			print(f"duplicate page found for {key} and {self.page_hashes[value]}")

