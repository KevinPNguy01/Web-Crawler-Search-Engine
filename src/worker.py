from pathlib import Path
from src.posting import Posting
from typing import Dict, List
import json
import os
from multiprocessing import Queue, Value
import signal
import msgspec
import ctypes

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

	def process_document(self, file_path: Path, id: int) -> None:
		""" Processing the given document, extracting the postings from it. """

		# Load json file for this document quickly.
		with open(file_path, encoding="utf-8") as f:
			page = decoder.decode(f.read())

		# Skip file if it contains invalid html.
		if not is_valid_html(page.content):
			return

		# Add all postings from that file to this worker's own dict.
		for token, posting in Posting.get_postings(page.content, id).items():
			self.postings.setdefault(token, []).append(posting)
			self.posting_count += 1
		self.q_out.put((file_path, id))
		print(f"Worker {self.worker_id} - {id} - {file_path}")