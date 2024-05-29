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
		self.folder = folder
		self.q_in = q_in
		self.q_out = q_out
		self.running = running

		self.postings: Dict[str, List[Posting]] = {}    # Map of tokens to lists of Postings that contain that token.
		self.posting_count: int = 0						# The current number of postings.
		self.index_count = 0							# The current number of partial indices.
		for file in os.listdir(self.folder):
			if file.startswith(f"w{self.worker_id}"):
				self.index_count += 1

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
				try:
					index.write(line)
				except:
					print(line)
		# Update relevant variables.
		self.postings = {}
		self.posting_count = 0
		self.index_count += 1

	def read_file(self, file_path: Path, id: int) -> None:
		with open(file_path, encoding="utf-8") as f:
			page = decoder.decode(f.read())
		# Skip file if it contains invalid html.
		if not is_valid_html(page.content):
			return

		# Add all postings from that file to this index's own dict.
		for token, posting in Posting.get_postings(page.content, id).items():
			self.postings.setdefault(token, []).append(posting)
			self.posting_count += 1
		print(f"Worker {self.worker_id} - {id} - {file_path}")
		self.q_out.put((file_path, id))

	def run(self):
		while self.running.value and (doc_and_id := self.q_in.get()):
			self.read_file(*doc_and_id)

			# If there are more than 100,000 postings stored in memory, write them to a partial index.
			if self.posting_count > 100000:
				self.create_partial_index()

	def __call__(self):
		signal.signal(signal.SIGINT, signal.SIG_IGN)
		try:
			self.run()
		except KeyboardInterrupt:
			pass
		self.exit()

	def exit(self):
		self.create_partial_index()
		self.q_out.put(None)			# Signal to the main process that this worker is done.
		print(f"Worker {self.worker_id} exited.")