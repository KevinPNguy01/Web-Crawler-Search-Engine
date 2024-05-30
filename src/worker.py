from pathlib import Path
from src.posting import Posting
from typing import Dict, List
import json
import os
from multiprocessing import Queue, Value
import signal
import msgspec
import ctypes
from bs4 import BeautifulSoup
import re
from src.tokenizer import tokenize

class WebPage(msgspec.Struct, gc=False):
    url: str
    content: str
    encoding: str

decoder = msgspec.json.Decoder(type=WebPage)

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

		# Count the number of partial indices associated with this worker id.
		for file in os.listdir(self.folder):
			if file.startswith(f"w{self.worker_id}"):
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
		self.q_out.put(None)			# Signal to the main process that this worker is done.
		print(f"Worker {self.worker_id} exited.")

	def create_partial_index(self) -> None:
		""" Write the tokens and postings stored in memory into a partial index. """

		with open(f"{self.folder}/w{self.worker_id}-i{self.index_count}.dat", "w") as index:
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
		print(f"Worker {self.worker_id} - Merging indices...")

		# Since the partial indices are in alphabetical order, we are essentially merging n sorted lists.
		indices = [open(f"{self.folder}/{file}") for file in os.listdir(self.folder) if file.startswith(f"w{self.worker_id}")]	# Open every partial index belonging to this worker.
		lines = [index.readline().strip() for index in indices]																	# Read the first line from every file.

		# Get the first token and list of postings from each file.
		tokens: List[str] = [None for _ in indices]
		postings_strings: List[str] = [None for _ in indices]
		for i, line in enumerate(lines):
			tokens[i], postings_strings[i] = line.split(":", 1) if line else (None, None)	

		with open(f"{self.folder}/w{self.worker_id}.dat", "w") as index:
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
			if file.startswith(f"w{self.worker_id}-"):
				os.remove(f"{self.folder}/{file}")
		os.rename(f"{self.folder}/w{self.worker_id}.dat", f"{self.folder}/w{self.worker_id}-0.dat")
		print(f"Worker {self.worker_id} - Merged indices.")

	def process_document(self, file_path: Path, id: int) -> None:
		""" Processing the given document, extracting the postings from it. """

		# Load json file for this document quickly.
		with open(file_path, encoding="utf-8") as f:
			page = decoder.decode(f.read())

		# Skip file if it contains invalid html.
		if not is_valid_html(page.content):
			return
		
		soup = BeautifulSoup(page.content, "lxml")
		title = soup.find("title")
		title = title.string if title else ""
		title = re.sub(r'\s+',' ', title if title else "").strip()

		# Add all postings from that file to this worker's own dict.
		for token, posting in Posting.get_postings(soup, id).items():
			self.postings.setdefault(token, []).append(posting)
			self.posting_count += 1
		self.q_out.put((id, file_path, title))
		print(f"Worker {self.worker_id} - {id} - {file_path}")