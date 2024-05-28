from pathlib import Path
from src.posting import Posting
from typing import Dict, List
import json
import os
from multiprocessing import Queue, Lock, Value
import signal

def is_valid_html(file_path: Path) -> bool:
	""" Ensure the JSON file has the "content" field and contains HTML tags. """
	with open(file_path, 'r', encoding='utf-8') as f:
		data = json.load(f)
		content = data.get('content', '')
		return '<html' in content[:1024].lower()

class Worker:
	def __init__(self, worker_id: int, lock, q_in: Queue, q_out: Queue, running):
		self.worker_id = worker_id
		self.q_in = q_in
		self.q_out = q_out
		self.lock = lock
		self.running = running

		self.postings: Dict[str, List[Posting]] = {}    # Map of tokens to lists of Postings that contain that token.
		self.posting_count: int = 0						# The current number of postings.
		self.index_count = 0							# The current number of partial indices.
		for file in os.listdir("partial"):
			if file.startswith(f"w{self.worker_id}"):
				self.index_count += 1

	def create_partial_index(self) -> None:
		""" Write the tokens and postings stored in memory into a partial index. """
		with open(f"partial/w{self.worker_id}-i{self.index_count}.dat", "w") as index:
			for token, postings in sorted(self.postings.items()):
				# Each line of the index is of the form: 
				# 	<token>:<id_1>,<tf-idf_1>;<id_2>,<tf-idf_2>;<id_3>,<tf-idf_3>;
				# ex.
				#	research:0,3;4,2;7,3;
				#   computer:0,12;3,8;4,9;
				# The token "research" is found in documents 0, 4, 7 with tf-idfs of 3, 2, 3 respectively.
				# The token "computer" is found in documents 0, 3, 4 with tf-idfs of 12, 8, 9.
				line = f"{token}:" + ";".join(str(p) for p in postings) + "\n"
				try:
					index.write(line)
				except:
					print(line)
		# Update relevant variables.
		self.postings = {}
		self.posting_count = 0
		self.index_count += 1

	def read_file(self, file_path: Path, id: int) -> None:
		# Skip file if it contains invalid html.
		if not is_valid_html(file_path):
			return

		# Add all postings from that file to this index's own dict.
		for token, posting in Posting.get_postings(file_path, id).items():
			self.postings.setdefault(token, []).append(posting)
			self.posting_count += 1
		print(f"Worker {self.worker_id} - {id} - {file_path}")
		self.q_out.put((file_path, id))

	def run(self):
		file_path, id = self.q_in.get(block=False)
		while self.running.value and file_path:
			self.read_file(file_path, id)
			file_path, id = self.q_in.get(block=False)

			# If there are more than 100,000 postings stored in memory, write them to a partial index.
			if self.posting_count > 100000:
				self.create_partial_index()
		self.create_partial_index()
		print(f"Worker {self.worker_id} finished.")

	def __call__(self):
		signal.signal(signal.SIGINT, signal.SIG_IGN)
		try:
			self.run()
		except:
			self.exit()

	def exit(self):
		self.create_partial_index()
		print(f"Worker {self.worker_id} exited.")